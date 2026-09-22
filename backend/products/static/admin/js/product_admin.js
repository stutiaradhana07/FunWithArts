/**
 * Fun With Art - Product Admin Interactive UX Enhancements
 * Enhances Django Admin's native changelist formset without overriding native save logic.
 */
document.addEventListener('DOMContentLoaded', function () {
    const changelistForm = document.getElementById('changelist-form');
    if (!changelistForm) return;

    // Read low stock threshold from data attribute or fallback to 5
    const kpiBar = document.querySelector('.product-admin-kpi-bar');
    const threshold = kpiBar && kpiBar.dataset.threshold ? parseInt(kpiBar.dataset.threshold, 10) : 5;

    const modifiedInputs = new Set();
    const initialValues = new Map();
    let isSubmitting = false;

    // Create sticky save changes bar if not present in DOM
    let stickyBar = document.getElementById('product-sticky-save-bar');
    if (!stickyBar) {
        stickyBar = document.createElement('div');
        stickyBar.id = 'product-sticky-save-bar';
        stickyBar.className = 'product-sticky-save-bar';
        stickyBar.innerHTML = `
            <div class="unsaved-info">
                <span class="pulse-dot"></span>
                <span id="unsaved-count-text"><strong>0</strong> unsaved changes</span>
            </div>
            <input type="submit" name="_save" class="default sticky-save-btn" value="💾 Save Changes" form="changelist-form">
        `;
        document.body.appendChild(stickyBar);
    }

    const unsavedText = document.getElementById('unsaved-count-text');

    // 1. Highlight rows with server-side validation errors
    const errorLists = changelistForm.querySelectorAll('ul.errorlist');
    errorLists.forEach(function (errorList) {
        const row = errorList.closest('tr');
        if (row) {
            row.classList.add('row-has-error');
        }
    });

    // 2. Track initial values of editable fields
    const editableInputs = changelistForm.querySelectorAll('input[name^="form-"], select[name^="form-"]');
    editableInputs.forEach(function (input) {
        const inputKey = input.name;
        if (input.type === 'checkbox') {
            initialValues.set(inputKey, input.checked);
        } else {
            initialValues.set(inputKey, input.value);
        }

        // Listen for input and change events
        input.addEventListener('input', function () {
            handleFieldChange(input);
        });
        input.addEventListener('change', function () {
            handleFieldChange(input);
        });
    });

    function handleFieldChange(input) {
        const inputKey = input.name;
        const initialVal = initialValues.get(inputKey);
        const currentVal = input.type === 'checkbox' ? input.checked : input.value;
        const row = input.closest('tr');

        if (currentVal !== initialVal) {
            modifiedInputs.add(inputKey);
            if (row) row.classList.add('row-modified');
        } else {
            modifiedInputs.delete(inputKey);
            // Check if any other input in the same row is modified
            if (row) {
                const otherModifiedInRow = Array.from(row.querySelectorAll('input[name^="form-"], select[name^="form-"]')).some(
                    (other) => modifiedInputs.has(other.name)
                );
                if (!otherModifiedInRow) {
                    row.classList.remove('row-modified');
                }
            }
        }

        // Handle live visual update of stock badges
        if (input.name.endsWith('-stock')) {
            updateLiveStockBadge(input);
        }

        updateStickyBar();
    }

    function updateLiveStockBadge(stockInput) {
        const row = stockInput.closest('tr');
        if (!row) return;

        const badge = row.querySelector('.stock-badge');
        if (!badge) return;

        const val = parseInt(stockInput.value, 10);

        badge.classList.remove('badge-in-stock', 'badge-low-stock', 'badge-out-of-stock');

        if (isNaN(val) || val <= 0) {
            badge.classList.add('badge-out-of-stock');
            badge.textContent = '✖ Out of Stock';
        } else if (val <= threshold) {
            badge.classList.add('badge-low-stock');
            badge.textContent = `⚠ Low Stock (${val})`;
        } else {
            badge.classList.add('badge-in-stock');
            badge.textContent = `● In Stock (${val})`;
        }
    }

    function updateStickyBar() {
        const count = modifiedInputs.size;
        if (count > 0) {
            stickyBar.classList.add('has-unsaved-changes');
            if (unsavedText) {
                unsavedText.innerHTML = `<strong>${count}</strong> unsaved change${count > 1 ? 's' : ''}`;
            }
        } else {
            stickyBar.classList.remove('has-unsaved-changes');
        }
    }

    // 3. Prevent leaving page with unsaved changes
    window.addEventListener('beforeunload', function (e) {
        if (!isSubmitting && modifiedInputs.size > 0) {
            e.preventDefault();
            e.returnValue = 'You have unsaved product changes. Are you sure you want to leave?';
            return e.returnValue;
        }
    });

    // 4. Bypass beforeunload on submit
    changelistForm.addEventListener('submit', function () {
        isSubmitting = true;
    });

    document.querySelectorAll('input[type="submit"]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            isSubmitting = true;
        });
    });
});
