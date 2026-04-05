// ===== CHAT.js - Chat-specific functions =====

// Update unread chat count
function updateUnreadChatCount() {
    fetch('/chat/unread_count')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const badge = document.getElementById('unreadChatCount');
            const mobileBadge = document.getElementById('mobileUnreadChatCount');
            
            if (data.unread_count > 0) {
                if (badge) {
                    badge.textContent = data.unread_count > 99 ? '99+' : data.unread_count;
                    badge.style.display = 'inline-block';
                }
                if (mobileBadge) {
                    mobileBadge.textContent = data.unread_count > 99 ? '99+' : data.unread_count;
                    mobileBadge.style.display = 'inline-block';
                }
            } else {
                if (badge) badge.style.display = 'none';
                if (mobileBadge) mobileBadge.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error fetching unread count:', error);
        });
}

// Initialize chat features
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if user is logged in (chat link exists)
    if (document.querySelector('.chat-link')) {
        updateUnreadChatCount();
        setInterval(updateUnreadChatCount, 30000);
        
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden) {
                updateUnreadChatCount();
            }
        });
    }
});

// Make functions available globally
window.updateUnreadChatCount = updateUnreadChatCount;