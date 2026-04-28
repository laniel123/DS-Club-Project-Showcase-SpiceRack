// ── tab switching ─────────────────────────────────────────────────────────────

function switchTab(tabId, clickedElement) {
    document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");
    document.querySelectorAll('.user-tab, .recipe-tab').forEach(t => t.classList.remove('active-tab'));
    
    const target = document.getElementById(tabId);
    if (target) {
        target.style.display = 'block'; // Ensures JS doesn't break the CSS
    }

    if (clickedElement) clickedElement.classList.add('active-tab')
}

async function openRecipeTab(title) {
    // handles special characters so as to not cause any issues later in the code
    const safeTitle = title.replace(/[^a-zA-Z0-9]/g, '-');
    const tabId     = "recipe-tab-" + safeTitle;
    const contentId = "recipe-content-" + safeTitle;

    // switches to tab if it already exists.
    if (document.getElementById(tabId)) {
        switchTab(contentId, document.getElementById(tabId));
        return;
    }

    // connects to the tab container in the HTML code
    const tabsContainer = document.querySelector(".recipe-tabs");
    // creates a new tab in the container
    const newTab = document.createElement("div");

    // attributes belonging to the newly created tab element
    newTab.id = tabId;
    newTab.className = "recipe-tab user-tab";
    newTab.innerHTML = `
        <h1 class="recipe-header-title" style="font-size: 0.9rem;">${title}</h1>
        <span class="close-tab" onclick="closeRecipeTab(event, '${contentId}', '${tabId}')">×</span>
    `;
    newTab.onclick = () => switchTab(contentId, newTab);
    tabsContainer.appendChild(newTab);

    // connects to the recipe-box element from HTML
    const recipeBox = document.querySelector('.recipe-box');
    // creates a new div element to "replace" (not really) the current "body-r" element
    const newContent = document.createElement('div');

    // attributes of the newly created div element
    newContent.id = contentId;
    newContent.className = 'body-r tab-content recipe-detail-view';
    newContent.style.display = 'none';
    newContent.innerHTML = `<div class="loading-recipe">Loading ${title}...</div>`;
    recipeBox.appendChild(newContent);

    // switches to the new tab and body element when the recipe title is clicked on
    switchTab(contentId, newTab);

    // gets the proper information to populate the new element
    try {
        const response = await fetch(`/get_recipe_details/${encodeURIComponent(title)}`);
        const data     = await response.json();
        if (data.error) throw new Error(data.error);

        // creation of the elements to be placed on the new body element, all pulled from the existing data.
        const ingHtml  = data.ingredients.map(i => `<li>${i.trim()}</li>`).join("");
        const stepHtml = data.directions.map(d => `<li>${d.trim()}</li>`).join("");
        const imgHtml  = data.image ? `<img src="${data.image}" alt="${title}" class="recipe-detail-img">` : '';

        // HTML content of the new elements, ensures the structure is in line with the current structure
        newContent.innerHTML = `
            <div class="recipe-detail-header">
                <h2>${title}</h2>
            </div>
            <div class="recipe-detail-body">
                ${imgHtml}
                <div class="recipe-detail-columns">
                    <div class="ingredients-col">
                        <h3>Ingredients</h3>
                        <ul>${ingHtml}</ul>
                    </div>
                    <div class="directions-col">
                        <h3>Directions</h3>
                        <ol>${stepHtml}</ol>
                    </div>
                </div>
            </div>
        `;
    // prevents website crash if data cannot be retrieved 
    } catch (error) {
        newContent.innerHTML = `<div class="error-msg">Could not load recipe details.</div>`;
    }

}

function closeRecipeTab(event, contentId, tabId) {
    // ensures that the tab isnt switched to when the x is clicked.
    event.stopPropagation();
    
    const tab     = document.getElementById(tabId);
    const content = document.getElementById(contentId);
    const wasActive = tab.classList.contains('active-tab');
    
    if (tab) tab.remove();
    if (content) content.remove();

    // redirects you to "Your Recipes" tab if the current body was corresponding to the tab closed
    if (wasActive) {
        const yourRecipesTab = document.querySelector('.user-tab[onclick*="your-recipes-content"]');
        switchTab('your-recipes-content', yourRecipesTab);
    }
}

