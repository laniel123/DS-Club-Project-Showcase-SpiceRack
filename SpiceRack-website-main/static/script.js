// ── modal ─────────────────────────────────────────────────────────────────────

async function openModal(title) {
    const modal      = document.getElementById('recipe-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalImg   = document.getElementById("modal-image");
    const ingList    = document.getElementById("modal-ingredients");
    const stepList   = document.getElementById("modal-steps");

    modal.style.display = "block";
    modalTitle.innerText = title;
    ingList.innerHTML    = '<li>Loading ingredients...</li>';
    stepList.innerHTML   = '<li>Loading directions...</li>';
    modalImg.style.display = "none";

    try {
        const response = await fetch(`/get_recipe_details/${encodeURIComponent(title)}`);
        const data     = await response.json();
        if (data.error) throw new Error(data.error);
        if (data.image) {
            modalImg.src           = data.image;
            modalImg.style.display = "block";
        }
        ingList.innerHTML  = data.ingredients.map(i => `<li>${i.trim()}</li>`).join('');
        stepList.innerHTML = data.directions.map(d => `<li>${d.trim()}</li>`).join('');
    } catch (error) {
        ingList.innerHTML  = '<li>Could not load ingredients.</li>';
        stepList.innerHTML = '<li>Could not load directions.</li>';
    }
}

function closeModal() {
    document.getElementById('recipe-modal').style.display = "none";
}

document.addEventListener('click', function(event) {
    // open modal only when clicking the title text itself, not buttons inside the card
    if (event.target.classList.contains('recipe-title')) {
        openModal(event.target.getAttribute('data-title'));
    }
    const modal = document.getElementById('recipe-modal');
    if (event.target === modal) closeModal();
});


// ── tab switching ─────────────────────────────────────────────────────────────

function switchTab(tabId, clickedElement) {
    document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");
    document.querySelectorAll('.user-tab').forEach(t => t.classList.remove('active-tab'));
    document.getElementById(tabId).style.display = 'grid';
    clickedElement.classList.add('active-tab');
}


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
