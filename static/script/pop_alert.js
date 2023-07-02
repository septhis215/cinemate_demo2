// Search query error response
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');
const errorMsg = [
    "You didn't enter a search query. Let's fix that!",
    "Uh oh! Looks like you forgot to enter a search query!",
    "Give your search buddy something before you go!",
    "We can't read your mind! Give us a clue!"
]

// pop-up error for emoty search query
searchForm.addEventListener('submit', (e) => {
    const randErrorMesg = Math.floor(Math.random() * errorMsg.length);
    if (searchInput.value.trim() === '') {
        e.preventDefault();
        swal({
            title: "Empty Search!",
            text: errorMsg[randErrorMesg],
            icon: "warning",
            button: "Got it!",
            closeOnClickOutside: true,
            closeOnEsc: true,
            timer: 5000,
            animation: "pop"
        });
    }
});

function watchlistAlert() {
    swal({
        icon: 'error',
        title: 'Oops...',
        text: 'Please sign to access your watchlist',
        button: "Got it!",
        closeOnClickOutside: true,
        closeOnEsc: true,
        timer: 5000,
        animation: "pop"
    })
}

