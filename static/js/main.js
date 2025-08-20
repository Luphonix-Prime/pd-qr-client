// Main JavaScript file for TrustTags application

document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar toggle
    initializeSidebarToggle();

    // Initialize DataTables
    initializeDataTables();

    // Initialize tooltips
    initializeTooltips();

    // Initialize form validation
    initializeFormValidation();

    // Initialize search functionality
    initializeSearch();

    // Initialize animations
    initializeAnimations();
});

/**
 * Initialize sidebar toggle functionality
 */
function initializeSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');

    if (sidebarToggle && sidebar && mainContent) {
        sidebarToggle.addEventListener('click', function() {
            // Toggle sidebar visibility
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');

            // Store sidebar state in localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
        });

        // Restore sidebar state from localStorage
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('expanded');
        }
    }

    // Handle mobile sidebar toggle
    const mobileToggle = document.querySelector('[data-bs-toggle="collapse"]');
    if (mobileToggle && window.innerWidth <= 768) {
        mobileToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
}

/**
 * Initialize DataTables for enhanced table functionality
 */
function initializeDataTables() {
    // Check if DataTables is loaded
    if (typeof $.fn.DataTable !== 'undefined') {
        // Initialize DataTables on tables with specific classes
        $('.data-table').each(function() {
            if (!$.fn.DataTable.isDataTable(this)) {
                $(this).DataTable({
                    responsive: true,
                    pageLength: 10,
                    lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
                    language: {
                        search: "Search:",
                        lengthMenu: "Show _MENU_ entries",
                        info: "Showing _START_ to _END_ of _TOTAL_ entries",
                        paginate: {
                            previous: "Previous",
                            next: "Next"
                        }
                    },
                    dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>rtip',
                    columnDefs: [
                        { orderable: false, targets: 'no-sort' }
                    ]
                });
            }
        });
    }
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize tooltips for buttons with title attributes
    const titleButtons = document.querySelectorAll('button[title], a[title]');
    titleButtons.forEach(function(button) {
        if (!button.hasAttribute('data-bs-toggle')) {
            button.setAttribute('data-bs-toggle', 'tooltip');
            new bootstrap.Tooltip(button);
        }
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    // Custom form validation
    const forms = document.querySelectorAll('.needs-validation');

    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Real-time validation for required fields
    const requiredFields = document.querySelectorAll('input[required], select[required], textarea[required]');
    requiredFields.forEach(function(field) {
        field.addEventListener('blur', function() {
            validateField(field);
        });

        field.addEventListener('input', function() {
            if (field.classList.contains('is-invalid')) {
                validateField(field);
            }
        });
    });
}

/**
 * Validate individual form field
 */
function validateField(field) {
    const isValid = field.checkValidity();

    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
    }

    return isValid;
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    // Global search functionality for tables
    const searchInputs = document.querySelectorAll('input[placeholder*="Search"]');

    searchInputs.forEach(function(searchInput) {
        const targetTable = searchInput.closest('.card').querySelector('table');

        if (targetTable) {
            searchInput.addEventListener('input', debounce(function() {
                performTableSearch(searchInput.value, targetTable);
            }, 300));
        }
    });
}

/**
 * Perform table search
 */
function performTableSearch(searchTerm, table) {
    const rows = table.querySelectorAll('tbody tr');
    const term = searchTerm.toLowerCase().trim();

    rows.forEach(function(row) {
        const text = row.textContent.toLowerCase();
        const shouldShow = text.includes(term);

        row.style.display = shouldShow ? '' : 'none';

        // Add highlighting
        if (shouldShow && term) {
            highlightSearchTerm(row, term);
        } else {
            removeHighlight(row);
        }
    });

    // Update "no results" message
    updateNoResultsMessage(table, term);
}

/**
 * Highlight search terms in table rows
 */
function highlightSearchTerm(row, term) {
    // Remove existing highlights
    removeHighlight(row);

    if (!term) return;

    const cells = row.querySelectorAll('td');
    cells.forEach(function(cell) {
        const text = cell.textContent;
        if (text.toLowerCase().includes(term)) {
            const regex = new RegExp(`(${escapeRegExp(term)})`, 'gi');
            cell.innerHTML = cell.innerHTML.replace(regex, '<mark class="bg-warning">$1</mark>');
        }
    });
}

/**
 * Remove search highlighting
 */
function removeHighlight(row) {
    const marks = row.querySelectorAll('mark.bg-warning');
    marks.forEach(function(mark) {
        mark.outerHTML = mark.innerHTML;
    });
}

/**
 * Update no results message
 */
function updateNoResultsMessage(table, searchTerm) {
    const tbody = table.querySelector('tbody');
    const visibleRows = tbody.querySelectorAll('tr[style=""], tr:not([style])');
    let noResultsRow = tbody.querySelector('.no-results-row');

    if (visibleRows.length === 0 && searchTerm) {
        if (!noResultsRow) {
            const colCount = table.querySelectorAll('thead th').length;
            noResultsRow = document.createElement('tr');
            noResultsRow.className = 'no-results-row';
            noResultsRow.innerHTML = `
                <td colspan="${colCount}" class="text-center py-4">
                    <i class="fas fa-search fa-2x text-muted mb-2"></i>
                    <p class="text-muted mb-0">No results found for "${searchTerm}"</p>
                </td>
            `;
            tbody.appendChild(noResultsRow);
        }
    } else if (noResultsRow) {
        noResultsRow.remove();
    }
}

/**
 * Initialize animations
 */
function initializeAnimations() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(function(card, index) {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in-up');
    });

    // Add hover effects to interactive elements
    addHoverEffects();
}

