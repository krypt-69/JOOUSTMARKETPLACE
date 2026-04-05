// ===== PRODUCTS.JS - PRODUCTS PAGE FUNCTIONALITY =====
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const searchInput = document.getElementById('searchInput');
    const clearSearch = document.getElementById('clearSearch');
    const categoryFilter = document.getElementById('categoryFilter');
    const sortFilter = document.getElementById('sortFilter');
    const priceRange = document.getElementById('priceRange');
    const maxPriceDisplay = document.getElementById('maxPriceDisplay');
    const filterToggle = document.getElementById('filterToggle');
    const closeFilter = document.getElementById('closeFilter');
    const filterPanel = document.getElementById('filterPanel');
    const resetFilters = document.getElementById('resetFilters');
    const applyFilters = document.getElementById('applyFilters');
    const viewButtons = document.querySelectorAll('.view-btn');
    const productsView = document.getElementById('productsView');
    const productCards = document.querySelectorAll('.product-card');
    const actionChips = document.querySelectorAll('.action-chip');
    const loadMoreBtn = document.getElementById('loadMore');
    const quickViewModal = document.getElementById('quickViewModal');
    const closeModal = document.querySelector('.close-modal');
    const resultsCount = document.getElementById('resultsCount');

    // Only run if we're on products page
    if (!productsView) return;

    // Price Range Display
    if (priceRange) {
        priceRange.addEventListener('input', function() {
            const value = this.value;
            if (value == this.max) {
                maxPriceDisplay.textContent = `KES ${parseInt(value).toLocaleString()}+`;
            } else {
                maxPriceDisplay.textContent = `KES ${parseInt(value).toLocaleString()}`;
            }
        });
    }

    // Search Functionality
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            if (clearSearch) clearSearch.style.display = this.value ? 'block' : 'none';
            filterProducts();
        });
    }

    if (clearSearch) {
        clearSearch.addEventListener('click', function() {
            searchInput.value = '';
            this.style.display = 'none';
            filterProducts();
        });
    }

    // Filter Toggle
    if (filterToggle) {
        filterToggle.addEventListener('click', function() {
            filterPanel.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }

    if (closeFilter) {
        closeFilter.addEventListener('click', function() {
            filterPanel.classList.remove('active');
            document.body.style.overflow = '';
        });
    }

    // Apply Filters
    if (applyFilters) {
        applyFilters.addEventListener('click', function() {
            filterProducts();
            filterPanel.classList.remove('active');
            document.body.style.overflow = '';
        });
    }

    // Reset Filters
    if (resetFilters) {
        resetFilters.addEventListener('click', function() {
            if (categoryFilter) categoryFilter.value = '';
            if (priceRange) {
                priceRange.value = priceRange.max;
                maxPriceDisplay.textContent = `KES ${parseInt(priceRange.max).toLocaleString()}+`;
            }
            
            document.querySelectorAll('input[name="condition"]').forEach(checkbox => {
                checkbox.checked = false;
            });
            
            filterProducts();
        });
    }

    // View Toggle
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            viewButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            if (this.dataset.view === 'list') {
                productsView.classList.add('list-view');
            } else {
                productsView.classList.remove('list-view');
            }
            
            // Save preference to localStorage
            localStorage.setItem('productView', this.dataset.view);
        });
    });

    // Load saved view preference
    const savedView = localStorage.getItem('productView') || 'grid';
    const savedViewBtn = document.querySelector(`.view-btn[data-view="${savedView}"]`);
    if (savedViewBtn) {
        savedViewBtn.click();
    }

    // Action Chips (Quick Categories)
    actionChips.forEach(chip => {
        chip.addEventListener('click', function() {
            actionChips.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            
            const category = this.dataset.category;
            if (categoryFilter) {
                if (category === 'all') {
                    categoryFilter.value = '';
                } else {
                    categoryFilter.value = category;
                }
            }
            
            filterProducts();
        });
    });

    // Sort Functionality
    if (sortFilter) {
        sortFilter.addEventListener('change', sortProducts);
    }

    // Load More Button (Simulated)
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', function() {
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            this.disabled = true;
            
            // Simulate API call
            setTimeout(() => {
                // In a real app, you would fetch more products from the server
                this.innerHTML = '<i class="fas fa-redo"></i> Load More Products';
                this.disabled = false;
                
                // Show a toast message
                showToast('More products loaded!', 'success');
            }, 1500);
        });
    }

    // Quick View Modal
    document.querySelectorAll('.product-card').forEach(card => {
        card.addEventListener('click', function(e) {
            // Don't open modal if clicking on action buttons, links, or quick actions
            if (e.target.closest('.product-actions') || 
                e.target.closest('.quick-action') || 
                e.target.closest('a') || 
                e.target.closest('button') ||
                e.target.tagName === 'A' || 
                e.target.tagName === 'BUTTON') {
                return;
            }
            openQuickView(this);
        });
    });

    if (closeModal) {
        closeModal.addEventListener('click', function() {
            quickViewModal.classList.remove('active');
            document.body.style.overflow = '';
        });
    }

    if (quickViewModal) {
        quickViewModal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }

    // Filter Products Function
    function filterProducts() {
        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        const selectedCategory = categoryFilter ? categoryFilter.value : '';
        const maxPrice = priceRange ? parseInt(priceRange.value) : 10000;
        const selectedConditions = Array.from(document.querySelectorAll('input[name="condition"]:checked'))
            .map(checkbox => checkbox.value);
        
        let visibleCount = 0;
        
        productCards.forEach(card => {
            const productName = card.dataset.name;
            const productCategory = card.dataset.category.toLowerCase();
            const productPrice = parseInt(card.dataset.price);
            const productCondition = card.dataset.condition;
            
            const matchesSearch = productName.includes(searchTerm);
            const matchesCategory = !selectedCategory || productCategory === selectedCategory.toLowerCase();
            const matchesPrice = productPrice <= maxPrice;
            const matchesCondition = selectedConditions.length === 0 || 
                selectedConditions.includes(productCondition);
            
            if (matchesSearch && matchesCategory && matchesPrice && matchesCondition) {
                card.style.display = 'block';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        
        // Update results count
        if (resultsCount) {
            resultsCount.textContent = `${visibleCount} Products Available`;
        }
        
        // Sort after filtering
        sortProducts();
    }

    // Sort Products Function
    function sortProducts() {
        if (!sortFilter) return;
        
        const sortBy = sortFilter.value;
        const container = productsView;
        const cards = Array.from(productCards).filter(card => card.style.display !== 'none');
        
        cards.sort((a, b) => {
            switch (sortBy) {
                case 'price_low':
                    return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
                case 'price_high':
                    return parseFloat(b.dataset.price) - parseFloat(a.dataset.price);
                case 'name':
                    return a.querySelector('.product-title').textContent
                        .localeCompare(b.querySelector('.product-title').textContent);
                case 'newest':
                default:
                    return parseFloat(b.dataset.date) - parseFloat(a.dataset.date);
            }
        });
        
        // Reappend cards in sorted order
        cards.forEach(card => container.appendChild(card));
    }

    // Quick View Function
    function openQuickView(productCard) {
        const title = productCard.querySelector('.product-title').textContent;
        const price = productCard.querySelector('.product-price').textContent;
        const description = productCard.querySelector('.product-description').textContent;
        const seller = productCard.querySelector('.seller-name').textContent;
        const image = productCard.querySelector('.product-image img');
        const imageSrc = image ? image.src : '';
        const imageAlt = image ? image.alt : 'Product Image';
        
        const modalBody = quickViewModal.querySelector('.modal-body');
        modalBody.innerHTML = `
            <div class="quick-view-content">
                <div class="quick-view-image">
                    ${imageSrc ? 
                        `<img src="${imageSrc}" alt="${imageAlt}" loading="lazy">` : 
                        `<div class="product-image-placeholder">
                            <i class="fas fa-camera"></i>
                            <span>No Image Available</span>
                        </div>`
                    }
                </div>
                <div class="quick-view-details">
                    <h4>${title}</h4>
                    <div class="quick-view-price">${price}</div>
                    <p>${description}</p>
                    <div class="quick-view-seller">
                        <strong>Seller:</strong> ${seller}
                    </div>
                    <div class="quick-view-actions">
                        ${productCard.querySelector('.product-actions').innerHTML}
                    </div>
                </div>
            </div>
        `;
        
        quickViewModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Reattach event listeners to modal buttons
        setTimeout(() => {
            const modalActions = modalBody.querySelectorAll('.btn-action');
            modalActions.forEach(button => {
                if (button.href) {
                    button.addEventListener('click', function(e) {
                        quickViewModal.classList.remove('active');
                        document.body.style.overflow = '';
                    });
                }
            });
        }, 100);
    }

    // Toast Notification Function
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: type === 'success' ? '#4CB944' : '#405DE6',
            color: 'white',
            padding: '10px 16px',
            borderRadius: 'var(--radius-sm)',
            boxShadow: 'var(--shadow-hover)',
            zIndex: '1003',
            transform: 'translateX(100px)',
            opacity: '0',
            transition: 'all 0.3s ease',
            fontSize: '0.85rem',
            maxWidth: '300px',
            wordBreak: 'break-word'
        });
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
            toast.style.opacity = '1';
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.transform = 'translateX(100px)';
            toast.style.opacity = '0';
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    // Initialize
    filterProducts();
    
    // Show clear search button if there's existing text
    if (searchInput && searchInput.value && clearSearch) {
        clearSearch.style.display = 'block';
    }
    
    // Handle window resize
    window.addEventListener('resize', function() {
        // Recalculate any layout issues on resize
        filterProducts();
    });
});