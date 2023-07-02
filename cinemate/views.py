import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import auth
import pandas as pd
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.http import HttpResponse, JsonResponse
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Review, Preference, Watchlist
from datetime import datetime, timedelta
from django.urls import reverse
from django.core.paginator import Paginator
from django.db import connection
import numpy as np
import requests
import imdb
import pickle
import random

# Create your views here.


# load the nlp model and tfidf vectorizer from disk
filename = "nlp_model.pkl"
clf = pickle.load(open(filename, "rb"))
vectorizer = pickle.load(open("transform.pkl", "rb"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username taken.")
            elif User.objects.filter(email=email).exists():
                messages.error(request, "Email taken.")
            else:
                try:
                    user = User.objects.create_user(
                        username=username, email=email, password=password
                    )
                    messages.success(
                        request, "Registration successful. You can now login."
                    )
                    request.session["user_id"] = user.id  # Save user_id in session
                    return redirect("preferences")

                except:
                    messages.error(request, "An error occurred during registration.")
        else:
            messages.error(request, "Passwords do not match.")

    return render(request, "registerPage.html")


def login(request):
    if request.method == "POST":
        # Retrieve form data
        username = request.POST["username"]
        password = request.POST["password"]

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect("/")
        else:
            messages.error(request, "Invalid Username or Password.")
            return redirect("login")
    else:
        return render(request, "loginPage.html")


def logout(request):
    auth.logout(request)
    return redirect("/")


def forgotPassword(request):
    if request.method == "POST":
        username = request.POST["username-forget"]
        email = request.POST["email-forget"]
        password = request.POST["password-forget"]
        confirm_password = request.POST["confirm-password-forget"]

        if password == confirm_password:
            try:
                user = User.objects.get(username=username, email=email)
                user.set_password(password)
                user.save()
                messages.success(
                    request,
                    "Password reset successful. You can now login with your new password.",
                )
                return redirect("login")
            except User.DoesNotExist:
                messages.error(request, "Invalid username or email.")
            except:
                messages.error(request, "An error occurred during password reset.")
        else:
            messages.error(request, "Passwords do not match.")

    return render(request, "reset_password.html")


def preferences(request):
    i = 0
    apiKey = "0590e66205dca735336af409ce16babe"
    genreList_url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={apiKey}"
    response = requests.get(genreList_url)
    genres = response.json()["genres"]
    user_id = request.session.get("user_id")

    genre_info = []
    for genre in genres:
        genre_id = genre["id"]
        genre_name = genre["name"]
        movies = fetch_genre(genre_id)
        genre_info.append({"id": genre_id, "name": genre_name, "movies": movies})

    movie_categories_context = {
        "genreList": genre_info,
        "i": i,
        "user_id": user_id,  # Include user_id in the context
    }

    process_genres_url = reverse("process_genres")
    process_genres_url += f"?user_id={user_id}"
    movie_categories_context["process_genres_url"] = process_genres_url

    return render(request, "preferences.html", movie_categories_context)


def process_genres(request):
    if request.method == "POST":
        selected_genres = request.POST.get("selected_genres")
        user_id = request.session.get("user_id")
        if not selected_genres:
            return redirect("preferences")
        if selected_genres and user_id:
            genre_names = selected_genres.split(",")
            user_preferences = Preference(userID=user_id)
            for i in range(len(genre_names)):
                genre_name = genre_names[i]
                setattr(user_preferences, f"genre{i+1}", genre_name)
            # Process the genre names as needed
            user_preferences.save()
            messages.success(request, "Genres processed successfully")
            return redirect(
                "login"
            )  # Assuming 'login' is the name of your login page URL
        else:
            messages.error(request, "No selected genres provided")
            return redirect("login")


def fetch_genreID(genre_name):
    apiKey = "0590e66205dca735336af409ce16babe"
    genreList_url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={apiKey}"
    response = requests.get(genreList_url)
    genres = response.json()["genres"]

    for genre in genres:
        if genre_name == genre["name"]:
            return genre["id"]
    return None


def fetch_genre(genre_id):
    apiKey = "0590e66205dca735336af409ce16babe"
    genre_url = f"https://api.themoviedb.org/3/discover/movie?api_key={apiKey}&sort_by=popularity.desc&page=1&with_genres={genre_id}"

    response = requests.get(genre_url)
    data = response.json()
    movies = []
    for movie in data["results"][:10]:
        title = movie["title"]
        id = movie["id"]
        poster_path = movie["backdrop_path"]
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w780/{poster_path}"
        else:
            poster_url = "{% static 'img/null-poster.png' %}"
        movies.append(
            {
                "title": title,
                "poster_url": poster_url,
                "id": id,
            }
        )
    return movies


def recommend(request):
    apiKey = "0590e66205dca735336af409ce16babe"
    page_num = int(request.GET.get("page", 1))
    movies_per_page = 20

    user_id = request.user.id
    user_preferences = Preference.objects.get(userID=user_id)

    genre_names = [
        user_preferences.genre1,
        user_preferences.genre2,
        user_preferences.genre3,
    ]

    genre_ids = []
    for genre_name in genre_names:
        if genre_name:
            genre_id = fetch_genreID(genre_name)
            genre_ids.append(str(genre_id))
            print(genre_name + " " + str(genre_id))

    genre_ids_str = ",".join(genre_ids)
    if "," in genre_ids_str:
        genre_ids_str = [
            int(genre_id) for genre_id in genre_ids_str.strip("[]").split(",")
        ]
    else:
        genre_ids_str = ",".join(genre_ids)

    displayed_movies_per_page = (page_num - 1) * 2 + 1

    movie_pages = []
    for i in range(displayed_movies_per_page, displayed_movies_per_page + 2):
        page_url = f"https://api.themoviedb.org/3/discover/movie?page={i}&api_key={apiKey}&language=en-US&sort_by=popularity.desc&with_genres={genre_ids_str}"
        page_res = requests.get(page_url)
        page_data = page_res.json()
        movies = page_data["results"][:movies_per_page]
        movie_pages.append(movies)

    rec_movies = []
    for movies in movie_pages:
        rec_movies.extend(movies)

    previous_page = None
    if page_num > 1:
        previous_page = page_num - 1

    next_page = None
    if len(movie_pages[-1]) > 0:
        next_page = page_num + 1

    movie_categories_context = {
        "rec_movies": rec_movies,
        "previous_page": previous_page,
        "next_page": next_page,
        "current_page": page_num,
    }

    return render(request, "recommend.html", movie_categories_context)


@csrf_exempt
@login_required
def toggleWatchlist(request):
    if request.method == "POST":
        movie_id = request.POST.get("movie_id")
        user = request.user
        watchlist_item = Watchlist.objects.filter(
            movieID=movie_id, userID=user.id
        ).first()
        if watchlist_item:
            # Movie is already in the watchlist, remove it
            watchlist_item.delete()
            print("MOVIE DELETED")
            is_added = False
        else:
            # Movie is not in the watchlist, add it
            watchlist_item = Watchlist(movieID=movie_id, userID=user.id)
            watchlist_item.save()
            print("MOVIE ADDED")
            is_added = True
        response = {"is_added": is_added}
        return JsonResponse(response)


@login_required
def checkWatchlist(request):
    if request.method == "POST":
        movie_id = request.POST.get("movie_id")
        # Retrieve user's watchlist
        user_watchlist = Watchlist.objects.filter(userID=request.user.id).values_list(
            "movieID", flat=True
        )

        # Get all movie IDs in the user's watchlist
        watchlist_movie_ids = list(user_watchlist)

        if movie_id in watchlist_movie_ids:
            is_added = True
        else:
            is_added = False
        response = {"is_added": is_added}
        return JsonResponse(response)


# Homepage
def index(request):
    apiKey = "0590e66205dca735336af409ce16babe"

    if request.user.id:
        user_id = request.user.id
        user_preferences = Preference.objects.get(userID=user_id)

        genre_names = [
            user_preferences.genre1,
            user_preferences.genre2,
            user_preferences.genre3,
        ]

        genre_ids = []
        for genre_name in genre_names:
            if genre_name:
                genre_id = fetch_genreID(genre_name)
                genre_ids.append(str(genre_id))

        genre_ids_str = ",".join(genre_ids)

        if "," in genre_ids_str:
            genre_ids_str = [
                int(genre_id) for genre_id in genre_ids_str.strip("[]").split(",")
            ]
        else:
            genre_ids_str = ",".join(genre_ids)

        num_movies_to_display = 20
        fetched_movies = []

        # Fetch a smaller number of movies directly from the API
        for page in range(1, 6):
            rec_movies_url = f"https://api.themoviedb.org/3/discover/movie?api_key={apiKey}&language=en-US&sort_by=popularity.desc&with_genres={genre_ids_str}&with_release_type=2|3&page={page}"
            rec_movies_res = requests.get(rec_movies_url)
            rec_movies_data = rec_movies_res.json()
            fetched_movies += rec_movies_data["results"]

            random_movies = random.sample(
                fetched_movies, min(num_movies_to_display, len(fetched_movies))
            )
            random.shuffle(random_movies)
            rec_movies = random_movies

    latest_movies_url = f"https://api.themoviedb.org/3/movie/now_playing?api_key={apiKey}&language=en-US&page=1&with_release_type=2|3"
    latest_movies_res = requests.get(latest_movies_url)
    latest_movies_data = latest_movies_res.json()
    latest_movies = latest_movies_data["results"]

    fan_fav_movies_url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={apiKey}&language=en-US&page=1&region=US&with_release_type=2|3"
    fan_fav_movies_res = requests.get(fan_fav_movies_url)
    fan_fav_movies_data = fan_fav_movies_res.json()
    fan_fav_movies = fan_fav_movies_data["results"]

    upcoming_movies_url = f"https://api.themoviedb.org/3/movie/upcoming?api_key={apiKey}&language=en-US&page=1&region=US&sort_by=release_date.desc&with_release_type=2|3"
    upcoming_movies_res = requests.get(upcoming_movies_url)
    upcoming_movies_data = upcoming_movies_res.json()
    upcoming_movies = upcoming_movies_data["results"]

    if request.user.id:
        user_watchlist = Watchlist.objects.filter(userID=request.user.id).values_list(
            "movieID", flat=True
        )
        # Get all movie IDs in the user's watchlist
        watchlist_movie_ids = list(user_watchlist)
        watchlist_movies = []
        for movie_id in watchlist_movie_ids:
            watchlist_movies_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={apiKey}&language=en-US"
            watchlist_movies_res = requests.get(watchlist_movies_url)
            watchlist_movies_data = watchlist_movies_res.json()
            watchlist_movies.append(watchlist_movies_data)

    movie_categories_context = {
        "latest_movies": latest_movies,
        "fan_fav_movies": fan_fav_movies,
        "upcoming_movies": upcoming_movies,
    }

    if request.user.id:
        movie_categories_context["rec_movies"] = rec_movies
        movie_categories_context["watchlist_movies"] = watchlist_movies

    return render(request, "index.html", movie_categories_context)


def login_page(request):
    return render(request, "loginPage.html")


def register_page(request):
    return render(request, "registerPage.html")


def reset_password_page(request):
    return render(request, "reset_password.html")


def watchlist(request):
    apiKey = "0590e66205dca735336af409ce16babe"
    fetched_movies = []
    num_movies_to_display = 12
    page_num = int(request.GET.get("page", 1))

    for page in range(1, 6):
        pop_page_url = f"https://api.themoviedb.org/3/movie/popular?page={page}&api_key={apiKey}&language=en-US"
        pop_page_res = requests.get(pop_page_url)
        pop_page_data = pop_page_res.json()
        pop_page_movies = pop_page_data["results"][:12]
        fetched_movies += pop_page_movies

        random_movies = random.sample(
            fetched_movies, min(num_movies_to_display, len(fetched_movies))
        )
        random.shuffle(random_movies)
        popular_movies = random_movies

    user_watchlist = Watchlist.objects.filter(userID=request.user.id).values_list(
        "movieID", flat=True
    )

    watchlist_movie_ids = list(user_watchlist)
    watchlist_movies = []
    for movie_id in watchlist_movie_ids:
        watchlist_movies_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={apiKey}&language=en-US"
        watchlist_movies_res = requests.get(watchlist_movies_url)
        watchlist_movies_data = watchlist_movies_res.json()
        watchlist_movies.append(watchlist_movies_data)

    paginator = Paginator(watchlist_movies, 36)  # Display 36 movies per page

    try:
        watchlist_movies = paginator.page(page_num)
    except PageNotAnInteger:
        watchlist_movies = paginator.page(1)
    except EmptyPage:
        watchlist_movies = paginator.page(paginator.num_pages)

    previous_page = None
    if watchlist_movies.has_previous():
        previous_page = watchlist_movies.previous_page_number()

    next_page = None
    if watchlist_movies.has_next():
        next_page = watchlist_movies.next_page_number()

    movie_categories_context = {
        "watchlist_movies": watchlist_movies,
        "popular_movies": popular_movies,
        "previous_page": previous_page,
        "next_page": next_page,
        "current_page": page_num,
    }
    return render(request, "watchlist.html", movie_categories_context)


def recent_movie(request):
    apiKey = "0590e66205dca735336af409ce16babe"
    page_num = int(request.GET.get("page", 1))

    displayed_movies_per_page = (page_num - 1) * 2 + 1

    movie_pages = []
    for i in range(displayed_movies_per_page, displayed_movies_per_page + 2):
        page_url = f"https://api.themoviedb.org/3/movie/now_playing?page={i}&api_key={apiKey}&language=en-US&with_release_type=2|3"
        page_res = requests.get(page_url)
        page_data = page_res.json()
        movies = page_data["results"][:20]
        movie_pages.append(movies)

    latest_movies = []
    for movies in movie_pages:
        latest_movies.extend(movies)

    previous_page = None
    if page_num > 1:
        previous_page = page_num - 1

    next_page = None
    if len(movie_pages[-1]) > 0:
        next_page = page_num + 1

    movie_categories_context = {
        "latest_movies": latest_movies,
        "previous_page": previous_page,
        "next_page": next_page,
        "current_page": page_num,
    }

    return render(request, "recent_movie.html", movie_categories_context)


def fetch_movies_by_genre(genre_id):
    apiKey = "0590e66205dca735336af409ce16babe"
    top_rated_url = f"https://api.themoviedb.org/3/discover/movie?api_key={apiKey}&language=en-US&with_release_type=2|3&sort_by=vote_average.desc&sort_by=release_date.desc&vote_count.gte=800&page=1&with_genres={genre_id}"

    response = requests.get(top_rated_url)
    data = response.json()
    movies = []
    for movie in data["results"][:10]:
        title = movie["title"]
        id = movie["id"]
        poster_path = movie["poster_path"]
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}"
        else:
            poster_url = "{% static 'img/null-poster.png' %}"
        movies.append(
            {
                "title": title,
                "poster_url": poster_url,
                "id": id,
            }
        )
    return movies


def top_movie(request):
    i = 0
    apiKey = "0590e66205dca735336af409ce16babe"
    genreList_url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={apiKey}"
    response = requests.get(genreList_url)
    genres = response.json()["genres"]

    genre_info = []
    for genre in genres:
        genre_id = genre["id"]
        genre_name = genre["name"]
        movies = fetch_movies_by_genre(genre_id)
        genre_info.append({"id": genre_id, "name": genre_name, "movies": movies})

    movie_categories_context = {
        "genreList": genre_info,
        "i": i,
    }

    return render(request, "top_movie.html", movie_categories_context)


def popular_movie(request):
    apiKey = "0590e66205dca735336af409ce16babe"
    page_num = int(request.GET.get("page", 1))

    displayed_movies_per_page = (page_num - 1) * 2 + 1

    movie_pages = []
    for i in range(displayed_movies_per_page, displayed_movies_per_page + 2):
        page_url = f"https://api.themoviedb.org/3/movie/popular?page={i}&api_key={apiKey}&language=en-US&with_release_type=2|3"
        page_res = requests.get(page_url)
        page_data = page_res.json()
        movies = page_data["results"][:20]
        movie_pages.append(movies)

    popular_movies = []
    for movies in movie_pages:
        popular_movies.extend(movies)

    previous_page = None
    if page_num > 1:
        previous_page = page_num - 1

    next_page = None
    if len(movie_pages[-1]) > 0:
        next_page = page_num + 1

    movie_categories_context = {
        "popular_movies": popular_movies,
        "previous_page": previous_page,
        "next_page": next_page,
        "current_page": page_num,
    }
    return render(request, "popular_movie.html", movie_categories_context)


def fan_fav(request):
    apiKey = "0590e66205dca735336af409ce16babe"
    page_num = int(request.GET.get("page", 1))

    displayed_movies_per_page = (page_num - 1) * 2 + 1

    movie_pages = []
    for i in range(displayed_movies_per_page, displayed_movies_per_page + 2):
        page_url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={apiKey}&language=en-US&page={i}&region=US&with_release_type=2|3"
        page_res = requests.get(page_url)
        page_data = page_res.json()
        movies = page_data["results"][:20]
        movie_pages.append(movies)

    fan_fav_movies = []
    for movies in movie_pages:
        fan_fav_movies.extend(movies)

    previous_page = None
    if page_num > 1:
        previous_page = page_num - 1

    next_page = None
    if len(movie_pages[-1]) > 0:
        next_page = page_num + 1

    movie_categories_context = {
        "fan_fav_movies": fan_fav_movies,
        "previous_page": previous_page,
        "next_page": next_page,
        "current_page": page_num,
    }
    return render(request, "fan_fav.html", movie_categories_context)


def upcoming_movie(request):
    apiKey = "0590e66205dca735336af409ce16babe"
    page_num = int(request.GET.get("page", 1))

    displayed_movies_per_page = (page_num - 1) * 2 + 1

    movie_pages = []
    for i in range(displayed_movies_per_page, displayed_movies_per_page + 2):
        page_url = f"https://api.themoviedb.org/3/movie/upcoming?page={i}&api_key={apiKey}&language=en-US&region=US&sort_by=release_date.desc&with_release_type=2|3"
        page_res = requests.get(page_url)
        page_data = page_res.json()
        movies = page_data["results"][:20]
        movie_pages.append(movies)

    upcoming_movies = []
    for movies in movie_pages:
        upcoming_movies.extend(movies)

    previous_page = None
    if page_num > 1:
        previous_page = page_num - 1

    next_page = None
    if len(movie_pages[-1]) > 0:
        next_page = page_num + 1

    movie_categories_context = {
        "upcoming_movies": upcoming_movies,
        "previous_page": previous_page,
        "next_page": next_page,
        "current_page": page_num,
    }
    return render(request, "upcoming_movie.html", movie_categories_context)


# Query movies
def search_movies(request):
    apiKey = "0590e66205dca735336af409ce16babe"
    query = request.GET.get("q")
    page_num = int(request.GET.get("page", 1))

    results = []

    if query:
        # Fetch movies from page 1
        first_page_url = f"https://api.themoviedb.org/3/search/movie?page={page_num}&api_key={apiKey}&query={query}&sort_by=popularity.desc,vote_average.desc"
        first_page_res = requests.get(first_page_url)
        first_page_data = first_page_res.json()
        first_page_movies = first_page_data["results"]

        # Fetch movies from page 2
        second_page_url = f"https://api.themoviedb.org/3/search/movie?page={page_num + 1}&api_key={apiKey}&query={query}&sort_by=popularity.desc,vote_average.desc"
        second_page_res = requests.get(second_page_url)
        second_page_data = second_page_res.json()
        second_page_movies = second_page_data["results"]

        # Combine movies from both pages
        results = first_page_movies + second_page_movies

        # Limit the number of results to 20 for the first page if there are more than 20 results
        results = results[:40]

    search_context = {
        "results": results,
        "query": query,
    }

    return render(request, "searchResults.html", search_context)


# Getting IMDB reviews
def get_imdb_reviews(title):
    imdb_access = imdb.IMDb()

    results = imdb_access.search_movie(title)
    if not results:
        return []

    selected_movie = results[0]

    imdb_access.update(selected_movie, "reviews")

    total_reviews = []
    if "reviews" in selected_movie:
        for review in selected_movie["reviews"]:
            author = review["author"]
            content = review["content"]
            date = review["date"]

            review_info = {"author": author, "content": content, "date": date}
            total_reviews.append(review_info)

    return total_reviews


def addReview(request, movie_id):
    if request.method == "POST":
        current_time = datetime.utcnow()  # Get the current UTC time
        malaysia_time = current_time + timedelta(hours=8)
        content = request.POST["content"]
        user_id = request.user.id
        # Create a new review object
        review = Review(
            content=content, movieID=movie_id, userID=user_id, reviewDate=malaysia_time
        )
        review.save()
    return redirect(reverse("movie_info", kwargs={"movie_id": movie_id}) + "#review-area")


def deleteReview(request, movie_id):
    if request.method == "POST":
        user_id = request.user.id
        review_id = request.POST["review_id"]
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM cinemate.cinemate_review WHERE userID=%s AND reviewID=%s AND movieID=%s;",
                [user_id, int(review_id), movie_id],
            )
            print("REVIEW DELETED")
    return redirect(reverse("movie_info", kwargs={"movie_id": movie_id}) + "#review-area")


