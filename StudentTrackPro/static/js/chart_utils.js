/**
 * Utility functions for Chart.js
 * Provides helper methods for consistent chart styling and data processing
 */

// Default color schemes for consistent charts across the application
const ChartColors = {
    // Status colors
    present: {
        background: 'rgba(40, 167, 69, 0.7)',
        border: 'rgba(40, 167, 69, 1)'
    },
    late: {
        background: 'rgba(255, 193, 7, 0.7)',
        border: 'rgba(255, 193, 7, 1)'
    },
    absent: {
        background: 'rgba(220, 53, 69, 0.7)',
        border: 'rgba(220, 53, 69, 1)'
    },
    excused: {
        background: 'rgba(23, 162, 184, 0.7)',
        border: 'rgba(23, 162, 184, 1)'
    },
    
    // Chart default colors
    default: [
        { background: 'rgba(40, 167, 69, 0.7)', border: 'rgba(40, 167, 69, 1)' },
        { background: 'rgba(23, 162, 184, 0.7)', border: 'rgba(23, 162, 184, 1)' },
        { background: 'rgba(255, 193, 7, 0.7)', border: 'rgba(255, 193, 7, 1)' },
        { background: 'rgba(220, 53, 69, 0.7)', border: 'rgba(220, 53, 69, 1)' },
        { background: 'rgba(111, 66, 193, 0.7)', border: 'rgba(111, 66, 193, 1)' },
        { background: 'rgba(248, 108, 107, 0.7)', border: 'rgba(248, 108, 107, 1)' }
    ]
};

/**
 * Get color based on attendance percentage and threshold
 * @param {number} percentage - The attendance percentage
 * @param {number} threshold - The minimum required percentage
 * @return {Object} Object containing background and border colors
 */
function getColorByPercentage(percentage, threshold) {
    if (percentage < 60) {
        return {
            background: 'rgba(220, 53, 69, 0.7)', // Danger - red
            border: 'rgba(220, 53, 69, 1)'
        };
    } else if (percentage < threshold) {
        return {
            background: 'rgba(255, 193, 7, 0.7)', // Warning - yellow
            border: 'rgba(255, 193, 7, 1)'
        };
    } else {
        return {
            background: 'rgba(40, 167, 69, 0.7)', // Success - green
            border: 'rgba(40, 167, 69, 1)'
        };
    }
}

/**
 * Format date strings for display in charts
 * @param {string} dateString - Date string in YYYY-MM-DD format
 * @param {string} format - Optional format ('short', 'medium', 'long')
 * @return {string} Formatted date string
 */
function formatChartDate(dateString, format = 'short') {
    const date = new Date(dateString);
    
    switch(format) {
        case 'short':
            return `${date.getMonth() + 1}/${date.getDate()}`;
        case 'medium':
            return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear().toString().substr(-2)}`;
        case 'long':
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
            });
        default:
            return dateString;
    }
}

/**
 * Calculate average from an array of numbers
 * @param {Array} values - Array of numbers
 * @return {number} Average value
 */
function calculateAverage(values) {
    if (!values || values.length === 0) return 0;
    const sum = values.reduce((a, b) => a + b, 0);
    return sum / values.length;
}

/**
 * Convert a status string to a numeric value for charts
 * @param {string} status - Status string ('present', 'late', 'absent', 'excused')
 * @return {number} Numeric value representing the status
 */
function statusToValue(status) {
    switch(status) {
        case 'present': return 1;
        case 'late': return 0.5;
        case 'excused': return 0.75;
        case 'absent': return 0;
        default: return null;
    }
}

/**
 * Convert a numeric value to a status string
 * @param {number} value - Numeric value
 * @return {string} Status string
 */
function valueToStatus(value) {
    if (value === 1) return 'Present';
    if (value === 0.5) return 'Late';
    if (value === 0.75) return 'Excused';
    if (value === 0) return 'Absent';
    return 'Unknown';
}

/**
 * Get default chart options for consistent styling
 * @param {string} type - Chart type ('bar', 'line', 'pie', etc.)
 * @return {Object} Default chart options
 */
function getDefaultChartOptions(type) {
    const baseOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                position: 'bottom'
            }
        }
    };
    
    switch(type) {
        case 'bar':
            return {
                ...baseOptions,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            };
        case 'line':
            return {
                ...baseOptions,
                elements: {
                    line: {
                        tension: 0.1
                    }
                }
            };
        case 'pie':
        case 'doughnut':
            return {
                ...baseOptions,
                plugins: {
                    ...baseOptions.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const value = context.raw;
                                const percentage = Math.round((value / total) * 100);
                                return `${context.label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            };
        default:
            return baseOptions;
    }
}
