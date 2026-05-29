document.addEventListener('DOMContentLoaded', function() {
    // Find the image field, the image_position and image_zoom containers/inputs
    const imageFieldContainer = document.querySelector('.field-image');
    const positionFieldContainer = document.querySelector('.field-image_position');
    const zoomFieldContainer = document.querySelector('.field-image_zoom');
    
    const positionInput = document.getElementById('id_image_position');
    const zoomInput = document.getElementById('id_image_zoom');
    const fileInput = document.getElementById('id_image');

    if (!imageFieldContainer || !positionInput) {
        return;
    }

    // Hide original inputs to keep Django Admin extremely clean
    if (positionInput) {
        positionInput.style.display = 'inline-block';
        positionInput.style.width = '100px';
        positionInput.style.marginRight = '10px';
        positionInput.setAttribute('readonly', 'true');
    }
    if (zoomInput) {
        zoomInput.style.display = 'inline-block';
        zoomInput.style.width = '70px';
        zoomInput.setAttribute('readonly', 'true');
    }

    let currentObjectUrl = null;
    let pickerWrapper = null;
    let cropImg = null;
    let zoomSlider = null;
    let zoomDisplay = null;
    let posDisplay = null;
    let container = null;

    let isDragging = false;
    let startX = 0;
    let startY = 0;
    let startPctX = 50;
    let startPctY = 50;

    // Helper to update coordinates and scale in the DOM and Inputs
    function updateCropState(pctX, pctY, zoomVal) {
        // Round to nearest integer for percentage, and 2 decimal places for zoom
        pctX = Math.round(Math.max(0, Math.min(100, pctX)));
        pctY = Math.round(Math.max(0, Math.min(100, pctY)));
        zoomVal = parseFloat(Math.max(1.0, Math.min(3.0, zoomVal))).toFixed(2);

        // Update raw hidden inputs
        if (positionInput) positionInput.value = `${pctX}% ${pctY}%`;
        if (zoomInput) zoomInput.value = zoomVal;

        // Update preview styles
        if (cropImg) {
            cropImg.style.objectPosition = `${pctX}% ${pctY}%`;
            cropImg.style.transform = `scale(${zoomVal})`;
        }

        // Update visual labels
        if (zoomDisplay) zoomDisplay.textContent = `${zoomVal}x`;
        if (posDisplay) posDisplay.textContent = `${pctX}% ${pctY}%`;
        if (zoomSlider) zoomSlider.value = zoomVal;
    }

    // Initialize state from existing database values
    function initCropState() {
        let pctX = 50;
        let pctY = 50;
        let zoomVal = 1.0;

        if (positionInput && positionInput.value) {
            const match = positionInput.value.trim().match(/^(\d+)%\s+(\d+)%$/);
            if (match) {
                pctX = parseInt(match[1]);
                pctY = parseInt(match[2]);
            }
        }

        if (zoomInput && zoomInput.value) {
            const floatVal = parseFloat(zoomInput.value);
            if (!isNaN(floatVal)) {
                zoomVal = floatVal;
            }
        }

        updateCropState(pctX, pctY, zoomVal);
    }

    // Function to render or update the crop preview grid widget
    function renderCropEditor(imageUrl) {
        if (!pickerWrapper) {
            pickerWrapper = document.createElement('div');
            pickerWrapper.className = 'focal-point-picker-wrapper';
            pickerWrapper.innerHTML = `
                <div class="focal-point-picker-title">Main Image Crop & Zoom Editor</div>
                <div class="focal-point-picker-subtitle">Drag the image inside the crop window below to center it. Use the slider to zoom in/out. This matches exactly how your piece will be cropped on the Archive page.</div>
                
                <div class="crop-box-container">
                    <img class="crop-preview-image" src="${imageUrl}" alt="Crop preview" />
                    <div class="crop-grid-overlay">
                        <div class="grid-line vertical line-1"></div>
                        <div class="grid-line vertical line-2"></div>
                        <div class="grid-line horizontal line-1"></div>
                        <div class="grid-line horizontal line-2"></div>
                    </div>
                </div>

                <div class="zoom-controls-row">
                    <span class="zoom-icon">🔍⁻</span>
                    <input type="range" class="crop-zoom-slider" min="1.00" max="3.00" step="0.05" value="1.00">
                    <span class="zoom-icon">🔍⁺</span>
                </div>

                <div class="crop-info-row">
                    <span class="info-label">Zoom: <span class="info-value zoom-val">1.00x</span></span>
                    <span class="info-label">Focal Point: <span class="info-value pos-val">50% 50%</span></span>
                </div>
            `;

            // Append to the position field container
            positionFieldContainer.appendChild(pickerWrapper);

            // Keep references
            container = pickerWrapper.querySelector('.crop-box-container');
            cropImg = pickerWrapper.querySelector('.crop-preview-image');
            zoomSlider = pickerWrapper.querySelector('.crop-zoom-slider');
            zoomDisplay = pickerWrapper.querySelector('.zoom-val');
            posDisplay = pickerWrapper.querySelector('.pos-val');

            // --- 1. DRAGGING / PANNING LOGIC ---
            container.addEventListener('mousedown', function(e) {
                isDragging = true;
                startX = e.clientX;
                startY = e.clientY;

                // Parse current coordinates
                let currentPctX = 50;
                let currentPctY = 50;
                if (positionInput && positionInput.value) {
                    const match = positionInput.value.trim().match(/^(\d+)%\s+(\d+)%$/);
                    if (match) {
                        currentPctX = parseInt(match[1]);
                        currentPctY = parseInt(match[2]);
                    }
                }
                startPctX = currentPctX;
                startPctY = currentPctY;

                e.preventDefault();
            });

            document.addEventListener('mousemove', function(e) {
                if (!isDragging) return;

                const dx = e.clientX - startX;
                const dy = e.clientY - startY;

                const rect = container.getBoundingClientRect();
                const currentZoom = parseFloat(zoomSlider.value) || 1.0;

                // Sensitivity adjusts with zoom to make panning extremely precise and intuitive
                const sensitivityX = (100 / rect.width) * (0.35 / currentZoom);
                const sensitivityY = (100 / rect.height) * (0.35 / currentZoom);

                // Calculate panned percentages (inverted because drag direction shifts focal point opposite)
                const newPctX = startPctX - (dx * sensitivityX);
                const newPctY = startPctY - (dy * sensitivityY);

                updateCropState(newPctX, newPctY, currentZoom);
            });

            document.addEventListener('mouseup', function() {
                isDragging = false;
            });

            // --- 2. ZOOM SLIDER LOGIC ---
            zoomSlider.addEventListener('input', function() {
                // Read current position
                let currentPctX = 50;
                let currentPctY = 50;
                if (positionInput && positionInput.value) {
                    const match = positionInput.value.trim().match(/^(\d+)%\s+(\d+)%$/);
                    if (match) {
                        currentPctX = parseInt(match[1]);
                        currentPctY = parseInt(match[2]);
                    }
                }
                updateCropState(currentPctX, currentPctY, parseFloat(this.value));
            });

        } else {
            // Update preview image src if already rendered
            const previewImg = pickerWrapper.querySelector('.crop-preview-image');
            if (previewImg) {
                previewImg.src = imageUrl;
            }
        }

        // Initialize state from existing settings
        initCropState();
    }

    // 1. Initialize using existing image if present on load
    const imageLink = imageFieldContainer.querySelector('p.file-upload a') || imageFieldContainer.querySelector('a');
    if (imageLink && imageLink.href) {
        renderCropEditor(imageLink.href);
    }

    // 2. Listen for file input changes to show crop grid instantly for newly selected files
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                // Free memory from any previous object URL
                if (currentObjectUrl) {
                    URL.revokeObjectURL(currentObjectUrl);
                }
                currentObjectUrl = URL.createObjectURL(file);
                renderCropEditor(currentObjectUrl);
            }
        });
    }
});