# Getting/Storing IMDB reviews based on TMDB movie titles
def movie_reviews(request, movie_id):
    current_time = datetime.utcnow()  # Get the current UTC time
    malaysia_time = current_time + timedelta(hours=8)
    apiKey = "0590e66205dca735336af409ce16babe"
    movie_info_url = (
        f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={apiKey}&language=en-US"
    )
    movie_info_res = requests.get(movie_info_url)
    movie_info_data = movie_info_res.json()

    imdb_reviews = get_imdb_reviews(movie_info_data["title"])
    personalized_reviews = Review.objects.filter(movieID=movie_id)
    personalized_reviews = personalized_reviews.filter(
        movieID=movie_id, reviewDate__lte=malaysia_time
    )
    reviews = []
    for personalized_review in personalized_reviews:
        comment = personalized_review.content
        user = User.objects.get(id=personalized_review.userID)
        movie_review_list = np.array([comment])
        movie_vector = vectorizer.transform(movie_review_list)
        pred = clf.predict(movie_vector)
        reviews_status = "Good" if pred else "Poor"
        review_info = {
            "id": personalized_review.reviewID,
            "author": user.username,
            "content": personalized_review.content,
            "date": personalized_review.reviewDate,
            "status": reviews_status,
        }
        reviews.append(review_info)

    malaysia_time_aware = timezone.make_aware(malaysia_time)
    reviews = sorted(reviews, key=lambda x: abs(x["date"] - malaysia_time_aware))
    for rev in imdb_reviews:
        date = rev["date"]
        movie_review_list = np.array([rev["content"]])
        movie_vector = vectorizer.transform(movie_review_list)
        pred = clf.predict(movie_vector)
        reviews_status = "Good" if pred else "Poor"
        review_info = {
            "author": rev["author"],
            "content": rev["content"],
            "date": date,
            "status": reviews_status,
        }
        reviews.append(review_info)

    context = {"movie": movie_info_data, "reviews": reviews}
    return render(request, "reviewsPage.html", context)


