async function openModal(title) {
    // pulls the elements from index.html which itself pulls from the app.py file which links the .db files to the website.
    const modal = document.getElementById('recipe-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalImg = document.getElementById("modal-image");
    const ingList = document.getElementById("modal-ingredients");
    const stepList = document.getElementById("modal-steps");

    // shows the pop up and displays the title (which is the title of the recipe)
    modal.style.display = "block";
    modalTitle.innerText = title;

    // clears the last entry and puts in place holders if the flask script is slow.
    ingList.innerHTML = '<li>Loading ingredients...</li>;'
    stepList.innerHTML = '<li>Loading directions...</li>;'
    modalImg.style.display = "none";

    // pulls the data from the flask script via the element IDs in html.
    try {
        // handles cases where the title has an apostophe (would otherwise throw an error because the "'" in the title closes the quote).
        const response = await fetch(`/get_recipe_details/${encodeURIComponent(title)}`);
        const data = await response.json();

        // converts the error message from one that would crash to one that can be handled later.
        if (data.error) throw new Error(data.error);

        // checks if an image is present in the data and if so, allows the image to be displayed in the modal.
        if (data.image) {
            modalImg.src = data.image;
            modalImg.style.display = "block";
        }

        // loads the ingredients and the directions as a list of elements.
        ingList.innerHTML = data.ingredients.map(item => `<li>${item.trim()}</li>`).join('');
        stepList.innerHTML = data.directions.map(item => `<li>${item.trim()}</li>`).join('');

        // again, catches the error so the website doesnt crash.
    } catch (error) {
        console.error('Error fetching recipe details: ', error);
        ingList.innerHTML = '<li>Could not load ingredients.</li>';
        stepList.innerHTML = '<li>Could not load directions.</li>';
    }
}

function closeModal() {
    document.getElementById('recipe-modal').style.display = "none";
}
// allows for the title of the recipe to be clicked on to open the window.
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('recipe-title')) {
        const title = event.target.getAttribute('data-title');
        openModal(title);
    }
    
    // makes it so you are able to click outside of the window to close it.
    let modal = document.getElementById('recipe-modal');
    if (event.target == modal) {
        closeModal();
    }
});