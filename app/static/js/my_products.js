// ===== MY_PRODUCTS.JS - MY PRODUCTS PAGE FUNCTIONALITY =====
document.addEventListener('DOMContentLoaded', function() {
    // Only run if we're on my products page
    if (!document.querySelector('.my-products-container')) return;
    
    const filterButtons = document.querySelectorAll('.filter-btn');
    const productCards = document.querySelectorAll('.product-card');
    const searchInput = document.getElementById('searchInput');
    const searchClear = document.querySelector('.search-clear');
    const sortSelect = document.getElementById('sortSelect');
    const resetFiltersBtn = document.getElementById('resetFilters');

    // Show/hide search clear button
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            if (searchClear) searchClear.style.display = this.value ? 'block' : 'none';
            filterProducts();
        });
    }

    if (searchClear) {
        searchClear.addEventListener('click', function() {
            searchInput.value = '';
            this.style.display = 'none';
            filterProducts();
        });
    }

    // Filter buttons
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            filterProducts();
        });
    });

    // Sort functionality
    if (sortSelect) {
        sortSelect.addEventListener('change', sortProducts);
    }

    // Reset filters
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            document.querySelector('.filter-btn[data-filter="all"]').classList.add('active');
            if (searchInput) {
                searchInput.value = '';
                if (searchClear) searchClear.style.display = 'none';
            }
            if (sortSelect) sortSelect.value = 'newest';
            filterProducts();
        });
    }

    function filterProducts() {
        if (!searchInput) return;
        
        const searchTerm = searchInput.value.toLowerCase();
        const activeFilter = document.querySelector('.filter-btn.active')?.dataset.filter || 'all';
        const emptyState = document.getElementById('emptyFiltered');
        
        let visibleCount = 0;

        productCards.forEach(card => {
            const productName = card.dataset.name;
            const productStatus = card.dataset.status;
            const productCategory = card.dataset.category;
            const isFeatured = card.dataset.featured === 'true';
            
            const matchesSearch = productName.includes(searchTerm);
            const matchesFilter = activeFilter === 'all' || 
                                (activeFilter === 'available' && productStatus === 'available') ||
                                (activeFilter === 'sold' && productStatus === 'sold') ||
                                (activeFilter === 'featured' && isFeatured) ||
                                (activeFilter === productCategory);
            
            if (matchesSearch && matchesFilter) {
                card.style.display = 'grid';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        // Show/hide empty state
        if (emptyState) {
            if (visibleCount === 0 && (searchTerm || activeFilter !== 'all')) {
                emptyState.style.display = 'block';
            } else {
                emptyState.style.display = 'none';
            }
        }

        sortProducts();
    }

    function sortProducts() {
        if (!sortSelect) return;
        
        const sortBy = sortSelect.value;
        const container = document.getElementById('productsGrid');
        const cards = Array.from(productCards).filter(card => card.style.display !== 'none');
        
        cards.sort((a, b) => {
            switch (sortBy) {
                case 'price_high':
                    return parseFloat(b.dataset.price) - parseFloat(a.dataset.price);
                case 'price_low':
                    return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
                case 'name':
                    return a.querySelector('.product-title').textContent
                        .localeCompare(b.querySelector('.product-title').textContent);
                case 'oldest':
                    return parseFloat(a.dataset.date) - parseFloat(b.dataset.date);
                case 'newest':
                default:
                    return parseFloat(b.dataset.date) - parseFloat(a.dataset.date);
            }
        });

        // Reappend cards in sorted order
        cards.forEach(card => container.appendChild(card));
    }

    // Initialize
    filterProducts();
});

// Image Gallery State
let currentProductImages = [];
let currentImageIndex = 0;

// Open Image Gallery
function openImageGallery(productId, imageUrls) {
    if (imageUrls && imageUrls.length > 0) {
        currentProductImages = imageUrls;
        currentImageIndex = 0;
        showImageGallery();
    }
}

function showImageGallery() {
    const modal = document.getElementById('imageGalleryModal');
    const galleryImage = document.getElementById('galleryImage');
    const thumbnails = document.getElementById('galleryThumbnails');
    const counter = document.getElementById('galleryCounter');
    
    if (currentProductImages.length > 0) {
        galleryImage.src = currentProductImages[currentImageIndex];
        
        // Update counter
        counter.textContent = `${currentImageIndex + 1} / ${currentProductImages.length}`;
        
        // Update thumbnails
        thumbnails.innerHTML = '';
        currentProductImages.forEach((src, index) => {
            const thumb = document.createElement('img');
            thumb.src = src;
            thumb.className = `thumbnail ${index === currentImageIndex ? 'active' : ''}`;
            thumb.onclick = () => {
                currentImageIndex = index;
                showImageGallery();
            };
            thumbnails.appendChild(thumb);
        });
        
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

function closeImageGallery() {
    const modal = document.getElementById('imageGalleryModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

function changeImage(direction) {
    currentImageIndex = (currentImageIndex + direction + currentProductImages.length) % currentProductImages.length;
    showImageGallery();
}

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    const modal = document.getElementById('imageGalleryModal');
    if (modal && modal.style.display === 'block') {
        if (e.key === 'Escape') {
            closeImageGallery();
        } else if (e.key === 'ArrowLeft') {
            changeImage(-1);
        } else if (e.key === 'ArrowRight') {
            changeImage(1);
        }
    }
});

// Mark as sold function
function markAsSold(productId) {
    if (confirm('Mark this product as sold?')) {
        fetch(`/mark-sold/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('Product marked as sold successfully!');
                location.reload();
            } else {
                alert('Error: ' + (data.message || 'Unknown error occurred'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }
}

// Delete product function
function deleteProduct(productId) {
    if (confirm('Are you sure you want to delete this product? This action cannot be undone.')) {
        fetch(`/delete/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('Product deleted successfully!');
                location.reload();
            } else {
                alert('Error: ' + (data.message || 'Unknown error occurred'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }
}