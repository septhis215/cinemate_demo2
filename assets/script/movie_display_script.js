const apiKey = "0590e66205dca735336af409ce16babe";
const popularMovieURL = `https://api.themoviedb.org/3/trending/movie/week?api_key=${apiKey}&language=en-US&page=1`;

const mCarousel = document.querySelector(".m-carousel");
const nextBtn = document.getElementById('next-btn');
const prevBtn = document.getElementById('prev-btn');

let currentPage = 0;

// Fetching movies
async function getRecentPopularMovies() {
    const res = await fetch(popularMovieURL);
    const dat = await res.json();
    return dat.results;
}

// Fetching movie trailers
async function getMovieTrailers(movieId) {
    const movieTrailersURL = `https://api.themoviedb.org/3/movie/${movieId}/videos?api_key=${apiKey}&language=en-US`;
    const res = await fetch(movieTrailersURL);
    const data = await res.json();
    return data.results;
}

nextBtn.addEventListener('click', () => {
    const totalSlides = Math.ceil(mCarousel.scrollWidth / mCarousel.offsetWidth);
    if (currentPage === totalSlides - 1) {
        mCarousel.scrollTo({ left: 0, behavior: 'auto' });
        currentPage = 0;
    } else {
        mCarousel.scrollLeft += mCarousel.offsetWidth;
        currentPage++;
    }
});

prevBtn.addEventListener('click', () => {
    const totalSlides = Math.ceil(mCarousel.scrollWidth / mCarousel.offsetWidth);
    if (currentPage === 0) {
        mCarousel.scrollTo({ left: mCarousel.scrollWidth * (totalSlides - 1), behavior: 'auto' });
        currentPage = totalSlides - 1;
    } else {
        mCarousel.scrollLeft -= mCarousel.offsetWidth;
        currentPage--;
    }
});

// Appending movies into movie carousel
async function appendNextMovieSlides() {
    const movies = await getRecentPopularMovies();
    movies.forEach(async(movie) => {
        // Element creation for slider
        const m_slide = document.createElement("div");
        const m_poster = document.createElement("div");
        const m_detail = document.createElement("div");
        const m_title = document.createElement("h2");
        const rating = document.createElement("span");
        const releaseDate = document.createElement("span");
        const m_desc = document.createElement("p");
        const m_dummy = document.createElement("div")

        // Specifically for fetching movie genres of every movie displayed
        const m_URL = `https://api.themoviedb.org/3/movie/${movie.id}?api_key=${apiKey}&language=en-US`;
        const res = await fetch(m_URL);
        const m_detail_genre = await res.json();
        const m_genre = m_detail_genre.genres.slice(0, 3);
        const m_genre_names = m_genre.map((genre) => genre.name);
        const m_genre_element = document.createElement("span");

        // Specifically for fetching the duration/runtime of a movie
        const duration = m_detail_genre.runtime;
        const durationElement = document.createElement("span");

        // Direct to Youtube Trailer
        const m_btn_container = document.createElement("div");
        const m_trailer = document.createElement("button");
        m_btn_container.classList.add("m-btn-container");
        m_trailer.classList.add("m-trailer");
        m_trailer.innerHTML = '<i class="fa-brands fa-youtube"></i>&nbsp;&nbsp;Trailer';

        const trailers = await getMovieTrailers(movie.id);
        if (trailers.length > 0) {
            const trailer_key = trailers[0].key;
            m_trailer.addEventListener("click", (e) => {
                e.preventDefault();
                createYouTubePopUp(trailer_key);
            });
        } else {
            m_trailer.style.display = "none";
        }

        // Dynamic movie carousel creation
        m_slide.classList.add("m-slide");
        m_poster.classList.add("m-poster");
        m_poster.style.backgroundImage = `url(https://image.tmdb.org/t/p/original/${movie.backdrop_path})`;
        m_dummy.classList.add("m-dummy")
        m_detail.classList.add("m-detail");
        m_title.classList.add("m-title");
        m_title.textContent = movie.title;
        rating.classList.add("m-rating");
        rating.innerHTML = `<i class="fa-solid fa-star"></i>&nbsp;&nbsp;${movie.vote_average.toFixed(2)}/10`;
        m_genre_element.classList.add("m-genre");
        m_genre_element.textContent = m_genre_names.join(", ");
        releaseDate.classList.add("m-release-date");
        releaseDate.innerHTML = `<i class="fa-regular fa-calendar"></i>&nbsp;&nbsp;${movie.release_date}`;
        durationElement.classList.add("m-duration");
        durationElement.innerHTML = `<i class="fa-regular fa-clock"></i>&nbsp;&nbsp;${duration} min`;
        m_desc.classList.add("m-overview");
        m_desc.textContent = movie.overview.length > 400 ? movie.overview.slice(0, 400) + "..." : movie.overview;

        m_title.addEventListener("click", () => {
            window.location.href = `/movie/${movie.id}`;
        });

        // Appending all elements 
        m_slide.appendChild(m_poster);
        m_slide.appendChild(m_dummy)
        m_slide.appendChild(m_detail);
        m_detail.appendChild(m_btn_container);
        m_btn_container.appendChild(m_trailer);
        m_detail.appendChild(m_title);
        m_detail.appendChild(rating);
        m_detail.appendChild(m_genre_element);
        m_detail.appendChild(releaseDate);
        m_detail.appendChild(durationElement);
        m_detail.appendChild(m_desc);
        mCarousel.appendChild(m_slide);
    });
}

function createYouTubePopUp(trailer_key) {
    const popUpContainer = document.createElement("div");
    const player = document.createElement("iframe");
    const closeBtn = document.createElement("button");

    player.src = `https://www.youtube.com/embed/${trailer_key}?autoplay=1`;
    player.allow = "autoplay";
    player.frameborder = "";
    player.allowfullscreen = false;

    popUpContainer.classList.add("youtube-popup-container");
    player.classList.add("youtube-popup");
    closeBtn.classList.add("popup-close-btn");
    closeBtn.innerHTML = '<i class="fa-solid fa-xmark"></i>&nbsp;&nbsp;Close';

    closeBtn.addEventListener("click", () => {
        popUpContainer.remove();
    });

    popUpContainer.appendChild(player);
    popUpContainer.appendChild(closeBtn);
    document.body.appendChild(popUpContainer);
}

function autoPlay() {
    setInterval(() => {
        const totalSlides = Math.ceil(mCarousel.scrollWidth / mCarousel.offsetWidth);
        if (currentPage === totalSlides - 1) {
            mCarousel.scrollTo({ left: 0, behavior: 'smooth' });
            currentPage = 0;
        } else {
            mCarousel.scrollLeft += mCarousel.offsetWidth;
            currentPage++;
        }
    }, 10000)
}


function setDetailHeight() {
    const m_detail = document.querySelectorAll(".m-detail");
    m_detail.forEach(detail => {
        detail.style.height = `${detail.parentElement.clientHeight}px`;
    });
}

window.addEventListener("resize", setDetailHeight);
setDetailHeight();

autoPlay();

appendNextMovieSlides();