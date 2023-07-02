from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("recent_movie/", views.recent_movie, name="recent_movie"),
    path("top_movie/", views.top_movie, name="top_movie"),
    path("popular_movie/", views.popular_movie, name="popular_movie"),
    path("fan_fav/", views.fan_fav, name="fan_fav"),
    path("upcoming_movie/", views.upcoming_movie, name="upcoming_movie"),
    path("movie/<int:movie_id>/", views.movie_info, name="movie_info"),
    path("movie/<int:movie_id>/reviews/", views.movie_reviews, name="movie_reviews"),
    path("loginPage/", views.login_page, name="login_page"),
    path("registerPage/", views.register_page, name="register_page"),
    path("forgotPasswordPage/", views.reset_password_page, name="reset_password_page"),
    path("forgotPassword/", views.forgotPassword, name="forgotPassword"),
    path("register/", views.register, name="register"),
    path("checkWatchlist/", views.checkWatchlist, name="checkWatchlist"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("movie/<int:movie_id>/addReview", views.addReview, name="addReview"),
    path("movie/<int:movie_id>/deleteReview/", views.deleteReview, name="deleteReview"),
    path("toggle-watchlist/", views.toggleWatchlist, name="toggleWatchlist"),
    path("search_movies/", views.search_movies, name="search_movies"),
    path("profile", views.profile, name="profile"),
    path("watchlist/", views.watchlist, name="watchlist"),
    path("top_box_office/", views.top_box_office, name="top_box_office"),
    path("preferences/", views.preferences, name="preferences"),
    path("fetch_genre/", views.fetch_genre, name="fetch_genre"),
    path("process_genres/", views.process_genres, name="process_genres"),
    path("recommend/", views.recommend, name="recommend"),
    path("movie_memory_game/", views.memory_game, name="memory_game"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
