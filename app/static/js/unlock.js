// ===== UNLOCK.JS - UNLOCK PRODUCT PAGE FUNCTIONALITY =====
document.addEventListener('DOMContentLoaded', function() {
    // Only run if we're on unlock product page
    if (!document.querySelector('.unlock-container')) return;
    
    const unlockForm = document.getElementById('unlockForm');
    
    if (unlockForm) {
        unlockForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Disable button and show loading state
            const submitBtn = document.querySelector('.btn-unlock');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = 'Processing...';
            submitBtn.disabled = true;
            
            // Simulate processing delay for better UX
            setTimeout(() => {
                // Submit the form
                this.submit();
            }, 1500);
        });
    }
});

// Notification function for better UX
function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `<span>${message}</span>`;
    
    // Add styles for notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'error' ? 'var(--calm-error)' : 'var(--calm-primary)'};
        color: var(--calm-text-primary);
        padding: 12px 20px;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        animation: slideDown 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}