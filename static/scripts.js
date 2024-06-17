// Get the modal
var modal = document.getElementById("flashMessageModal");

// Get the <span> element that closes the modal
var closeModal = document.getElementsByClassName("close")[0];

// Show the modal when the page loads
window.onload = function() {
    if (modal) {
        modal.style.display = "block";
        setTimeout(function() {
            modal.style.display = "none";
        }, 5000); // Change the time (in milliseconds) as needed
    }
}

// When the user clicks on <span> (x), close the modal
if (closeModal) {
    closeModal.onclick = function() {
        modal.style.display = "none";
    }
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}
