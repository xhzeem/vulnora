// VulnerableShop - Frontend JavaScript

// Close alert messages
document.addEventListener('DOMContentLoaded', function () {
    const closeButtons = document.querySelectorAll('.close-alert');
    closeButtons.forEach(button => {
        button.addEventListener('click', function () {
            this.parentElement.style.display = 'none';
        });
    });
});

// Auto-hide alerts after 5 seconds
setTimeout(function () {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        alert.style.transition = 'opacity 0.5s';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 500);
    });
}, 5000);

// Form validation (client-side - easily bypassable)
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;

    const inputs = form.querySelectorAll('input[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.style.borderColor = 'var(--danger-color)';
        } else {
            input.style.borderColor = 'var(--border-color)';
        }
    });

    return isValid;
}

// Cart quantity update
function updateCartQuantity(cartId, quantity) {
    // INSECURE: Client-side validation that can be bypassed
    if (quantity < 1) {
        console.log('Quantity must be at least 1');
        return false;
    }

    // Note: No maximum quantity check - could order more than available stock
    return true;
}

// Price manipulation helper (for educational purposes)
function manipulatePrice() {
    const priceField = document.getElementById('total_amount');
    if (priceField) {
        console.log('Current price:', priceField.value);
        console.log('You can change this value in the browser developer tools!');
    }
}

// XSS testing helper
function testXSS(payload) {
}

// SQL Injection helper
function sqlInjectionHint() {
    console.log('Login bypass: admin\' OR \'1\'=\'1\'-- ');
}

// SSTI Testing
function sstiHint() {
    console.log('Basic test: {{ 7*7 }}');
    console.log('Config access: {{ config }}');
    console.log('RCE: {{ config.__class__.__init__.__globals__[\'os\'].popen(\'ls\').read() }}');
}

// Log vulnerability hints to console for educational purposes
console.log('%c🚨 VulnerableShop - Educational Security Platform', 'color: #f56565; font-size: 20px; font-weight: bold;');
console.log('%c⚠️  This application is INTENTIONALLY VULNERABLE', 'color: #ed8936; font-size: 14px; font-weight: bold;');
console.log('1. SQL Injection in login form');
console.log('4. IDOR in order pages');
console.log('5. Price manipulation in checkout');
console.log('6. CSRF in profile updates');
console.log('7. SSRF in admin health check');
console.log('8. Command injection in admin backup');
console.log('\nType sqlInjectionHint() or sstiHint() for more help!');

// Make helper functions available globally
window.manipulatePrice = manipulatePrice;
window.testXSS = testXSS;
window.sqlInjectionHint = sqlInjectionHint;
window.sstiHint = sstiHint;