// recognizes the clicking on any of the tab related elements
document.addEventListener('click', function(event) {
    // open modal only when clicking the title text itself, not buttons inside the card
    if (event.target.classList.contains('recipe-title')) {
        openRecipeTab(event.target.getAttribute('data-title'));
    }
});


// ── heart / save ──────────────────────────────────────────────────────────────

function toggleSave(event, btn) {
    event.stopPropagation();
    event.preventDefault();

    // read data from attributes — avoids apostrophe breaking JS strings
    const title   = btn.getAttribute('data-title');
    const profile = btn.getAttribute('data-profile');
    const rawMatched = btn.getAttribute('data-matched');
    const matched = (rawMatched && rawMatched.trim()) ? JSON.parse(rawMatched) : [];

    const isSaved = btn.classList.contains('saved');

    if (isSaved) {
        // optimistic UI update first
        btn.classList.remove('saved');
        btn.innerHTML = '♡';
        btn.title = 'Save to Your Recipes';

        fetch('/unsave_recipe', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ title: title })
        }).catch(err => console.error('unsave failed:', err));

        // if in your-recipes tab, fade and remove the card
        const card = btn.closest('.recipe-item');
        const tab  = card ? card.closest('.tab-content') : null;
        if (tab && tab.id === 'your-recipes-content') {
            card.style.opacity    = '0';
            card.style.transition = 'opacity 0.3s';
            setTimeout(() => card.remove(), 300);
        }

    } else {
        // optimistic UI update first
        btn.classList.add('saved');
        btn.innerHTML = '♥';
        btn.title = 'Saved';

        // pop animation
        btn.style.transform = 'scale(1.5)';
        btn.style.color     = '#e05c7a';
        setTimeout(() => { btn.style.transform = 'scale(1)'; }, 200);

        fetch('/save_recipe', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                title:   title,
                profile: profile,
                matched: matched
            })
        }).then(r => r.json())
          .then(d => { location.reload(); })
          .catch(err => console.error('save failed:', err));
    }
}

function toggleSpiceFav(event, spiceId) {
    event.preventDefault();
    event.stopPropagation();
    
    fetch('/toggle_spice_favorite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ spice_id: spiceId })
    }).then(r => r.json())
      .then(() => {
          location.reload();
      })
      .catch(err => console.error('error toggling spice favorite:', err));
}

// ── barcode scanner ───────────────────────────────────────────────────────────

function openBarcodeModal() {
    document.getElementById('barcode-modal').style.display = 'flex';
}

function closeBarcodeModal() {
    document.getElementById('barcode-modal').style.display = 'none';
    document.getElementById('barcode-result').innerText    = '';
    document.getElementById('barcode-result').style.color  = '#888';
    document.getElementById('barcode-file').value          = '';
}

async function submitBarcode() {
    const fileInput = document.getElementById('barcode-file');
    const result    = document.getElementById('barcode-result');

    if (!fileInput.files.length) {
        result.innerText = 'Please choose a photo first.';
        return;
    }

    result.innerText    = 'Scanning...';
    result.style.color  = '#888';

    const formData = new FormData();
    formData.append('barcode_image', fileInput.files[0]);

    try {
        const resp = await fetch('/scan_barcode', { method: 'POST', body: formData });
        const data = await resp.json();
        result.innerText = data.message;
        if (data.success) {
            result.style.color = '#4A6741';
            setTimeout(() => { closeBarcodeModal(); location.reload(); }, 1500);
        } else {
            result.style.color = '#c0392b';
        }
    } catch (e) {
        result.innerText   = 'Something went wrong. Try again.';
        result.style.color = '#c0392b';
    }
}

// causes all flash elements on screen to fade out when they appear
document.addEventListener('DOMContentLoaded', () => {
    const flashes = document.querySelectorAll('.flash');
    
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.classList.add('fade-out');
            
            setTimeout(() => {
                flash.remove();
            }, 400); 
            
        }, 3500); 
    });
});

