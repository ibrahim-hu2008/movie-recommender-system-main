window.addEventListener("load", function() {
    let filmInput = document.getElementById("input-box");
    let resultsBox = document.querySelector(".film-results ul");
    let moviePoster = document.querySelector(".movie-poster");
    let movieLink = document.getElementById("movie-link");

    let chosenFilm = null;

    // autocomplete
    filmInput.addEventListener("input", function() {
        let searchText = filmInput.value;

        if (searchText === "") {
            resultsBox.innerHTML = "";
            return;
        }

        fetch("/autocomplete?q=" + encodeURIComponent(searchText))
            .then(response => response.json())
            .then(films => {
                resultsBox.innerHTML = "";

                films.forEach(function(film) {
                    let option = document.createElement("li");
                    option.classList.add("film-result");
                    option.textContent = film.title + " (" + film.year + ")";
                    option.dataset.id = film.id;
                    option.dataset.poster = film.poster_path;

                    option.addEventListener("click", function() {
                        filmInput.value = film.title + " (" + film.year + ")";
                        resultsBox.innerHTML = "";
                        chosenFilm = film;

                        console.log(film.id);

                        // build poster
                        let posterLink = "https://image.tmdb.org/t/p/w500" + chosenFilm.poster_path;
                        let posterImage = document.createElement("img");
                        posterImage.src = posterLink;
                        posterImage.alt = chosenFilm.title;
                        posterImage.style.width = "100%";

                        moviePoster.innerHTML = ""; 
                        moviePoster.appendChild(posterImage);

                        let moviepageLink = "/moviepage/" + film.id;
                        console.log(moviepageLink);
                        movieLink.href = moviepageLink;

                    });

                    resultsBox.appendChild(option);
                });
            });
    });

});

