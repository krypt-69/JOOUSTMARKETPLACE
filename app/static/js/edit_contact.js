// ===== EDIT_CONTACT.JS - EDIT CONTACT DETAILS PAGE FUNCTIONALITY =====
document.addEventListener('DOMContentLoaded', function() {
    // Only run if we're on edit contact details page
    if (!document.querySelector('.contact-details-container')) return;
    
    // Add floating label functionality
    const inputs = document.querySelectorAll('.input-container input, .input-container select');
    
    inputs.forEach(input => {
        // Check initial state
        if (input.value || (input.tagName === 'SELECT' && input.value !== '')) {
            input.nextElementSibling.style.top = '0';
            input.nextElementSibling.style.fontSize = '0.75rem';
            input.nextElementSibling.style.color = '#5D3FD3';
            input.nextElementSibling.style.fontWeight = '600';
        }
        
        input.addEventListener('focus', function() {
            this.nextElementSibling.style.top = '0';
            this.nextElementSibling.style.fontSize = '0.75rem';
            this.nextElementSibling.style.color = '#5D3FD3';
            this.nextElementSibling.style.fontWeight = '600';
        });
        
        input.addEventListener('blur', function() {
            if (!this.value && (this.tagName !== 'SELECT' || this.value === '')) {
                this.nextElementSibling.style.top = '50%';
                this.nextElementSibling.style.fontSize = '0.9rem';
                this.nextElementSibling.style.color = '#718096';
                this.nextElementSibling.style.fontWeight = '500';
            }
        });
    });
    
    // Add input validation styling
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.checkValidity()) {
                this.style.borderColor = 'rgba(6, 214, 160, 0.5)';
            } else {
                this.style.borderColor = 'rgba(255, 107, 107, 0.5)';
            }
        });
    });
    
    // Add click animations to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!this.href || this.getAttribute('type') === 'submit') {
                this.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            }
        });
    });
    
    // Add entrance animations
    const elements = document.querySelectorAll('.contact-header, .form-section, .contact-preview');
    elements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        setTimeout(() => {
            el.style.transition = 'all 0.5s ease';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, index * 100);
    });
});