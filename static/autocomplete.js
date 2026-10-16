window.addEventListener("load", function() {
    let filmInput = document.getElementById("input-box");
    let resultsBox = document.querySelector(".film-results ul");
    let addFilmButton = document.getElementById("addbutton");
    let posterSlots = document.querySelectorAll(".film-poster");

    let chosenFilm = null;
    let currentIndex = 0; // keep track of slot position
    let chosenFilmIds = []; // store IDs of picked films

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
                    });

                    resultsBox.appendChild(option);
                });
            });
    });

    // add film poster into the next slot
    addFilmButton.addEventListener("click", function() {
        if (!chosenFilm) {
            alert("Please choose a film first!");
            return;
        }

        // check for duplicate
        if (chosenFilmIds.includes(chosenFilm.id)) {
            alert("You have already picked this film!");
            return;
        }

        // check max slots
        if (currentIndex >= posterSlots.length) {
            alert("You can only pick 3 favourite films!");
            return;
        }

        // build poster
        let posterLink = "https://image.tmdb.org/t/p/w500" + chosenFilm.poster_path;
        let slot = posterSlots[currentIndex];
        let posterImage = document.createElement("img");
        posterImage.src = posterLink;
        posterImage.alt = chosenFilm.title;
        posterImage.style.width = "100%";

        slot.innerHTML = ""; 
        slot.appendChild(posterImage);

        // track this film
        chosenFilmIds.push(chosenFilm.id);
        currentIndex++;

        // submit button appearing
        if (chosenFilmIds.length === 3) {
            document.getElementById("submit-btn").style.display = "inline-block";
        }
    });


    document.getElementById("submit-btn").addEventListener("click", function(e) {
        
        // stops link from redirecting so changes to db can be performed
        e.preventDefault();

        // fetch Flask route 
        fetch("/save-favourites", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                films: chosenFilmIds // list of favourite films
            })
        })
        
        .then(function(response) {
            return response.json();
        })

        .then(function(data) {
            // once saved, redirect to homepage 
            window.location.href = "/homepage";
        })          
    });



});

