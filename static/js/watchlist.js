// File to manage js functions for watchlist tool (frontend)
document.addEventListener("DOMContentLoaded", function () {
    const watchlistContainer = document.getElementById("watchlist-container");
    const emptyWatchlistMessage = document.getElementById("empty-watchlist");

    // If the watchlist container exists, fetch and render the watchlist
    if (watchlistContainer) {
        fetchAndRenderWatchlist();
    }

    // Fetch and render the watchlist
    function fetchAndRenderWatchlist() {
        fetch(getWatchlistUrl)
            .then(response => response.json())
            .then(data => {
                if (data.watchlist && data.watchlist.length > 0) {
                    watchlistContainer.innerHTML = ""; // Clear current list
                    emptyWatchlistMessage.classList.add("d-none"); // Hide empty message

                    // Populate the container with movie cards
                    data.watchlist.forEach(movie => {
                        const movieItem = `
                            <div class="col-md-6 mb-4">
                                <div class="card h-100">
                                    <div class="card-body">
                                        <h5 class="card-title">${movie.title}</h5>
                                        <button class="btn btn-danger remove-movie-btn" 
                                                data-movie-title="${movie.title}">
                                            Remove from Watchlist
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `;
                        watchlistContainer.innerHTML += movieItem;
                    });

                    // Attach event listeners to "Remove from Watchlist" buttons
                    addRemoveEventListeners();
                } else {
                    // Show empty message if no movies are in the watchlist
                    watchlistContainer.innerHTML = "";
                    emptyWatchlistMessage.classList.remove("d-none");
                }
            })
            .catch(error => console.error("Error fetching watchlist:", error));
    }

    // Attach event listeners to "Remove from Watchlist" buttons
    function addRemoveEventListeners() {
        document.querySelectorAll(".remove-movie-btn").forEach(button => {
            button.addEventListener("click", removeFromWatchlist);
        });
    }

    // Function to remove a movie from the watchlist
    function removeFromWatchlist() {
        const movieTitle = this.getAttribute("data-movie-title");

        if (confirm("Are you sure you want to remove this movie from your watchlist?")) {
            fetch(`/bookmark`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    movie_title: movieTitle,
                    bookmark: false,
                }),
            })
                .then(response => {
                    if (response.ok) {
                        // Remove the movie card from the DOM
                        this.closest(".col-md-6").remove();

                        // If no more movies are left, show the empty message
                        if (watchlistContainer.children.length === 0) {
                            emptyWatchlistMessage.classList.remove("d-none");
                        }
                    } else {
                        alert("Failed to remove movie from watchlist.");
                    }
                })
                .catch(error => console.error("Error removing movie:", error));
        }
    }
});