def get_latest_review(id):
    try:
        review = Review.objects.filter(userID=id).latest("reviewDate")
        return review
    except Review.DoesNotExist:
        return None


# All particular movie details
def movie_info(request, movie_id):
    apiKey = "0590e66205dca735336af409ce16babe"
    movie_info_url = (
        f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={apiKey}&language=en-US"
    )
    movie_info_res = requests.get(movie_info_url)
    movie_info_data = movie_info_res.json()

    end_credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={apiKey}&language=en-US"
    end_credits_res = requests.get(end_credits_url)
    end_credits_data = end_credits_res.json()

    movie_trailer_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={apiKey}&language=en-US"
    movie_trailer_res = requests.get(movie_trailer_url)
    movie_trailer_data = movie_trailer_res.json()

    imdb_reviews = get_imdb_reviews(movie_info_data["title"])

    related_movies_url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations?api_key={apiKey}&language=en-US"
    related_movies_res = requests.get(related_movies_url)
    related_movies_data = related_movies_res.json()
    related_movies = related_movies_data.get("results", [])

    popular_movies_url = f"https://api.themoviedb.org/3/movie/popular?api_key={apiKey}&language=en-US&page=1&with_release_type=2|3"
    popular_movies_res = requests.get(popular_movies_url)
    popular_movies_data = popular_movies_res.json()
    popular_movies = popular_movies_data["results"]

    movie_cast = end_credits_data.get("cast", [])

    movie_cast_members = [
        {
            "name": member["name"],
            "profile_path": f"https://image.tmdb.org/t/p/w500/{member['profile_path']}"
            if member["profile_path"]
            else None,
            "character": member["character"],
        }
        for member in movie_cast
    ]

    productions = movie_info_data.get("productions", [])

    directors = [
        staff["name"]
        for staff in end_credits_data["crew"]
        if staff["job"] == "Director"
    ]

    productions = [comp["name"] for comp in movie_info_data["production_companies"]]

    movie_trailer_key = ""
    if "results" in movie_trailer_data:
        trailer_results = movie_trailer_data["results"]
        for trailer in trailer_results:
            if trailer["type"] == "Trailer":
                movie_trailer_key = trailer["key"]
                break

    current_time = datetime.utcnow()  # Get the current UTC time
    malaysia_time = current_time + timedelta(hours=8)
    imdb_reviews = get_imdb_reviews(movie_info_data["title"])

    reviews = []

    if request.user.id:
        personalized_reviews = Review.objects.filter(movieID=movie_id)
        personalized_reviews = personalized_reviews.filter(
            movieID=movie_id, reviewDate__lte=malaysia_time
        )
        for personalized_review in personalized_reviews:
            comment = personalized_review.content
            user = User.objects.get(id=personalized_review.userID)
            movie_review_list = np.array([comment])
            movie_vector = vectorizer.transform(movie_review_list)
            pred = clf.predict(movie_vector)
            reviews_status = "Good" if pred else "Poor"
            review_info = {
                "id": personalized_review.reviewID,
                "author": user.username,
                "content": personalized_review.content,
                "date": personalized_review.reviewDate,
                "status": reviews_status,
            }
            reviews.append(review_info)

    malaysia_time_aware = timezone.make_aware(malaysia_time)
    reviews = sorted(reviews, key=lambda x: abs(x["date"] - malaysia_time_aware))
    for rev in imdb_reviews:
        date = rev["date"]
        movie_review_list = np.array([rev["content"]])
        movie_vector = vectorizer.transform(movie_review_list)
        pred = clf.predict(movie_vector)
        reviews_status = "Good" if pred else "Poor"
        review_info = {
            "author": rev["author"],
            "content": rev["content"],
            "date": date,
            "status": reviews_status,
        }
        reviews.append(review_info)

    movie_context = {
        "movie": movie_info_data,
        "productions": productions,
        "directors": directors,
        "movie_trailer_key": movie_trailer_key,
        "reviews": reviews,
        "related_movies": related_movies,
        "movie_casts": movie_cast_members,
        "popular_movies": popular_movies,
    }

    return render(request, "individualMovie.html", movie_context)


