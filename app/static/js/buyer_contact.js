// ===== BUYER_CONTACT.JS - BUYER CONTACT PAGE FUNCTIONALITY =====
document.addEventListener('DOMContentLoaded', function() {
    // Only run if we're on buyer contact page
    if (!document.querySelector('.contact-page')) return;
    
    const contactItems = document.querySelectorAll('.contact-item');
    
    // Copy on long press for items without action buttons
    contactItems.forEach(item => {
        let pressTimer;
        const contactValue = item.querySelector('.contact-value');
        const contactAction = item.querySelector('.contact-action');
        
        if (contactValue && !contactAction) {
            item.addEventListener('touchstart', (e) => {
                pressTimer = setTimeout(() => {
                    const text = contactValue.textContent.trim();
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(text).then(() => {
                            showCopyFeedback(contactValue);
                        }).catch(() => {
                            fallbackCopy(text, contactValue);
                        });
                    } else {
                        fallbackCopy(text, contactValue);
                    }
                }, 500);
            });
            
            item.addEventListener('touchend', () => {
                clearTimeout(pressTimer);
            });
            
            item.addEventListener('touchmove', () => {
                clearTimeout(pressTimer);
            });
        }
    });
    
    // Handle contact actions animation
    document.querySelectorAll('.contact-action').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            this.style.transform = 'scale(0.9)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
    
    // Entrance animations
    const elements = document.querySelectorAll('.contact-item');
    elements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(10px)';
        setTimeout(() => {
            el.style.transition = 'all 0.3s ease';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, 50 * index);
    });
});

function showCopyFeedback(element) {
    element.classList.add('copy-feedback');
    const originalText = element.textContent;
    element.textContent = 'Copied!';
    
    setTimeout(() => {
        element.textContent = originalText;
        element.classList.remove('copy-feedback');
    }, 1000);
}

function fallbackCopy(text, element) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.top = '0';
    textarea.style.left = '0';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        document.execCommand('copy');
        showCopyFeedback(element);
    } catch (err) {
        console.error('Copy failed:', err);
    }
    
    document.body.removeChild(textarea);
}