/**
 * Add hover effects to interactive elements
 */
function addHoverEffects() {
    // Stat cards hover effect
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach(function(card) {
        card.addEventListener('mouseenter', function() {
            card.style.transform = 'translateY(-5px)';
        });

        card.addEventListener('mouseleave', function() {
            card.style.transform = 'translateY(0)';
        });
    });

    // Button hover effects
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(function(button) {
        button.addEventListener('mouseenter', function() {
            if (!button.disabled) {
                button.style.transform = 'translateY(-1px)';
            }
        });

        button.addEventListener('mouseleave', function() {
            button.style.transform = 'translateY(0)';
        });
    });
}

/**
 * Utility function to debounce function calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Escape special characters for regex
 */
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Show loading state
 */
function showLoading(element) {
    const loadingHTML = `
        <div class="d-flex justify-content-center align-items-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span class="ms-2">Loading...</span>
        </div>
    `;

    if (element) {
        element.innerHTML = loadingHTML;
    }
}

/**
 * Hide loading state
 */
function hideLoading(element, originalContent) {
    if (element && originalContent) {
        element.innerHTML = originalContent;
    }
}

/**
 * Show success message
 */
function showSuccessMessage(message, duration = 5000) {
    showAlert(message, 'success', duration);
}

/**
 * Show error message
 */
function showErrorMessage(message, duration = 5000) {
    showAlert(message, 'danger', duration);
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info', duration = 5000) {
    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    // Find or create alert container
    let alertContainer = document.querySelector('.alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.className = 'alert-container';
        alertContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
        `;
        document.body.appendChild(alertContainer);
    }

    // Add alert
    const alertElement = document.createElement('div');
    alertElement.innerHTML = alertHTML;
    alertContainer.appendChild(alertElement.firstElementChild);

    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            const alert = alertContainer.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, duration);
    }
}

/**
 * Format date for display
 */
function formatDate(date, format = 'DD-MM-YYYY') {
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();

    switch (format) {
        case 'DD-MM-YYYY':
            return `${day}-${month}-${year}`;
        case 'MM-DD-YYYY':
            return `${month}-${day}-${year}`;
        case 'YYYY-MM-DD':
            return `${year}-${month}-${day}`;
        default:
            return d.toLocaleDateString();
    }
}

/**
 * Format number with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showSuccessMessage('Copied to clipboard!');
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

/**
 * Fallback copy to clipboard for older browsers
 */
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        showSuccessMessage('Copied to clipboard!');
    } catch (err) {
        showErrorMessage('Failed to copy to clipboard');
    }

    document.body.removeChild(textArea);
}

/**
 * Download file from URL
 */
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || 'download';
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Confirm action with modal
 */
function confirmAction(message, callback, title = 'Confirm Action') {
    const modalHTML = `
        <div class="modal fade" id="confirmModal" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="confirmBtn">Confirm</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal
    const existingModal = document.getElementById('confirmModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
    modal.show();

    // Handle confirm button
    document.getElementById('confirmBtn').addEventListener('click', () => {
        modal.hide();
        if (typeof callback === 'function') {
            callback();
        }
    });

    // Clean up on hide
    document.getElementById('confirmModal').addEventListener('hidden.bs.modal', () => {
        document.getElementById('confirmModal').remove();
    });
}

// Export functions for global use
window.TrustTags = {
    showSuccessMessage,
    showErrorMessage,
    showAlert,
    showLoading,
    hideLoading,
    formatDate,
    formatNumber,
    copyToClipboard,
    downloadFile,
    confirmAction,
    debounce
};

// Add QR Code generation and display functions
$(document).ready(function() {
    // Product selection change event
    $('#productSelect').change(function() {
        var productId = $(this).val();
        var batchSelect = $('#batchSelect');

        // Clear batch options
        batchSelect.empty().append('<option value="">-- Select --</option>');

        if (productId) {
            // Fetch batches for selected product
            $.get('/api/batches/' + productId, function(data) {
                $.each(data, function(index, batch) {
                    batchSelect.append('<option value="' + batch.id + '">' + 
                                     batch.batch_no + ' (MFG: ' + batch.mfg_date + 
                                     ', EXP: ' + batch.expiry_date + ')</option>');
                });
            });
        }
    });

    // Auto-generate batch number
    $('.generate-batch-btn').click(function() {
        var today = new Date();
        var batchNo = 'BATCH' + today.getFullYear() + 
                     String(today.getMonth() + 1).padStart(2, '0') + 
                     String(today.getDate()).padStart(2, '0') + 
                     Math.random().toString(36).substr(2, 6).toUpperCase();
        $('#batchNo').val(batchNo);
    });

    // QR Code display function
    window.showQRCode = function(codeType, codeId) {
        $.get('/show-qr/' + codeType + '/' + codeId, function(data) {
            $('#qrCodeContainer').html('<img src="' + data.qr_image + '" class="img-fluid" style="max-width: 300px;">');
            $('#qrCodeData').text(data.qr_data);
            $('#qrCodeModal').modal('show');
        }).fail(function() {
            alert('Error loading QR code');
        });
    };
});