// ── dynamic recipe filtering ──────────────────────────────────────────────────

function applyFilters() {
    const selectedCourse = document.getElementById('course-filter').value.trim().toLowerCase();
    const checkedDiets = Array.from(document.querySelectorAll('.diet-filter:checked')).map(cb => cb.value.trim().toLowerCase());

    document.querySelectorAll('.recipe-item').forEach(item => {
        const courseAttr = item.getAttribute('data-course') || "";
        const course = courseAttr.trim().toLowerCase();
        const dietsAttr = item.getAttribute('data-diets') || "";
        const itemDiets = dietsAttr ? dietsAttr.split(',').map(d => d.trim().toLowerCase()) : [];

        const courseMatch = (selectedCourse === 'all' || course === selectedCourse);
        
        const dietMatch = checkedDiets.every(d => itemDiets.includes(d));

        if (courseMatch && dietMatch) {
            item.style.display = ''; 
        } else {
            item.style.display = 'none';
        }
    });
}

// ── Global Search & Randomizer ──────────────────────────────────────────────

let searchTimer;

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('search-input');
    const searchTabBtn = document.getElementById('search-tab-button');

    if (!input) return;

    // Show tab and switch to it when user clicks the search bar
    input.addEventListener('focus', () => {
        if (searchTabBtn) {
            searchTabBtn.style.visibility = 'visible';
            switchTab('tab-search-all', searchTabBtn);
        }
    });

    // Debounce the API call while user types
    input.addEventListener('input', function() {
        const query = this.value.trim();
        clearTimeout(searchTimer);

        if (query.length < 2) return;

        searchTimer = setTimeout(async () => {
            try {
                const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const recipes = await response.json();
                renderSearchResults(recipes);
            } catch (error) {
                console.error("Search failed:", error);
            }
        }, 400); 
    });
});

function renderSearchResults(recipes) {
    const container = document.getElementById('tab-search-all');
    if (!container) return;

    if (!Array.isArray(recipes) || recipes.length === 0) {
        container.innerHTML = `<div class="empty-grid-msg"><p>${recipes.length === 0 ? "No recipes found matching your search." : "Server error."}</p></div>`;
        return;
    }

    // Generate text-only cards wrapped in the masonry grid
    container.innerHTML = `<div class="masonry-grid">` + recipes.map(r => `
        <div class="recipe-item text-only-card" data-course="${r.course}">
            <div class="card-top-row">
                <h3 class="recipe-title" onclick="openRecipeTab('${r.title.replace(/'/g, "\\'")}')" style="cursor: pointer; padding-right: 10px;">
                    ${r.title}
                </h3>
                <button class="heart-btn ${r.saved ? 'saved' : ''}"
                    data-title="${r.title.replace(/'/g, "&apos;")}"
                    onclick="toggleSave(event, this)"
                    title="Save to Your Recipes">
                    ${r.saved ? '♥' : '♡'}
                </button>
            </div>
            <ul class="recipe-category" style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                <li class="chip-course">${r.course || 'Global'}</li>
            </ul>
        </div>
    `).join('') + `</div>`;
}

function clearSearch() {
    const input = document.getElementById('search-input');
    const searchTabBtn = document.getElementById('search-tab-button');
    if (input) input.value = '';
    if (searchTabBtn) searchTabBtn.style.display = 'none';
    
    // Refresh page to clean up the UI
    location.reload();
}

async function randomRecipe() {
    const btn = document.getElementById('random-btn');
    if (btn) btn.style.transform = 'rotate(360deg)';

    try {
        const response = await fetch('/api/random_recipe');
        const data = await response.json();
        // Friend's code used openModal(), we use openRecipeTab()
        if (data.title) openRecipeTab(data.title);
    } catch (error) {
        console.error("Could not fetch random recipe:", error);
    } finally {
        if (btn) setTimeout(() => btn.style.transform = 'none', 500);
    }
}
