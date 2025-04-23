/**
 * Attendance management functionality
 * Handles attendance marking, validation, UI interactions, and gamification
 */

document.addEventListener('DOMContentLoaded', function() {
    const attendanceStatusSelects = document.querySelectorAll('.attendance-status-select');
    
    // Attendance marking color coding
    attendanceStatusSelects.forEach(select => {
        // Initial color
        setSelectColor(select);
        
        // Update color on change
        select.addEventListener('change', function() {
            setSelectColor(this);
            updateNoteFieldVisibility(this);
            checkAttendancePercentage();
        });
        
        // Initialize note field visibility
        updateNoteFieldVisibility(select);
    });
    
    // Handle mass attendance actions if present
    const massActionButtons = document.querySelectorAll('.mass-action-btn');
    massActionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const status = this.dataset.status;
            markAllAttendance(status);
        });
    });
    
    // Handle row click to select status
    const attendanceRows = document.querySelectorAll('.attendance-row');
    attendanceRows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't trigger if clicked on select or input
            if (e.target.tagName === 'SELECT' || e.target.tagName === 'INPUT') {
                return;
            }
            
            const select = this.querySelector('.attendance-status-select');
            const currentStatus = select.value;
            
            // Cycle through statuses on click
            switch(currentStatus) {
                case 'present':
                    select.value = 'late';
                    break;
                case 'late':
                    select.value = 'absent';
                    break;
                case 'absent':
                    select.value = 'excused';
                    break;
                case 'excused':
                    select.value = 'present';
                    break;
                default:
                    select.value = 'present';
            }
            
            // Trigger change event
            select.dispatchEvent(new Event('change'));
        });
    });
    
    // Form validation and confirmation
    const attendanceForm = document.querySelector('form');
    if (attendanceForm) {
        attendanceForm.addEventListener('submit', function(e) {
            // Check for any unset attendance values
            const unsetSelects = Array.from(attendanceStatusSelects).filter(select => !select.value);
            
            if (unsetSelects.length > 0) {
                if (!confirm(`${unsetSelects.length} student(s) have no attendance status set. They will be marked as absent. Continue?`)) {
                    e.preventDefault();
                    return false;
                }
                
                // Set unselected values to 'absent'
                unsetSelects.forEach(select => {
                    select.value = 'absent';
                });
            }
            
            return true;
        });
    }
    
    // Date range validator for absence requests
    const fromDateField = document.getElementById('from_date');
    const toDateField = document.getElementById('to_date');
    
    if (fromDateField && toDateField) {
        toDateField.addEventListener('change', function() {
            validateDateRange();
        });
        
        fromDateField.addEventListener('change', function() {
            validateDateRange();
        });
    }
    
    // Check attendance percentage on load
    checkAttendancePercentage();
});

/**
 * Set the background color of a select element based on its selected value
 * @param {HTMLElement} select - The select element
 */
function setSelectColor(select) {
    // Remove any existing classes
    select.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info', 'text-white');
    
    // Add appropriate class based on status
    switch(select.value) {
        case 'present':
            select.classList.add('bg-success', 'text-white');
            break;
        case 'absent':
            select.classList.add('bg-danger', 'text-white');
            break;
        case 'late':
            select.classList.add('bg-warning');
            break;
        case 'excused':
            select.classList.add('bg-info', 'text-white');
            break;
    }
}

/**
 * Show/hide notes field based on attendance status
 * @param {HTMLElement} select - The select element
 */
function updateNoteFieldVisibility(select) {
    const studentId = select.dataset.studentId;
    const notesField = document.querySelector(`input[name="notes_${studentId}"]`);
    
    if (!notesField) return;
    
    // Make notes required for some statuses
    if (select.value === 'excused' || select.value === 'late') {
        notesField.setAttribute('placeholder', 'Please provide a reason...');
        notesField.parentElement.classList.add('notes-highlighted');
    } else {
        notesField.setAttribute('placeholder', 'Optional notes');
        notesField.parentElement.classList.remove('notes-highlighted');
    }
}

/**
 * Mark all students with the same attendance status
 * @param {string} status - The status to set
 */
function markAllAttendance(status) {
    const attendanceStatusSelects = document.querySelectorAll('.attendance-status-select');
    
    attendanceStatusSelects.forEach(select => {
        select.value = status;
        setSelectColor(select);
        updateNoteFieldVisibility(select);
    });
    
    // Show confirmation message
    const massActionMessage = document.getElementById('mass-action-message');
    if (massActionMessage) {
        massActionMessage.textContent = `All students marked as ${status.charAt(0).toUpperCase() + status.slice(1)}`;
        massActionMessage.classList.remove('d-none');
        
        // Hide message after a few seconds
        setTimeout(() => {
            massActionMessage.classList.add('d-none');
        }, 3000);
    }
    
    checkAttendancePercentage();
}

/**
 * Validate date range for absence requests
 */
function validateDateRange() {
    const fromDateField = document.getElementById('from_date');
    const toDateField = document.getElementById('to_date');
    
    if (!fromDateField || !toDateField) return;
    
    const fromDate = new Date(fromDateField.value);
    const toDate = new Date(toDateField.value);
    
    const errorMessage = document.getElementById('date-range-error') || createErrorElement();
    
    if (fromDate > toDate) {
        errorMessage.textContent = 'End date cannot be earlier than start date';
        errorMessage.classList.remove('d-none');
        toDateField.classList.add('is-invalid');
        
        // Disable submit button
        const submitButton = document.querySelector('button[type="submit"]');
        if (submitButton) submitButton.disabled = true;
    } else {
        errorMessage.classList.add('d-none');
        toDateField.classList.remove('is-invalid');
        
        // Enable submit button
        const submitButton = document.querySelector('button[type="submit"]');
        if (submitButton) submitButton.disabled = false;
    }
}

/**
 * Create error message element for date validation
 * @return {HTMLElement} The error message element
 */
function createErrorElement() {
    const toDateField = document.getElementById('to_date');
    const errorMessage = document.createElement('div');
    
    errorMessage.id = 'date-range-error';
    errorMessage.className = 'text-danger mt-1';
    
    toDateField.parentNode.appendChild(errorMessage);
    return errorMessage;
}

document.addEventListener('DOMContentLoaded', function() {
    // ... (existing chart code) ...

    // Highlight holidays
    const holidayCells = document.querySelectorAll('#calendarSection tbody td:nth-child(3):contains("(H")');
    holidayCells.forEach(cell => {
        cell.style.fontWeight = '500';
        cell.style.color = '#dc3545';
    });
});

// Polyfill for :contains
if (!Element.prototype.matches(':contains')) {
    Element.prototype.matches = Element.prototype.matchesSelector || Element.prototype.mozMatchesSelector || Element.prototype.msMatchesSelector || Element.prototype.oMatchesSelector || Element.prototype.webkitMatchesSelector;
}