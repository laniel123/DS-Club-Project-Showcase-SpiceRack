// ── modal ─────────────────────────────────────────────────────────────────────

async function openModal(title) {
    const modal = document.getElementById('recipe-modal');
    const img   = document.getElementById('modal-image');
    const ings  = document.getElementById('modal-ingredients');
    const steps = document.getElementById('modal-steps');

    document.getElementById('modal-title').innerText = title;
    ings.innerHTML  = '<li>Loading...</li>';
    steps.innerHTML = '<li>Loading...</li>';
    img.style.display = 'none';
    modal.classList.add('open');

    try {
        const r    = await fetch(`/get_recipe_details/${encodeURIComponent(title)}`);
        const data = await r.json();
        if (data.error) throw new Error(data.error);
        if (data.image) {
            img.src = data.image;
            img.style.display = 'block';
        }
        ings.innerHTML  = data.ingredients.map(i => `<li>${i.trim()}</li>`).join('');
        steps.innerHTML = data.directions.map(d => `<li>${d.trim()}</li>`).join('');
    } catch (e) {
        ings.innerHTML  = '<li>Could not load.</li>';
        steps.innerHTML = '<li>Could not load.</li>';
    }
}

function closeModal() {
    document.getElementById('recipe-modal').classList.remove('open');
}


// ── tabs ──────────────────────────────────────────────────────────────────────

function switchTab(tabId, btn) {
    // 1. Hide all tab content sections
    document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
    
    // 2. Remove 'active' styling from all buttons
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    
    // 3. Show the specific tab requested (e.g., 'tab-recommends')
    const target = document.getElementById(tabId);
    if (target) {
        target.style.display = 'block';
    }
    
    // 4. Set the clicked button to active
    btn.classList.add('active');
}


// ── search ────────────────────────────────────────────────────────────────────

let searchTimer;

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('search-input');
    const searchTabBtn = document.getElementById('search-tab-button');
    
    if (!input) return;

    // Switch to 'Search All' tab automatically when user clicks the search box
    input.addEventListener('focus', () => {
        if (searchTabBtn) {
            switchTab('tab-search-all', searchTabBtn);
        }
    });

    // Database Search Logic
    input.addEventListener('input', function() {
        const query = this.value.trim();
        
        clearTimeout(searchTimer);

        if (query.length < 2) {
            return; // Don't search for single letters
        }

        searchTimer = setTimeout(async () => {
            try {
                // Hits the /api/search route we added to app.py
                const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const recipes = await response.json();
                renderSearchResults(recipes);
            } catch (error) {
                console.error("Search failed:", error);
            }
        }, 400); // Wait for user to stop typing
    });
});

// Helper function to build the cards in the 'Search All' tab
function renderSearchResults(recipes) {
    const grid = document.getElementById('global-search-results');
    if (!grid) return;

    if (recipes.length === 0) {
        grid.innerHTML = '<p class="empty-sub">No recipes found for that search.</p>';
        return;
    }

    grid.innerHTML = recipes.map(r => `
        <article class="recipe-card" data-title="${r.title}" onclick="openModal(this.dataset.title)">
            <div class="card-photo" style="background-image:url('${r.image}')">
                <div class="card-photo-overlay"></div>
                <button class="card-heart ${r.saved ? 'saved' : ''}" 
                        onclick="toggleSave(event, this)" 
                        data-title="${r.title}">
                    ${r.saved ? '♥' : '♡'}
                </button>
            </div>
            <div class="card-body">
                <p class="card-profile">GLOBAL DATABASE</p>
                <h3 class="card-title">${r.title}</h3>
            </div>
        </article>
    `).join('');
}

// Helper function to draw the cards in the Search All tab
function renderSearchResults(recipes) {
    const grid = document.getElementById('global-search-results');
    if (!grid) return;

    if (recipes.length === 0) {
        grid.innerHTML = '<p class="empty-sub">No recipes found in the database.</p>';
        return;
    }

    grid.innerHTML = recipes.map(r => `
        <article class="recipe-card" data-title="${r.title}" onclick="openModal(this.dataset.title)">
            <div class="card-photo" style="background-image:url('${r.image}')">
                <div class="card-photo-overlay"></div>
                <button class="card-heart ${r.saved ? 'saved' : ''}" 
                        onclick="toggleSave(event, this)" 
                        data-title="${r.title}">
                    ${r.saved ? '♥' : '♡'}
                </button>
            </div>
            <div class="card-body">
                <p class="card-profile">GLOBAL DATABASE</p>
                <h3 class="card-title">${r.title}</h3>
            </div>
        </article>
    `).join('');
}

function clearSearch() {
    const input = document.getElementById('search-input');
    if (!input) return;
    input.value = '';
    document.querySelectorAll('#tab-recommends .recipe-card').forEach(c => c.style.display = '');
}

let searchTimer;

document.getElementById('search-input').addEventListener('input', function(e) {
    const query = e.target.value;
    
    // Clear timer on every keystroke
    clearTimeout(searchTimer);

    // Don't search for tiny strings
    if (query.length < 2) return;

    searchTimer = setTimeout(async () => {
        // Switch to search tab automatically when typing starts
        const searchTabBtn = document.querySelector('button[onclick*="tab-search-all"]');
        switchTab('tab-search-all', searchTabBtn);

        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const recipes = await response.json();
        
        const grid = document.getElementById('global-search-results');
        if (recipes.length === 0) {
            grid.innerHTML = '<p class="empty-sub">No recipes found for that search.</p>';
            return;
        }

        grid.innerHTML = recipes.map(r => `
            <article class="recipe-card" data-title="${r.title}" onclick="openModal(this.dataset.title)">
                <div class="card-photo" style="background-image:url('${r.image}')">
                    <button class="card-heart ${r.saved ? 'saved' : ''}" onclick="toggleSave(event, this)" data-title="${r.title}">
                        ${r.saved ? '♥' : '♡'}
                    </button>
                </div>
                <div class="card-body">
                    <p class="card-profile">${r.profile}</p>
                    <h3 class="card-title">${r.title}</h3>
                </div>
            </article>
        `).join('');
    }, 400); // Wait 400ms after last keystroke
});

// ── random ────────────────────────────────────────────────────────────────────

function randomRecipe() {
    const cards = [...document.querySelectorAll('#tab-recommends .recipe-card')]
        .filter(c => c.style.display !== 'none');
    if (!cards.length) return;
    const card  = cards[Math.floor(Math.random() * cards.length)];
    const title = card.querySelector('.card-title').innerText;
    card.style.outline = '3px solid #B96B34';
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    setTimeout(() => card.style.outline = '', 800);
    openModal(title);
}


// ── heart / save ──────────────────────────────────────────────────────────────

function toggleSave(event, btn) {
    event.stopPropagation();
    event.preventDefault();

    const title   = btn.getAttribute('data-title');
    const profile = btn.getAttribute('data-profile');
    const raw     = btn.getAttribute('data-matched');
    const matched = raw && raw.trim() ? JSON.parse(raw) : [];
    const isSaved = btn.classList.contains('saved');

    if (isSaved) {
        btn.classList.remove('saved');
        btn.innerHTML = '♡';
        fetch('/unsave_recipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title })
        });
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
        btn.style.transform = 'scale(1.4)';
        setTimeout(() => btn.style.transform = '', 200);
        fetch('/save_recipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, profile, matched })
        }).then(r => r.json()).then(() => location.reload());
    }
}


// ── barcode ───────────────────────────────────────────────────────────────────

function openBarcodeModal() {
    const m = document.getElementById('barcode-modal');
    m.style.display = 'flex';
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