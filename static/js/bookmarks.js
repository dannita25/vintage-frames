// File to handle js functions for Bookmark tool
document.addEventListener("DOMContentLoaded", function () {
    // Attach event listeners to all bookmark buttons
    document.querySelectorAll(".bookmark-btn").forEach(button => {
        button.addEventListener("click", toggleBookmark);
    });
});

// Toggle bookmark state
function toggleBookmark() {
    const movieTitle = this.getAttribute("data-movie-title");
    const isBookmarked = this.getAttribute("data-bookmarked") === "true";

    fetch(bookmarkUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            movie_title: movieTitle,
            bookmark: !isBookmarked
        })
        
    })
    
        .then(response => {
            if (response.ok) {
                // Update button state
                this.setAttribute("data-bookmarked", (!isBookmarked).toString());
                this.innerHTML = !isBookmarked
                    ? `<i class="bi bi-bookmark-fill"></i> Bookmarked`
                    : `<i class="bi bi-bookmark"></i> Bookmark`;
                this.classList.toggle("btn-primary", !isBookmarked);
                this.classList.toggle("btn-outline-primary", isBookmarked);
            } else {
                alert("Failed to update bookmark. Please log in or try again later.");
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert("An error occurred. Please try again later.");
        });
}
