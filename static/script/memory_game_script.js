const cards = document.querySelectorAll(".memory-card");
const game = document.querySelector(".memory-game");
let flippedCard = false;
let firstCard, secondCard;
let lockBoard = false;
let match = 0;

function flipCard() {
    if (lockBoard) return;
    if (this === firstCard) return;
    this.classList.add("flip");
    if (!flippedCard) {
        // First Click
        flippedCard = true;
        firstCard = this;
        return;
    }
    // Second Click
    secondCard = this;

    checkForMatch();
    playAgain();
}

function checkForMatch() {
    // Do Card Match?
    let isMatch = firstCard.dataset.member === secondCard.dataset.member;
    isMatch ? disableCards() : unflipCards();
}

function disableCards() {
    firstCard.removeEventListener("click", flipCard);
    secondCard.removeEventListener("click", flipCard);
    match++;
    console.log(match);

    const posterPath = firstCard.querySelector(".front-face").src;
    const movieId = firstCard.dataset.memberId;
    const movieTitle = firstCard.dataset.member;

    console.log("Movie Poster Path:", posterPath);
    console.log("Movie ID:", movieId);
    console.log("Movie Title:", movieTitle);

    swal({
        title: "Movie Matched!",
        text: movieTitle,
        content: {
            element: "img",
            attributes: {
                src: posterPath,
                alt: movieTitle,
                style: "width: 200px; height: 300px;"
            }
        },
        buttons: {
            viewMovie: {
                text: "View Movie",
                value: "viewMovie",
            },
            continue: {
                text: "Continue",
                value: "continue",
            },
        },
        closeOnClickOutside: false,
        closeOnEsc: false,
    }).then((value) => {
        if (value === "viewMovie") {
            loading().then(() => {
                window.location.href = `/movie/${movieId}`;
            });
        } else if (value === "continue") {
            if (match == 6 || match > 6) {
                const modalOverlay = document.querySelector(".modal-overlay");
                const reloadBtn = document.querySelector(".reload");
                modalOverlay.classList.add("open-modal");

                reloadBtn.addEventListener("click", () => {
                    window.location.reload();
                });
            }
            resetBoard();
        } else {
            resetBoard();
        }
    });
}

function unflipCards() {
    lockBoard = true;
    setTimeout(() => {
        firstCard.classList.remove("flip");
        secondCard.classList.remove("flip");
        resetBoard();
    }, 1200);
}

function resetBoard() {
    [flippedCard, lockBoard] = [false, false];
    [firstCard, secondCard] = [null, null];
}
(function shuffle() {
    cards.forEach(card => {
        let randomPos = Math.floor(Math.random() * 12);
        card.style.order = randomPos;
    });
})();

function playAgain() {
    if (match == 6 || match > 6) {
        const modal = document.querySelector(".modal-overlay");
        const reloadBtn = document.querySelector(".reload");
        modal.classList.add("open-modal");

        reloadBtn.addEventListener("click", () => {
            window.location.reload();
        });
    }
}
cards.forEach(card => card.addEventListener("click", flipCard));