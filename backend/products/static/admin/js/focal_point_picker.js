document.addEventListener('DOMContentLoaded', function() {
    // Find the image field, the image_position field, and the input elements
    const imageFieldContainer = document.querySelector('.field-image');
    const positionFieldContainer = document.querySelector('.field-image_position');
    const positionInput = document.getElementById('id_image_position');
    const fileInput = document.getElementById('id_image');

    if (!imageFieldContainer || !positionInput) {
        return;
    }

    let currentObjectUrl = null;
    let pickerWrapper = null;
    let reticle = null;
    let coordinateDisplay = null;
    let container = null;
    let isDragging = false;

    // Helper to update coordinate display and reticle position
    function updateFocalPoint(xPct, yPct) {
        positionInput.value = `${xPct}% ${yPct}%`;
        if (coordinateDisplay) {
            coordinateDisplay.textContent = `${xPct}% ${yPct}%`;
        }
        if (reticle) {
            reticle.style.left = `${xPct}%`;
            reticle.style.top = `${yPct}%`;
        }
    }

    // Initialize position based on input field value
    function initPosition() {
        const val = positionInput.value.trim();
        const match = val.match(/^(\d+)%\s+(\d+)%$/);
        if (match) {
            updateFocalPoint(parseInt(match[1]), parseInt(match[2]));
        } else {
            updateFocalPoint(50, 50); // Default to center
        }
    }

    // Function to render or update the focal point grid picker
    function showGrid(imageUrl) {
        if (!pickerWrapper) {
            // Create the visual picker elements if they don't exist
            pickerWrapper = document.createElement('div');
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

            // Fetch references to inner elements
            container = pickerWrapper.querySelector('.focal-point-container');
            reticle = pickerWrapper.querySelector('.focal-point-reticle');
            coordinateDisplay = pickerWrapper.querySelector('.coordinate-val');

            // Handle clicks on the container to position focal point
            container.addEventListener('click', function(e) {
                const rect = container.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;

                const xPct = Math.round(Math.max(0, Math.min(100, x)));
                const yPct = Math.round(Math.max(0, Math.min(100, y)));

                updateFocalPoint(xPct, yPct);
            });

            // Make focal point draggable
            function handleMove(clientX, clientY) {
                if (!container) return;
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
        } else {
            // Update preview image src if the grid picker is already rendered
            const previewImg = pickerWrapper.querySelector('.focal-point-preview');
            if (previewImg) {
                previewImg.src = imageUrl;
            }
        }

        // Initialize reticle position based on existing values
        initPosition();
    }

    // 1. Initialize using existing image if present on load
    const imageLink = imageFieldContainer.querySelector('p.file-upload a') || imageFieldContainer.querySelector('a');
    if (imageLink && imageLink.href) {
        showGrid(imageLink.href);
    }

    // 2. Listen for file input changes to show grid instantly for newly selected files
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                // Free memory from any previous object URL
                if (currentObjectUrl) {
                    URL.revokeObjectURL(currentObjectUrl);
                }
                currentObjectUrl = URL.createObjectURL(file);
                showGrid(currentObjectUrl);
            }
        });
    }
});
