// Form Validation
document.addEventListener('DOMContentLoaded', function() {
    // Get all forms with validation
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(form)) {
                event.preventDefault();
            }
        });
    });

    // Quantity Input Handlers
    const quantityInputs = document.querySelectorAll('input[type="number"]');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const min = parseInt(this.getAttribute('min')) || 1;
            const max = parseInt(this.getAttribute('max')) || 99;
            
            if (this.value < min) this.value = min;
            if (this.value > max) this.value = max;
        });
    });

    // Password Confirmation
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        if (input.id === 'confirm_password') {
            input.addEventListener('input', function() {
                const password = document.getElementById('password');
                if (this.value !== password.value) {
                    this.setCustomValidity('Passwords do not match');
                } else {
                    this.setCustomValidity('');
                }
            });
        }
    });

    // Card Number Formatting
    const cardInput = document.getElementById('card_number');
    if (cardInput) {
        cardInput.addEventListener('input', function(e) {
            let value = this.value.replace(/\D/g, '');
            value = value.replace(/(.{4})/g, '$1 ').trim();
            this.value = value;
        });
    }

    // Expiry Date Formatting
    const expiryInput = document.getElementById('expiry_date');
    if (expiryInput) {
        expiryInput.addEventListener('input', function(e) {
            let value = this.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.slice(0,2) + '/' + value.slice(2,4);
            }
            this.value = value;
        });
    }
});

// Form Validation Function
function validateForm(form) {
    let isValid = true;
    
    // Required Fields
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showError(field, 'This field is required');
            isValid = false;
        } else {
            clearError(field);
        }
    });

    // Email Validation
    const emailField = form.querySelector('input[type="email"]');
    if (emailField && emailField.value) {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(emailField.value)) {
            showError(emailField, 'Please enter a valid email address');
            isValid = false;
        }
    }

    // Password Validation
    const passwordField = form.querySelector('input[type="password"]');
    if (passwordField && passwordField.value) {
        if (passwordField.value.length < 8) {
            showError(passwordField, 'Password must be at least 8 characters long');
            isValid = false;
        }
    }

    return isValid;
}

// Error Display Functions
function showError(field, message) {
    clearError(field);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
    field.classList.add('error');
}

function clearError(field) {
    const errorDiv = field.parentNode.querySelector('.error-message');
    if (errorDiv) {
        errorDiv.remove();
    }
    field.classList.remove('error');
}

// Flash Messages
function showFlashMessage(message, type = 'success') {
    const flashDiv = document.createElement('div');
    flashDiv.className = `flash-message ${type}`;
    flashDiv.textContent = message;
    
    document.body.appendChild(flashDiv);
    
    setTimeout(() => {
        flashDiv.remove();
    }, 3000);
}

// Admin Dashboard Functions
if (window.location.pathname.includes('admin')) {
    // Product Image Preview
    const imageInput = document.getElementById('image');
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.createElement('img');
                    preview.src = e.target.result;
                    preview.style.maxWidth = '200px';
                    preview.style.marginTop = '10px';
                    
                    const container = imageInput.parentNode;
                    const oldPreview = container.querySelector('img');
                    if (oldPreview) {
                        container.removeChild(oldPreview);
                    }
                    container.appendChild(preview);
                }
                reader.readAsDataURL(file);
            }
        });
    }
}

// Cart Functions
function updateCart(productId, quantity) {
    fetch('/update-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showFlashMessage('Cart updated successfully');
            updateCartDisplay(data.cart);
        } else {
            showFlashMessage('Failed to update cart', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showFlashMessage('An error occurred', 'error');
    });
}

function updateCartDisplay(cart) {
    const cartItemsContainer = document.querySelector('.cart-items');
    const totalElement = document.querySelector('.total');
    
    if (cartItemsContainer && cart) {
        cartItemsContainer.innerHTML = '';
        let total = 0;
        
        cart.items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'cart-item';
            itemDiv.innerHTML = `
                <span>${item.name}</span>
                <span>$${item.price.toFixed(2)}</span>
            `;
            cartItemsContainer.appendChild(itemDiv);
            total += item.price * item.quantity;
        });
        
        if (totalElement) {
            totalElement.innerHTML = `<strong>Total: $${total.toFixed(2)}</strong>`;
        }
    }
} 