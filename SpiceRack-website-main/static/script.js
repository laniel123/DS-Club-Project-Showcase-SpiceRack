// ── GLOBALS ───────────────────────────────────────────────────────────────────
let searchTimer; // Only declared once at the top
let currentModalRecipe = { title: '', profile: '', matched: [] }; // Track current recipe in modal

// ── MODAL LOGIC ───────────────────────────────────────────────────────────────

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

/**
 * Switches between "Your Recipes", "Recommendations", and "Search All".
 */
function switchTab(tabId, btn) {
    // Hide all contents
    document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
    
    // Deactivate all buttons
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    
    // Show target tab
    const target = document.getElementById(tabId);
    if (target) {
        target.style.display = 'block';
    }
    
    // Activate clicked button
    if (btn) btn.classList.add('active');
}

// ── SEARCH LOGIC (DATABASE INTEGRATION) ───────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('search-input');
    const searchTabBtn = document.getElementById('search-tab-button');
    
    if (!input) return;

    // 1. Focus Logic: Reveal button and jump to 'Search All' tab
    input.addEventListener('focus', () => {
        if (searchTabBtn) {
            searchTabBtn.style.display = 'inline-block'; // Reveals the hidden tab button
            switchTab('tab-search-all', searchTabBtn);  // Automatically switches view
        }
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
        <article class="recipe-card text-only-card" data-title="${r.title}" onclick="openModal(this.dataset.title)">
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
    const searchTabBtn = document.getElementById('search-tab-button');
    
    if (input) input.value = '';
    
    // Hide the tab button again
    if (searchTabBtn) {
        searchTabBtn.style.display = 'none';
    }
    
    // Switch back to Recommendations or Your Recipes
    const recommendsBtn = document.querySelector('button[onclick*="tab-recommends"]');
    switchTab('tab-recommends', recommendsBtn);
    
    location.reload(); 
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
            // Open the modal for the random title found
            openModal(data.title);
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
        // Unsave Logic
        btn.classList.remove('saved');
        btn.innerHTML = '♡';
        fetch('/unsave_recipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title })
        });
        
        // If we are currently in the Saved tab, remove the card visually
        const card = btn.closest('.recipe-card');
        const tab  = card?.closest('.tab-content');
        if (tab && tab.id === 'tab-saved') {
            card.style.transition = 'opacity 0.3s';
            card.style.opacity = '0';
            setTimeout(() => card.remove(), 300);
        }
    } else {
        // Save Logic
        btn.classList.add('saved');
        btn.innerHTML = '♥';
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