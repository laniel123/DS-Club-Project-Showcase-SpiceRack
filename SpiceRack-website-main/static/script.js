// ── GLOBALS ───────────────────────────────────────────────────────────────────
let searchTimer;
let currentModalRecipe = { title: '', profile: '', matched: [] };

// ── TAB SYSTEM ────────────────────────────────────────────────────────────────

function switchTab(tabId, clickedElement) {
    // Hide all tab content panes
    document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
    // Deactivate all tab buttons
    document.querySelectorAll('.user-tab, .recipe-tab').forEach(t => t.classList.remove('active-tab'));

    const target = document.getElementById(tabId);
    if (target) target.style.display = 'block';
    if (clickedElement) clickedElement.classList.add('active-tab');
}

async function openRecipeTab(title) {
    const safeTitle = title.replace(/[^a-zA-Z0-9]/g, '-');
    const tabId     = 'recipe-tab-' + safeTitle;
    const contentId = 'recipe-content-' + safeTitle;

    // Switch to existing tab if already open
    if (document.getElementById(tabId)) {
        switchTab(contentId, document.getElementById(tabId));
        return;
    }

    // Add pill tab to the recipe-tabs strip
    const tabsContainer = document.querySelector('.recipe-tabs');
    const newTab = document.createElement('div');
    newTab.id = tabId;
    newTab.className = 'recipe-tab user-tab';
    newTab.innerHTML = `
        <h1 class="recipe-header-title" style="font-size:0.8rem;">${title}</h1>
        <button class="close-tab" onclick="closeRecipeTab(event,'${contentId}','${tabId}')">×</button>
    `;
    newTab.onclick = () => switchTab(contentId, newTab);
    tabsContainer.appendChild(newTab);

    // Create content pane inside recipe-box
    const recipeBox = document.querySelector('.recipe-box');
    const newContent = document.createElement('div');
    newContent.id = contentId;
    newContent.className = 'body-r tab-content recipe-detail-view';
    newContent.style.display = 'none';
    newContent.innerHTML = `<div class="loading-recipe">Loading ${title}...</div>`;
    recipeBox.appendChild(newContent);

    switchTab(contentId, newTab);

    try {
        const response = await fetch(`/get_recipe_details/${encodeURIComponent(title)}`);
        const data     = await response.json();
        if (data.error) throw new Error(data.error);

        const ingHtml  = data.ingredients.map(i => `<li>${i.trim()}</li>`).join('');
        const stepHtml = data.directions.map(d => `<li>${d.trim()}</li>`).join('');
        const imgHtml  = data.image
            ? `<img src="${data.image}" alt="${title}" class="recipe-detail-img">`
            : '';

        const isSaved   = data.saved || false;
        const profile   = data.profile || '';
        const matched   = data.matched || [];
        const heartClass = isSaved ? 'detail-heart saved' : 'detail-heart';
        const heartChar  = isSaved ? '♥' : '♡';

        newContent.innerHTML = `
            <div class="recipe-detail-header">
                <h2>${title}</h2>
                <button class="${heartClass}"
                    data-title="${title.replace(/"/g, '&quot;')}"
                    data-profile="${profile.replace(/"/g, '&quot;')}"
                    data-matched='${JSON.stringify(matched)}'
                    onclick="toggleSave(event, this)"
                    title="${isSaved ? 'Saved' : 'Save to Your Recipes'}">
                    ${heartChar}
                </button>
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
    } catch (error) {
        newContent.innerHTML = `<div class="error-msg">Could not load recipe details.</div>`;
    }
}

function closeRecipeTab(event, contentId, tabId) {
    event.stopPropagation();
    const tab     = document.getElementById(tabId);
    const content = document.getElementById(contentId);
    const wasActive = tab && tab.classList.contains('active-tab');

    if (tab)     tab.remove();
    if (content) content.remove();

    // Fall back to Recommends if the closed tab was active
    if (wasActive) {
        const recommendsBtn = document.querySelector('.user-tab[onclick*="tab-recommends"]');
        switchTab('tab-recommends', recommendsBtn);
    }
}

// Delegate title clicks to openRecipeTab
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('recipe-title')) {
        openRecipeTab(e.target.getAttribute('data-title'));
    }
});


// ── FILTER PANEL ──────────────────────────────────────────────────────────────

function toggleFilters() {
    const panel = document.getElementById('filter-bar-panel');
    const btn   = document.getElementById('filters-toggle');
    panel.classList.toggle('open');
    btn.classList.toggle('active');
}

function clearFilters() {
    document.querySelectorAll('input[name="pref"], input[name="course_pref"]')
        .forEach(cb => cb.checked = false);
    applyFilters();
}

// ── SPICE FAVORITE ────────────────────────────────────────────────────────────

function toggleSpiceFav(event, spiceId) {
    event.preventDefault();
    event.stopPropagation();
    fetch('/toggle_spice_favorite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ spice_id: spiceId })
    }).then(() => location.reload())
      .catch(err => console.error('toggleSpiceFav error:', err));
}

/**
 * Opens the recipe modal and fetches details from the server.
 */
async function openModal(title) {
    const modal = document.getElementById('recipe-modal');
    const img   = document.getElementById('modal-image');
    const ings  = document.getElementById('modal-ingredients');
    const steps = document.getElementById('modal-steps');
    const heart = document.getElementById('modal-heart');

    document.getElementById('modal-title').innerText = title;
    ings.innerHTML  = '<li>Loading...</li>';
    steps.innerHTML = '<li>Loading...</li>';
    img.style.display = 'none';
    modal.classList.add('open');

    // Store current recipe for save functionality
    currentModalRecipe.title = title;

    try {
        const r    = await fetch(`/get_recipe_details/${encodeURIComponent(title)}`);
        const data = await r.json();
        if (data.error) throw new Error(data.error);

        // Store profile and matched spices
        currentModalRecipe.profile = data.profile || '';
        currentModalRecipe.matched = data.matched || [];
        currentModalRecipe.saved = data.saved || false;

        // Update heart button state
        if (heart) {
            if (data.saved) {
                heart.classList.add('saved');
                heart.innerHTML = '♥';
            } else {
                heart.classList.remove('saved');
                heart.innerHTML = '♡';
            }
        }

        if (data.image) {
            img.src = data.image;
            img.style.display = 'block';
        }

        ings.innerHTML  = data.ingredients.map(i => `<li>${i.trim()}</li>`).join('');
        steps.innerHTML = data.directions.map(d => `<li>${d.trim()}</li>`).join('');
    } catch (e) {
        ings.innerHTML  = '<li>Could not load ingredients.</li>';
        steps.innerHTML = '<li>Could not load directions.</li>';
        console.error("Modal Error:", e);
    }
}

/**
 * Closes the recipe modal.
 */
function closeModal() {
    document.getElementById('recipe-modal').classList.remove('open');
}

/**
 * Handles saving/unsaving recipes from the modal.
 */
function toggleSaveFromModal(event) {
    event.stopPropagation();
    event.preventDefault();

    const btn = document.getElementById('modal-heart');
    const isSaved = btn.classList.contains('saved');

    if (isSaved) {
        // Unsave
        btn.classList.remove('saved');
        btn.innerHTML = '♡';
        fetch('/unsave_recipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: currentModalRecipe.title })
        });
    } else {
        // Save
        btn.classList.add('saved');
        btn.innerHTML = '♥';
        btn.style.transform = 'scale(1.4)';
        setTimeout(() => btn.style.transform = '', 200);

        fetch('/save_recipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: currentModalRecipe.title,
                profile: currentModalRecipe.profile,
                matched: currentModalRecipe.matched
            })
        });
    }
}

// ── TAB SYSTEM ────────────────────────────────────────────────────────────────

// ── SEARCH LOGIC (DATABASE INTEGRATION) ───────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('search-input');
    const searchTabBtn = document.getElementById('search-tab-button');

    if (!input) return;

    input.addEventListener('focus', () => {
        switchTab('tab-search-all', null);
    });

    // 2. Input Logic: Fetch from Database with Debounce
    input.addEventListener('input', function() {
        const query = this.value.trim();
        clearTimeout(searchTimer); // Clear existing timer to prevent lag

        if (query.length < 2) {
            return;
        }

        searchTimer = setTimeout(async () => {
            try {
                // Hits the /api/search route in app.py
                const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const recipes = await response.json();
                renderSearchResults(recipes);
            } catch (error) {
                console.error("Search failed:", error);
            }
        }, 400); // Wait 400ms after user stops typing
    });
});

// Auto-apply filters when any checkbox changes so unchecking immediately takes effect
document.addEventListener('DOMContentLoaded', () => {
    let filterTimer;
    document.querySelectorAll('input[name="pref"], input[name="course_pref"]').forEach(cb => {
        cb.addEventListener('change', () => {
            clearTimeout(filterTimer);
            filterTimer = setTimeout(applyFilters, 300);
        });
    });
});

/**
 * Renders database search results into the Search All grid.
 */
function renderSearchResults(recipes) {
    const grid = document.getElementById('global-search-results');
    if (!grid) return;

    // Safety check: if recipes is not an array (due to 500 error), stop here
    if (!Array.isArray(recipes)) {
        grid.innerHTML = '<p class="empty-sub">Server error. Please check your backend.</p>';
        return;
    }

    if (recipes.length === 0) {
        grid.innerHTML = '<p class="empty-sub">No recipes found matching your search.</p>';
        return;
    }

    // Build text-only cards
    grid.innerHTML = recipes.map(r => `
        <article class="recipe-card text-only-card" data-title="${r.title}" onclick="openRecipeTab(this.dataset.title)">
            <div class="card-body">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <p class="card-profile">GLOBAL DATABASE</p>
                    <button class="card-heart ${r.saved ? 'saved' : ''}" 
                            onclick="toggleSave(event, this)" 
                            data-title="${r.title}"
                            style="position: static; width: 24px; height: 24px; font-size: 14px;">
                        ${r.saved ? '♥' : '♡'}
                    </button>
                </div>
                <h3 class="card-title">${r.title}</h3>
            </div>
        </article>
    `).join('');
}

/**
 * Clears the search input and refreshes view.
 */
function clearSearch() {
    const input = document.getElementById('search-input');
    if (input) input.value = '';
    const recommendsBtn = document.querySelector('.user-tab[onclick*="tab-recommends"]');
    switchTab('tab-recommends', recommendsBtn);
}
//-DIETARY RESTRICTIONS LOGIC────────────────────────────────────────────────────

/**
 * Gathers all checked preferences and reloads the page with query params.
 */
function applyFilters() {
    // 1. Collect Dietary Preferences (name="pref")
    const prefs = Array.from(document.querySelectorAll('input[name="pref"]:checked'))
                       .map(i => `pref=${encodeURIComponent(i.value)}`);
    
    // 2. Collect Course Selections (name="course_pref")
    const courses = Array.from(document.querySelectorAll('input[name="course_pref"]:checked'))
                         .map(i => `course_pref=${encodeURIComponent(i.value)}`);
    
    // 3. Merge into one query string and redirect
    const queryString = [...prefs, ...courses].join('&');
    window.location.href = queryString ? `/?${queryString}` : '/';
}





// ── RANDOMIZER ────────────────────────────────────────────────────────────────

/**
 * Picks a random recipe from the ENTIRE database via the server.
 */
async function randomRecipe() {
    const btn = document.getElementById('random-btn');
    
    // Visual feedback that it's thinking
    if (btn) btn.style.transform = 'rotate(360deg)';
    
    try {
        const response = await fetch('/api/random_recipe');
        const data = await response.json();
        
        if (data.title) {
            openRecipeTab(data.title);
        }
    } catch (error) {
        console.error("Could not fetch random recipe:", error);
    } finally {
        if (btn) {
            setTimeout(() => btn.style.transform = 'none', 500);
        }
    }
}

// ── HEART / SAVE SYSTEM ───────────────────────────────────────────────────────

/**
 * Handles saving and unsaving recipes via AJAX.
 */
function toggleSave(event, btn) {
    event.stopPropagation();
    event.preventDefault();

    const title   = btn.getAttribute('data-title');
    const profile = btn.getAttribute('data-profile') || "";
    const raw     = btn.getAttribute('data-matched');
    const matched = (raw && raw.trim() && raw !== "undefined") ? JSON.parse(raw) : [];
    const isSaved = btn.classList.contains('saved');

    if (isSaved) {
        btn.classList.remove('saved');
        btn.innerHTML = '♡';
        btn.title = 'Save to Your Recipes';
        fetch('/unsave_recipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title })
        });

        // If in Saved tab, fade and remove the card
        const card = btn.closest('.recipe-card');
        const tab  = card?.closest('.tab-content');
        if (tab && tab.id === 'tab-saved') {
            card.style.transition = 'opacity 0.3s';
            card.style.opacity = '0';
            setTimeout(() => card.remove(), 300);
        }
    } else {
        btn.classList.add('saved');
        btn.innerHTML = '♥';
        btn.title = 'Saved';
        btn.style.transform = 'scale(1.4)';
        setTimeout(() => btn.style.transform = '', 200);

        fetch('/save_recipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, profile, matched })
        });
    }
}

// ── BARCODE SCANNER ───────────────────────────────────────────────────────────

function openBarcodeModal() {
    document.getElementById('barcode-modal').style.display = 'flex';
}

function closeBarcodeModal() {
    document.getElementById('barcode-modal').style.display = 'none';
    document.getElementById('barcode-result').innerText = '';
    document.getElementById('barcode-file').value = '';
}

async function submitBarcode() {
    const file   = document.getElementById('barcode-file');
    const result = document.getElementById('barcode-result');
    if (!file.files.length) { result.innerText = 'Choose a photo first.'; return; }

    result.innerText   = 'Scanning...';
    result.style.color = '#888';

    const fd = new FormData();
    fd.append('barcode_image', file.files[0]);

    try {
        const r    = await fetch('/scan_barcode', { method: 'POST', body: fd });
        const data = await r.json();
        result.innerText   = data.message;
        result.style.color = data.success ? '#3D5A3E' : '#c0392b';
        if (data.success) setTimeout(() => { closeBarcodeModal(); location.reload(); }, 1500);
    } catch (e) {
        result.innerText   = 'Something went wrong.';
        result.style.color = '#c0392b';
    }
}