def format_money(money):
    money_str = f"{money:,}"
    return money_str


def top_box_office(request):
    apiKey = "0590e66205dca735336af409ce16babe"

    current_year = datetime.now().year

    top_box_office_url = f"https://api.themoviedb.org/3/discover/movie?api_key={apiKey}&sort_by=revenue.desc&language=en-US&primary_release_year={current_year}"
    top_box_office_res = requests.get(top_box_office_url)
    top_box_office_data = top_box_office_res.json()

    top_box_office = top_box_office_data["results"][:10]  # Get the top 10 movies

    # Fetch additional movie details including the total revenue
    for movie in top_box_office:
        movie_id = movie["id"]
        movie_details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={apiKey}&language=en-US"
        movie_details_res = requests.get(movie_details_url)
        movie_details_data = movie_details_res.json()

        # Update the movie data with the total revenue
        revenue = movie_details_data["revenue"]
        formatted_revenue = format_money(revenue)
        movie["revenue"] = formatted_revenue

        budget = movie_details_data["budget"]
        formatted_budget = format_money(budget)
        movie["budget"] = formatted_budget

    movie_categories_context = {
        "top_box_office": top_box_office,
    }
    return render(request, "top_box_office.html", movie_categories_context)


def get_latest_review(id):
    try:
        review = Review.objects.filter(userID=id).latest("reviewDate")
        return review
    except Review.DoesNotExist:
        return None


