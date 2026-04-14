// ===== CREATE.JS - CREATE PRODUCT PAGE FUNCTIONALITY =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('Product creation page loaded');
    
    // Only run if we're on create product page
    if (!document.querySelector('.create-product-container')) return;
    
    // Initialize steps - show only first step, hide others
    const steps = document.querySelectorAll('.form-step');
    steps.forEach((step, index) => {
        if (index === 0) {
            step.style.display = 'block';
            step.classList.add('active');
        } else {
            step.style.display = 'none';
            step.classList.remove('active');
        }
    });

    // Wizard navigation
    const stepButtons = document.querySelectorAll('.wizard-steps .step');
    
    // Next button functionality
    document.querySelectorAll('.btn-next').forEach(button => {
        button.addEventListener('click', function() {
            const currentStep = this.closest('.form-step');
            const currentStepNum = currentStep.dataset.step;
            const nextStepNum = this.dataset.next;
            const nextStep = document.querySelector(`.form-step[data-step="${nextStepNum}"]`);
            
            console.log('Moving from step', currentStepNum, 'to step', nextStepNum);
            
            if (validateStep(currentStepNum)) {
                console.log('Validation passed, moving to next step');
                
                // Hide current step
                currentStep.style.display = 'none';
                currentStep.classList.remove('active');
                
                // Show next step
                if (nextStep) {
                    nextStep.style.display = 'block';
                    nextStep.classList.add('active');
                }
                
                // Update wizard steps
                stepButtons.forEach(step => {
                    if (parseInt(step.dataset.step) <= parseInt(nextStepNum)) {
                        step.classList.add('active');
                    } else {
                        step.classList.remove('active');
                    }
                });
                
                // Update review summary when reaching step 3
                if (nextStepNum === '3') {
                    console.log('Updating review summary');
                    updateReviewSummary();
                }
            } else {
                console.log('Validation failed for step', currentStepNum);
            }
        });
    });
    
    // Previous button functionality
    document.querySelectorAll('.btn-prev').forEach(button => {
        button.addEventListener('click', function() {
            const currentStep = this.closest('.form-step');
            const prevStepNum = this.dataset.prev;
            const prevStep = document.querySelector(`.form-step[data-step="${prevStepNum}"]`);
            
            console.log('Moving back to step', prevStepNum);
            
            // Hide current step
            currentStep.style.display = 'none';
            currentStep.classList.remove('active');
            
            // Show previous step
            if (prevStep) {
                prevStep.style.display = 'block';
                prevStep.classList.add('active');
            }
            
            // Update wizard steps
            stepButtons.forEach(step => {
                if (parseInt(step.dataset.step) <= parseInt(prevStepNum)) {
                    step.classList.add('active');
                } else {
                    step.classList.remove('active');
                }
            });
        });
    });
    
    // Image upload functionality
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('image');
    const imagePreview = document.getElementById('imagePreview');
    
    console.log('Image upload elements:', { uploadArea, fileInput, imagePreview });
    
    if (uploadArea && fileInput) {
        // Click to upload
        uploadArea.addEventListener('click', function(e) {
            // Don't trigger if clicking on the file input itself
            if (e.target !== fileInput) {
                fileInput.click();
            }
        });
        
        // Drag and drop functionality
        ['dragover', 'dragenter'].forEach(event => {
            uploadArea.addEventListener(event, function(e) {
                e.preventDefault();
                uploadArea.style.borderColor = 'var(--primary)';
                uploadArea.style.background = '#111827';
            });
        });
        
        ['dragleave', 'dragend', 'drop'].forEach(event => {
            uploadArea.addEventListener(event, function(e) {
                e.preventDefault();
                uploadArea.style.borderColor = '#2d3748';
                uploadArea.style.background = 'transparent';
            });
        });
        
        // Handle file drop - UPDATED FOR MULTIPLE FILES
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            const files = e.dataTransfer.files;
            console.log('Files dropped:', files);
            if (files.length > 0) {
                handleMultipleImageUpload(files);
            }
        });
        
        // Handle file selection - UPDATED FOR MULTIPLE FILES
        fileInput.addEventListener('change', function(e) {
            console.log('File input changed:', e.target.files);
            if (e.target.files.length > 0) {
                handleMultipleImageUpload(e.target.files);
            }
        });
    }
    
    // Handle multiple image uploads
    function handleMultipleImageUpload(files) {
        console.log('Handling multiple image upload:', files);
        
        if (!files || files.length === 0) {
            console.log('No files provided');
            return;
        }
        
        // Validate each file
        const validFiles = [];
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            // Check if it's an image
            if (!file.type.startsWith('image/')) {
                alert('Please select only image files (JPEG, PNG, GIF, etc.)');
                return;
            }
            
            // Check file size (15MB limit)
            if (file.size > 15 * 1024 * 1024) {
                alert(`Image "${file.name}" is too large (${(file.size / 1024 / 1024).toFixed(2)}MB). Maximum size is 15MB.`);
                return;
            }
            
            validFiles.push(file);
        }
        
        if (validFiles.length === 0) {
            alert('No valid images to upload');
            return;
        }
        
        // Clear previous previews
        const imagePreview = document.getElementById('imagePreview');
        if (imagePreview) {
            imagePreview.innerHTML = '';
        }
        
        // Process each file for preview
        let previewsCreated = 0;
        
        validFiles.forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = function(e) {
                console.log(`File ${index + 1} read successfully`);
                
                // Create preview container for each image
                const previewItem = document.createElement('div');
                previewItem.className = 'preview-item';
                previewItem.dataset.index = index;
                previewItem.innerHTML = `
                    <img src="${e.target.result}" alt="Product preview ${index + 1}">
                    <button type="button" class="remove-image" title="Remove image" data-index="${index}">&times;</button>
                    <span class="image-counter">${index + 1}</span>
                `;
                
                // Add to preview area
                if (imagePreview) {
                    imagePreview.appendChild(previewItem);
                }
                
                // Add remove functionality
                const removeButton = previewItem.querySelector('.remove-image');
                removeButton.addEventListener('click', function() {
                    removeImageByIndex(index);
                });
                
                previewsCreated++;
                
                // When all previews are created, update the UI
                if (previewsCreated === validFiles.length) {
                    updateUploadAreaUI(validFiles.length);
                }
            };
            
            reader.onerror = function() {
                console.error(`Error reading file ${file.name}`);
                previewsCreated++;
                
                // If this was the last file, update UI anyway
                if (previewsCreated === validFiles.length) {
                    updateUploadAreaUI(validFiles.length);
                }
            };
            
            reader.readAsDataURL(file);
        });
        
        // Update file input with all selected files
        const dataTransfer = new DataTransfer();
        validFiles.forEach(file => {
            dataTransfer.items.add(file);
        });
        
        const fileInput = document.getElementById('image');
        if (fileInput) {
            fileInput.files = dataTransfer.files;
            console.log('File input updated with files:', fileInput.files.length, 'files');
        }
    }
    
    // Remove specific image by index
    function removeImageByIndex(indexToRemove) {
        console.log('Removing image at index:', indexToRemove);
        
        // Remove the preview
        const previewItem = document.querySelector(`.preview-item[data-index="${indexToRemove}"]`);
        if (previewItem) {
            previewItem.remove();
        }
        
        // Update the file input
        const fileInput = document.getElementById('image');
        if (fileInput && fileInput.files.length > 0) {
            const dataTransfer = new DataTransfer();
            const files = Array.from(fileInput.files);
            
            // Add all files except the one being removed
            files.forEach((file, index) => {
                if (index !== indexToRemove) {
                    dataTransfer.items.add(file);
                }
            });
            
            fileInput.files = dataTransfer.files;
            console.log('Updated file input, remaining files:', fileInput.files.length);
            
            // Update preview indices
            updatePreviewIndices();
            updateUploadAreaUI(fileInput.files.length);
            
            // If no files left, reset upload area
            if (fileInput.files.length === 0) {
                resetUploadArea();
            }
        }
    }
    
    // Update preview indices after removal
    function updatePreviewIndices() {
        const previewItems = document.querySelectorAll('.preview-item');
        previewItems.forEach((item, newIndex) => {
            item.dataset.index = newIndex;
            const removeButton = item.querySelector('.remove-image');
            if (removeButton) {
                removeButton.dataset.index = newIndex;
                // Update event listener
                removeButton.onclick = function() {
                    removeImageByIndex(newIndex);
                };
            }
            const counter = item.querySelector('.image-counter');
            if (counter) {
                counter.textContent = newIndex + 1;
            }
        });
    }
    
    // Update upload area UI based on number of images
    function updateUploadAreaUI(imageCount) {
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            if (imageCount > 0) {
                uploadArea.querySelector('h4').textContent = `${imageCount} Image${imageCount !== 1 ? 's' : ''} Uploaded`;
                uploadArea.querySelector('p').textContent = 'Click or drag to add more images';
                uploadArea.style.borderColor = 'var(--success)';
            } else {
                resetUploadArea();
            }
        }
    }
    
    // Reset upload area to initial state
    function resetUploadArea() {
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            uploadArea.querySelector('h4').textContent = 'Upload Product Images';
            uploadArea.querySelector('p').textContent = 'Drag & drop images or click to browse';
            uploadArea.style.borderColor = '#2d3748';
        }
    }
    
    // Character count for description
    const descriptionTextarea = document.getElementById('description');
    const charCount = document.getElementById('charCount');
    
    if (descriptionTextarea && charCount) {
        descriptionTextarea.addEventListener('input', function() {
            charCount.textContent = this.value.length;
        });
        
        // Initialize character count
        charCount.textContent = descriptionTextarea.value.length;
    }
    
    // Form validation
    function validateStep(step) {
        console.log('Validating step:', step);
        
        switch(step) {
            case '1':
                const title = document.getElementById('title');
                const category = document.getElementById('category_id');
                const condition = document.getElementById('condition');
                const image = document.getElementById('image');
                const description = document.getElementById('description');
                
                console.log('Form values:', {
                    title: title?.value,
                    category: category?.value,
                    condition: condition?.value,
                    image: image?.files,
                    description: description?.value
                });
                
                if (!title || !title.value.trim()) {
                    alert('Please enter a product title');
                    if (title) title.focus();
                    return false;
                }
                
                if (!category || !category.value) {
                    alert('Please select a category');
                    if (category) category.focus();
                    return false;
                }
                
                if (!condition || !condition.value) {
                    alert('Please select the product condition');
                    if (condition) condition.focus();
                    return false;
                }
                
                // Multiple image validation
                if (!image) {
                    alert('Image upload field not found');
                    return false;
                }
                
                const hasFiles = image.files && image.files.length > 0;
                const hasPreview = document.querySelectorAll('.preview-item img').length > 0;
                
                console.log('Image validation:', { hasFiles, hasPreview, filesCount: hasFiles ? image.files.length : 0 });
                
                // Minimum 1 image required
                if (!hasFiles && !hasPreview) {
                    alert('Please upload at least one product image');
                    return false;
                }
                
                // Check for at least 1 image
                const totalImages = Math.max(
                    hasFiles ? image.files.length : 0,
                    hasPreview ? document.querySelectorAll('.preview-item').length : 0
                );
                
                if (totalImages < 1) {
                    alert('Please upload at least one product image');
                    return false;
                }
                
                // Validate each file if files exist
                if (hasFiles) {
                    for (let i = 0; i < image.files.length; i++) {
                        const file = image.files[i];
                        if (!file.type.startsWith('image/')) {
                            alert(`File "${file.name}" is not a valid image file (JPEG, PNG, GIF, etc.)`);
                            return false;
                        }
                        
                        if (file.size > 15 * 1024 * 1024) {
                            alert(`Image "${file.name}" is too large (${(file.size / 1024 / 1024).toFixed(2)}MB). Maximum size is 15MB.`);
                            return false;
                        }
                    }
                }
                
                if (!description || !description.value.trim()) {
                    alert('Please enter a product description');
                    if (description) description.focus();
                    return false;
                }
                
                console.log('Step 1 validation passed');
                return true;
                
            case '2':
                const price = document.getElementById('price');
                const deliveryOption = document.querySelector('input[name="delivery_option"]:checked');
                
                console.log('Step 2 values:', {
                    price: price?.value,
                    deliveryOption: deliveryOption?.value
                });
                
                if (!price || !price.value || parseFloat(price.value) <= 0) {
                    alert('Please enter a valid price');
                    if (price) price.focus();
                    return false;
                }
                
                if (!deliveryOption) {
                    alert('Please select a delivery option');
                    return false;
                }
                
                // Validate delivery-specific fields
                if (deliveryOption.value === 'free') {
                    const deliveryAddress = document.querySelector('input[name="delivery_address"]');
                    if (!deliveryAddress || !deliveryAddress.value.trim()) {
                        alert('Please provide your wallet address or M-Pesa number for free delivery');
                        if (deliveryAddress) deliveryAddress.focus();
                        return false;
                    }
                }
                
                console.log('Step 2 validation passed');
                return true;
                
            case '3':
                // No payment validation needed - free listing
                console.log('Step 3 validation passed');
                return true;
                
            default:
                return true;
        }
    }
    
    // Update review summary
    function updateReviewSummary() {
        console.log('Updating review summary...');
        
        // Product details
        const title = document.getElementById('title');
        const category = document.getElementById('category_id');
        const condition = document.getElementById('condition');
        const description = document.getElementById('description');
        
        if (title) {
            const reviewTitle = document.getElementById('review-title');
            if (reviewTitle) reviewTitle.textContent = title.value || '-';
        }
        if (category) {
            const reviewCategory = document.getElementById('review-category');
            if (reviewCategory) reviewCategory.textContent = category.options[category.selectedIndex]?.text || '-';
        }
        if (condition) {
            const reviewCondition = document.getElementById('review-condition');
            if (reviewCondition) reviewCondition.textContent = condition.options[condition.selectedIndex]?.text || '-';
        }
        if (description) {
            const reviewDescription = document.getElementById('review-description');
            if (reviewDescription) {
                const descText = description.value || '';
                reviewDescription.textContent = 
                    descText.substring(0, 100) + (descText.length > 100 ? '...' : '');
            }
        }
        
        // Pricing & delivery
        const price = document.getElementById('price');
        if (price) {
            const reviewPrice = document.getElementById('review-price');
            if (reviewPrice) {
                reviewPrice.textContent = 
                    'KES ' + (price.value ? parseFloat(price.value).toLocaleString() : '-');
            }
        }
        
        const deliveryOption = document.querySelector('input[name="delivery_option"]:checked');
        const reviewDelivery = document.getElementById('review-delivery');
        if (reviewDelivery) {
            let deliveryText = '-';
            if (deliveryOption) {
                switch(deliveryOption.value) {
                    case 'free':
                        deliveryText = 'Free Delivery';
                        break;
                    case 'meetup':
                        deliveryText = 'Campus Meetup';
                        break;
                }
            }
            reviewDelivery.textContent = deliveryText;
        }
        
        console.log('Review summary updated');
    }
    
    // Form submission - FREE LISTING (no payment required)
    const productForm = document.getElementById('productForm');
    const submitBtn = document.getElementById('submitBtn');
    const paymentModal = document.getElementById('paymentProcessingModal');
    const paymentStatusText = document.getElementById('paymentStatusText');
    
    if (productForm) {
        productForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Form submission for free listing');
            
            // Validate all steps
            if (!validateStep('1') || !validateStep('2') || !validateStep('3')) {
                alert('Please complete all required fields correctly.');
                return;
            }
            
            // Show processing modal
            if (paymentModal) {
                paymentModal.style.display = 'flex';
            }
            
            if (paymentStatusText) {
                paymentStatusText.textContent = 'Creating your free listing...';
            }
            
            // Disable submit button to prevent multiple submissions
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }
            
            const formData = new FormData(productForm);
            
            try {
                const response = await fetch('/create', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                const responseText = await response.text();
                let json = null;
                try { json = JSON.parse(responseText); } catch(e) {}
                
                if (json && json.status === "success") {
                    // Product created successfully
                    hidePaymentModal();
                    window.location.href = '/my-products';
                    return;
                }
                
                // If response is HTML (redirect), follow it
                if (response.redirected) {
                    window.location.href = response.url;
                    return;
                }
                
                hidePaymentModal();
                enableSubmitButton();
                alert("Failed to create product. Please try again.");
                
            } catch (error) {
                console.error('Error:', error);
                hidePaymentModal();
                enableSubmitButton();
                alert('Network error: ' + error.message);
            }
        });
    }
    
    function hidePaymentModal() {
        if (paymentModal) {
            paymentModal.style.display = 'none';
        }
    }
    
    function enableSubmitButton() {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-check-circle"></i> List Item for Free';
        }
    }
    
    // Initialize delivery options
    console.log('Initializing delivery options...');
    const initialDeliveryOption = document.querySelector('input[name="delivery_option"]:checked');
    if (initialDeliveryOption) {
        console.log('Found initial delivery option:', initialDeliveryOption.value);
        initialDeliveryOption.dispatchEvent(new Event('change'));
    } else {
        console.log('No initial delivery option found');
    }
    
    console.log('Product creation page initialization complete');
});