// ===== NOTIFICATIONS.JS - NOTIFICATIONS PAGE FUNCTIONALITY =====
document.addEventListener('DOMContentLoaded', function() {
    // Only run if we're on notifications page
    if (!document.querySelector('.notifications-container')) return;
    
    // Mark as read functionality
    const markReadButtons = document.querySelectorAll('.mark-read-btn');
    
    markReadButtons.forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            
            const notificationId = this.dataset.notificationId;
            const notificationCard = this.closest('.notification-card');
            
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = 'Marking...';
            this.disabled = true;
            
            try {
                const response = await markNotificationAsRead(notificationId);
                
                if (response.success) {
                    // Update UI
                    notificationCard.classList.remove('unread');
                    
                    // Remove the button
                    this.remove();
                    
                    // Update badge
                    const oldBadge = notificationCard.querySelector('.badge');
                    if (oldBadge) {
                        oldBadge.className = 'badge read';
                        oldBadge.textContent = 'Read';
                    }
                    
                    showToast('Notification marked as read', 'success');
                }
            } catch (error) {
                console.error('Error marking notification as read:', error);
                this.innerHTML = originalText;
                this.disabled = false;
                showToast('Failed to mark as read', 'error');
            }
        });
    });

    // Mark all as read
    const markAllBtn = document.getElementById('markAllBtn');
    if (markAllBtn) {
        markAllBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            
            const originalText = this.innerHTML;
            this.innerHTML = 'Marking All...';
            this.disabled = true;
            
            try {
                const response = await markAllNotificationsAsRead();
                
                if (response.success) {
                    // Update all unread notifications
                    document.querySelectorAll('.notification-card.unread').forEach(card => {
                        card.classList.remove('unread');
                        
                        const markReadBtn = card.querySelector('.mark-read-btn');
                        if (markReadBtn) markReadBtn.remove();
                        
                        const badge = card.querySelector('.badge');
                        if (badge) {
                            badge.className = 'badge read';
                            badge.textContent = 'Read';
                        }
                    });
                    
                    showToast('All notifications marked as read', 'success');
                    
                    // Submit the form
                    setTimeout(() => {
                        document.getElementById('markAllForm').submit();
                    }, 500);
                }
            } catch (error) {
                console.error('Error marking all as read:', error);
                this.innerHTML = originalText;
                this.disabled = false;
                showToast('Failed to mark all as read', 'error');
            }
        });
    }

    // API functions
    async function markNotificationAsRead(notificationId) {
        const response = await fetch(`/notifications/${notificationId}/read`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        return await response.json();
    }

    async function markAllNotificationsAsRead() {
        const response = await fetch('/notifications/mark-all-read', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        return await response.json();
    }

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
});