# Account Page Access
def profile(request):
    apiKey = "0590e66205dca735336af409ce16babe"

    userID = request.user.id
    recent_review = get_latest_review(userID)
    movie_info_data = None

    # Get movie information only if user has made a review ever
    if recent_review:
        movie_id = recent_review.movieID
        movie_info_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={apiKey}&language=en-US"
        movie_info_res = requests.get(movie_info_url)
        movie_info_data = movie_info_res.json()

    user_watchlist = Watchlist.objects.filter(userID=request.user.id).values_list(
        "movieID", flat=True
    )
    # Get all movie IDs in the user's watchlist
    watchlist_movie_ids = list(user_watchlist)
    watchlist_movies = []
    for movie_id in watchlist_movie_ids:
        watchlist_movies_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={apiKey}&language=en-US"
        watchlist_movies_res = requests.get(watchlist_movies_url)
        watchlist_movies_data = watchlist_movies_res.json()
        watchlist_movies.append(watchlist_movies_data)

    reviews = []
    if recent_review:
        comment = recent_review.content
        movie_review_list = np.array([comment])
        movie_vector = vectorizer.transform(movie_review_list)
        pred = clf.predict(movie_vector)
        reviews_status = "Good" if pred else "Poor"
        review_info = {
            "author": request.user.username,
            "content": recent_review.content,
            "date": recent_review.reviewDate,
            "status": reviews_status,
        }
        print(reviews_status)
        reviews.append(review_info)

    account_context = {
        "watchlist_movies": watchlist_movies,
        "recent_review": reviews,
        "movie": movie_info_data,
    }
    return render(request, "account.html", account_context)


def memory_game(request):
    apiKey = "0590e66205dca735336af409ce16babe"
    movies = []

    for page in range(1, 11):  # Fetch 10 pages of movies (total 100 movies)
        movie_url = f"https://api.themoviedb.org/3/discover/movie?api_key={apiKey}&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page={page}&vote_count.gte=500"
        movie_res = requests.get(movie_url)
        movie_data = movie_res.json()
        movies += movie_data["results"]

    # Randomly select 6 movies and duplicate them
    selected_movies = random.sample(movies, 6)
    total_movies = selected_movies + selected_movies
    random.shuffle(total_movies)

    movie_context = {
        "movies": total_movies,
    }

    return render(request, "memory_game.html", movie_context)
