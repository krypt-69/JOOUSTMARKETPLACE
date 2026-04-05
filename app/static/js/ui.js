// ===== UI.js - Universal UI functions =====

function toggleMenu() {
    const navLinks = document.getElementById('navLinks');
    if (navLinks) navLinks.classList.toggle('active');
}

// Auto-hide flash messages after 5 seconds
function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-8px)';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
}

// Mobile bottom navigation active state
function initMobileNav() {
    const currentPath = window.location.pathname;
    const mobileNavItems = document.querySelectorAll('.mobile-nav-item');
    
    mobileNavItems.forEach(item => {
        if (item.getAttribute('href') === currentPath) {
            item.classList.add('active');
        }
    });

    // Touch feedback for mobile nav
    mobileNavItems.forEach(item => {
        item.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.92)';
        });
        
        item.addEventListener('touchend', function() {
            this.style.transform = '';
        });
    });
}

// Ripple effect for premium buttons
function initRippleEffect() {
    const premiumButtons = document.querySelectorAll('.token-item, .sell-item, .notification-item, .myitems-item');
    
    // Add ripple CSS once
    if (!document.querySelector('#ripple-style')) {
        const style = document.createElement('style');
        style.id = 'ripple-style';
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(2);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    premiumButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                background: rgba(255,255,255,0.3);
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
            `;
            
            const size = Math.max(this.offsetWidth, this.offsetHeight);
            const rect = this.getBoundingClientRect();
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = e.clientX - rect.left - size/2 + 'px';
            ripple.style.top = e.clientY - rect.top - size/2 + 'px';
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

// Adaptive mobile navigation layout
function initAdaptiveMobileNav() {
    const navContainer = document.getElementById('mobileNavContainer');
    if (!navContainer) return;
    
    const navItems = navContainer.querySelectorAll('.mobile-nav-item');
    
    function adjust() {
        if (window.innerWidth <= 320 && navItems.length > 4) {
            navContainer.classList.add('mobile-nav-compact');
            navContainer.classList.remove('mobile-nav-scrollable');
        } else if (window.innerWidth <= 380 && navItems.length > 5) {
            navContainer.classList.add('mobile-nav-scrollable');
            navContainer.classList.remove('mobile-nav-compact');
        } else {
            navContainer.classList.remove('mobile-nav-scrollable', 'mobile-nav-compact');
        }
    }
    
    adjust();
    window.addEventListener('resize', adjust);
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initFlashMessages();
    initMobileNav();
    initRippleEffect();
    initAdaptiveMobileNav();
});
// ===== RADIAL SEARCH MENU FUNCTIONALITY =====
(function() {
    const searchBtn = document.getElementById('searchFabBtn');
    const radialMenu = document.getElementById('radialMenu');
    
    if (!searchBtn || !radialMenu) return;
    
    // Toggle menu on button click
    searchBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        radialMenu.classList.toggle('open');
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchBtn.contains(e.target) && !radialMenu.contains(e.target)) {
            radialMenu.classList.remove('open');
        }
    });
    
    // Handle radial item clicks - smooth scroll to section
    const radialItems = document.querySelectorAll('.radial-item');
    radialItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const sectionId = item.getAttribute('data-section');
            const targetSection = document.getElementById(sectionId);
            
            if (targetSection) {
                // Smooth scroll to section
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start',
                    inline: 'nearest'
                });
                
                // Optional: Add highlight effect
                targetSection.style.transition = 'background 0.3s ease';
                targetSection.style.background = 'rgba(108, 140, 156, 0.1)';
                setTimeout(() => {
                    targetSection.style.background = '';
                }, 800);
            }
            
            // Close menu after clicking
            radialMenu.classList.remove('open');
        });
    });
    
    // Close on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && radialMenu.classList.contains('open')) {
            radialMenu.classList.remove('open');
        }
    });
})();

// Make functions available globally
window.toggleMenu = toggleMenu;