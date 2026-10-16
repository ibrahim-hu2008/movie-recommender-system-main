// star ratings
let stars = document.querySelectorAll('.rating input');
let showValue = document.getElementById('rating-value');
let ratingValue = null

for (let i = 0; i < stars.length; i++) {
    stars[i].addEventListener('click', function() {
        ratingValue = this.value;
        showValue.innerHTML = ratingValue + " out of 5";
    });
}

// get the elements from the HTML
let form = document.querySelector('.review-form');
let reviewBox = document.getElementById('review');
let errorMsg = document.querySelector('.error-message');
let submitButton = document.querySelector('.button.submit');

// when user clicks submit button
submitButton.addEventListener('click', function(event) {
    event.preventDefault(); // stops page from reloading

    let reviewText = reviewBox.value.trim();
    let minLength = 100;
    let maxLength = 1000;

    if (!ratingValue) {
        alert("Please select a rating before submitting a review!");
        return;
    }

    // check if review is too short
    if (reviewText.length < minLength) {
        errorMsg.textContent = "Reviews must be at least " + minLength + " characters long.";
        errorMsg.style.display = "block";
        errorMsg.style.color = "red";
        return;
    }

    // check if the review is too long
    if (reviewText.length > maxLength) {
        errorMsg.textContent = "Reviews must be no more than " + maxLength + " characters.";
        errorMsg.style.display = "block";
        errorMsg.style.color = "red";
        return;
    }

    // send review to backend
    fetch('/submit_review', {
        method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                review: reviewText, 
                rating: ratingValue,
                movie_id: movieId})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Your review has been submitted successfully!");
                reviewBox.value = ""; // clear text area

                // remove from watchlist
                fetch("/removefrom_watchlist", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ movie_id: movieId })
                });
                
            } else {
                alert("There was an error: " + data.message);
            }
        })
 });



