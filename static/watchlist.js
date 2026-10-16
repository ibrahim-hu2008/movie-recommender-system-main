let watchlistButton = document.getElementById('watchlist');

watchlistButton.addEventListener('click', function() {

        fetch("/addto_watchlist", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ movie_id: movieId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Added to Watchlist!");
            } else {
                alert("There was an error: " + data.message);
            }
        })
 });



   