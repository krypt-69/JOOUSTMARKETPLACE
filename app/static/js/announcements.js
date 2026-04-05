// ============================================
// Announcements - Mobile Timeline JavaScript
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Only run on announcements page
    const timelineContainer = document.querySelector('.timeline-container');
    if (!timelineContainer) return;
    
    console.log('Announcements JS loaded'); // Debug
    
    let expandedMessageId = null;
    
    // ========== EXPAND/COLLAPSE FUNCTIONALITY ==========
    const expandBtns = document.querySelectorAll('.expand-btn');
    console.log('Found expand buttons:', expandBtns.length);
    
    expandBtns.forEach(btn => {
        // Remove any existing listeners to avoid duplicates
        btn.removeEventListener('click', handleExpandClick);
        btn.addEventListener('click', handleExpandClick);
    });
    
    function handleExpandClick(e) {
        e.stopPropagation();
        const btn = this;
        const messageCard = btn.closest('.message-card');
        const messageThread = messageCard.closest('.message-thread');
        const messageId = messageThread ? messageThread.dataset.messageId : null;
        const preview = messageCard.querySelector('.message-preview');
        const full = messageCard.querySelector('.message-full');
        
        console.log('Expand clicked:', messageId); // Debug
        
        if (!preview || !full) return;
        
        // If this message is expanded
        if (expandedMessageId === messageId) {
            // Collapse it
            full.style.display = 'none';
            preview.style.display = 'block';
            btn.textContent = 'Read more';
            expandedMessageId = null;
            console.log('Collapsed'); // Debug
        } else {
            // Collapse all others
            const allFulls = document.querySelectorAll('.message-full');
            const allPreviews = document.querySelectorAll('.message-preview');
            const allBtns = document.querySelectorAll('.expand-btn');
            
            allFulls.forEach(f => f.style.display = 'none');
            allPreviews.forEach(p => p.style.display = 'block');
            allBtns.forEach(b => b.textContent = 'Read more');
            
            // Expand this one
            full.style.display = 'block';
            preview.style.display = 'none';
            btn.textContent = 'Show less';
            expandedMessageId = messageId;
            console.log('Expanded'); // Debug
        }
    }
    
    // ========== REACTIONS FUNCTIONALITY ==========
    const reactionBtns = document.querySelectorAll('.reaction-btn');
    console.log('Found reaction buttons:', reactionBtns.length);
    
    reactionBtns.forEach(btn => {
        btn.removeEventListener('click', handleReactionClick);
        btn.addEventListener('click', handleReactionClick);
    });
    
    async function handleReactionClick(e) {
        e.stopPropagation();
        const btn = this;
        const reactionType = btn.dataset.type;
        const announcementId = btn.dataset.id;
        
        if (!announcementId) {
            console.error('No announcement ID found');
            return;
        }
        
        console.log('Reaction clicked:', reactionType, announcementId); // Debug
        
        // Visual feedback - show loading
        const originalText = btn.innerHTML;
        btn.style.opacity = '0.5';
        
        try {
            const response = await fetch(`/announcements/api/announcements/${announcementId}/react`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ reaction_type: reactionType })
            });
            
            const data = await response.json();
            console.log('Response:', data); // Debug
            
            if (data.success) {
                // Update all reaction counts for this announcement
                const thread = document.querySelector(`.message-thread[data-message-id="${announcementId}"]`);
                if (thread) {
                    const allBtns = thread.querySelectorAll('.reaction-btn');
                    
                    allBtns.forEach(button => {
                        const type = button.dataset.type;
                        const countElement = button.querySelector('.reaction-count');
                        
                        if (data.reaction_counts && data.reaction_counts[type] !== undefined) {
                            countElement.textContent = data.reaction_counts[type];
                        }
                        
                        // Highlight active reaction
                        if (data.user_reaction === type) {
                            button.classList.add('active');
                        } else {
                            button.classList.remove('active');
                        }
                    });
                }
            } else {
                console.error('Error:', data.error);
                // Show error feedback
                showTemporaryMessage('Failed to update reaction', 'error');
            }
        } catch (error) {
            console.error('Network error:', error);
            showTemporaryMessage('Network error. Please try again.', 'error');
        } finally {
            // Restore button appearance
            btn.style.opacity = '1';
        }
    }
    
    // Helper function to show temporary messages
    function showTemporaryMessage(message, type) {
        const msgDiv = document.createElement('div');
        msgDiv.textContent = message;
        msgDiv.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: ${type === 'error' ? '#dc2626' : '#10b981'};
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        `;
        document.body.appendChild(msgDiv);
        setTimeout(() => msgDiv.remove(), 3000);
    }
    
    // ========== DYNAMIC TIME UPDATE ==========
    function updateTimes() {
        const timeElements = document.querySelectorAll('.message-time');
        timeElements.forEach(elem => {
            const timestamp = elem.dataset.timestamp;
            if (timestamp) {
                const timeAgo = getTimeAgo(new Date(timestamp));
                elem.textContent = timeAgo;
            }
        });
    }
    
    function getTimeAgo(date) {
        const now = new Date();
        const diffSeconds = Math.floor((now - date) / 1000);
        
        if (isNaN(diffSeconds)) return 'Just now';
        if (diffSeconds < 60) return 'Just now';
        if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)} min ago`;
        if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)} hr ago`;
        if (diffSeconds < 604800) return `${Math.floor(diffSeconds / 86400)} days ago`;
        
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
    
    // Initial time update
    updateTimes();
    
    // Update every minute
    setInterval(updateTimes, 60000);
    
    console.log('Announcements JS initialized successfully');
});