document.addEventListener('DOMContentLoaded', function() {
    // Find the image field and the image_position field
    const imageFieldContainer = document.querySelector('.field-image');
    const positionFieldContainer = document.querySelector('.field-image_position');
    const positionInput = document.getElementById('id_image_position');

    if (!imageFieldContainer || !positionInput) {
        return;
    }

    // Try to find an existing uploaded image URL
    const imageLink = imageFieldContainer.querySelector('p.file-upload a') || imageFieldContainer.querySelector('a');
    if (!imageLink || !imageLink.href) {
        // No image uploaded yet, show a placeholder or nothing
        return;
    }

    const imageUrl = imageLink.href;

    // Create the visual picker elements
    const pickerWrapper = document.createElement('div');
    pickerWrapper.className = 'focal-point-picker-wrapper';
    pickerWrapper.innerHTML = `
        <div class="focal-point-picker-title">Main Image Focal Point Grid</div>
        <div class="focal-point-picker-subtitle">Click anywhere on the image below to set the visual focal point (represented by the square). This controls what part of your pottery is centered and visible on the archive card pages.</div>
        <div class="focal-point-container">
            <img class="focal-point-preview" src="${imageUrl}" alt="Focal preview" />
            <div class="focal-point-grid-lines">
                <div class="grid-line vertical line-1"></div>
                <div class="grid-line vertical line-2"></div>
                <div class="grid-line horizontal line-1"></div>
                <div class="grid-line horizontal line-2"></div>
            </div>
            <div class="focal-point-reticle"></div>
        </div>
        <div class="focal-point-value-display">Selected Position: <span class="coordinate-val">50% 50%</span></div>
    `;

    // Append to the position field container
    positionFieldContainer.appendChild(pickerWrapper);

    const container = pickerWrapper.querySelector('.focal-point-container');
    const reticle = pickerWrapper.querySelector('.focal-point-reticle');
    const coordinateDisplay = pickerWrapper.querySelector('.coordinate-val');

    // Function to update coordinates
    function updateFocalPoint(xPct, yPct) {
        positionInput.value = `${xPct}% ${yPct}%`;
        coordinateDisplay.textContent = `${xPct}% ${yPct}%`;
        reticle.style.left = `${xPct}%`;
        reticle.style.top = `${yPct}%`;
    }

    // Initialize position based on existing value
    function initPosition() {
        const val = positionInput.value.trim();
        const match = val.match(/^(\d+)%\s+(\d+)%$/);
        if (match) {
            updateFocalPoint(parseInt(match[1]), parseInt(match[2]));
        } else {
            // Default to center center
            updateFocalPoint(50, 50);
        }
    }

    // Handle clicks on the container
    container.addEventListener('click', function(e) {
        const rect = container.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;

        const xPct = Math.round(Math.max(0, Math.min(100, x)));
        const yPct = Math.round(Math.max(0, Math.min(100, y)));

        updateFocalPoint(xPct, yPct);
    });

    // Make reticle draggable or click-draggable
    let isDragging = false;

    function handleMove(clientX, clientY) {
        const rect = container.getBoundingClientRect();
        const x = ((clientX - rect.left) / rect.width) * 100;
        const y = ((clientY - rect.top) / rect.height) * 100;

        const xPct = Math.round(Math.max(0, Math.min(100, x)));
        const yPct = Math.round(Math.max(0, Math.min(100, y)));

        updateFocalPoint(xPct, yPct);
    }

    container.addEventListener('mousedown', function(e) {
        isDragging = true;
        handleMove(e.clientX, e.clientY);
        e.preventDefault();
    });

    document.addEventListener('mousemove', function(e) {
        if (isDragging) {
            handleMove(e.clientX, e.clientY);
        }
    });

    document.addEventListener('mouseup', function() {
        isDragging = false;
    });

    // Run initializer
    initPosition();
});
