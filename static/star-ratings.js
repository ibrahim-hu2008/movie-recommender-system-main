let stars = document.querySelectorAll('.rating input');
let showValue = document.getElementById('rating-value');

for (let i = 0; i < stars.length; i++) {
    stars[i].addEventListener('click', function() {
        let rating = this.value;
        showValue.innerHTML = rating + " out of 5";
    });
}
