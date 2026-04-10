from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Product, Category, ProductUnlock, Offer, Chat, Notification, ProductImageGroup, ProductImage
from datetime import datetime
from sqlalchemy import or_
import os
import uuid
from app.utils.image_compressor import compress_image  # ← ADD THIS LINE

rooms_bp = Blueprint('rooms', __name__, url_prefix='/rooms')

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@rooms_bp.route('/')
def index():
    """List all available rooms with filters"""
    page = request.args.get('page', 1, type=int)
    
    # Base query - only show rooms (products with hostel_name not empty)
    query = Product.query.filter(
        Product.is_active == True,
        Product.hostel_name != ""  # Only rooms
    )
    
    # Apply filters
    location = request.args.get('location')
    if location:
        query = query.filter(Product.location.ilike(f'%{location}%'))
    
    # Status filter
    status = request.args.get('status', 'available')
    if status != 'all':
        query = query.filter(Product.status == status)
    
    # Deposit filter
    deposit_min = request.args.get('deposit_min', type=float)
    deposit_max = request.args.get('deposit_max', type=float)
    if deposit_min is not None:
        query = query.filter(Product.deposit >= deposit_min)
    if deposit_max is not None:
        query = query.filter(Product.deposit <= deposit_max)
    
    # Commission only
    commission_only = request.args.get('commission_only')
    if commission_only:
        query = query.filter(Product.is_commission_listing == True)
    
    # No deposit
    no_deposit = request.args.get('no_deposit')
    if no_deposit:
        query = query.filter(Product.deposit == 0)
    
    # Price range (rent)
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    if price_min is not None:
        query = query.filter(Product.price >= price_min)
    if price_max is not None:
        query = query.filter(Product.price <= price_max)
    
    # Leave date (upcoming)
    leave_before = request.args.get('leave_before')
    if leave_before:
        try:
            leave_date = datetime.strptime(leave_before, '%Y-%m-%d')
            query = query.filter(Product.leave_date <= leave_date)
        except:
            pass
    
    # Order by
    sort = request.args.get('sort', 'newest')
    if sort == 'newest':
        query = query.order_by(Product.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Product.created_at.asc())
    elif sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'leave_soon':
        query = query.order_by(Product.leave_date.asc())
    
    # Pagination
    rooms = query.paginate(page=page, per_page=12, error_out=False)
    
    categories = Category.query.all()
    
    return render_template('rooms/index.html', 
                         rooms=rooms, 
                         categories=categories,
                         filters=request.args)


@rooms_bp.route('/<int:room_id>')
def detail(room_id):
    """Room detail page"""
    room = Product.query.get_or_404(room_id)
    
    # Update status if needed
    room.update_status()
    db.session.commit()
    
    # Check if current user has unlocked this room
    is_unlocked = False
    if current_user.is_authenticated:
        is_unlocked = room.is_unlocked_by(current_user)
    
    # Get similar rooms
    similar_rooms = Product.query.filter(
        Product.id != room.id,
        Product.location == room.location,
        Product.is_active == True,
        Product.status == 'available',
        Product.hostel_name != ""  # Only rooms
    ).limit(3).all()
    
    return render_template('rooms/detail.html',
                         room=room,
                         is_unlocked=is_unlocked,
                         similar_rooms=similar_rooms)


@rooms_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new room listing"""
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('title')
            hostel_name = request.form.get('hostel_name')
            location = request.form.get('location')
            description = request.form.get('description')
            price = request.form.get('price', type=float)
            deposit = request.form.get('deposit', type=float, default=0)
            commission = request.form.get('commission_percentage', type=float, default=0)
            is_commission = request.form.get('is_commission_listing') == 'on'
            leave_date_str = request.form.get('leave_date')
            room_type = request.form.get('room_type', 'single')
            
            # Validate
            if not all([title, hostel_name, location, price, leave_date_str]):
                flash('Please fill in all required fields', 'danger')
                return redirect(url_for('rooms.create'))
            
            # Parse leave date
            try:
                leave_date = datetime.strptime(leave_date_str, '%Y-%m-%d')
            except:
                flash('Invalid leave date format', 'danger')
                return redirect(url_for('rooms.create'))
            
            # Handle image uploads
            image_files = request.files.getlist('images')
            
            # Validate at least one image was uploaded
            if not image_files or image_files[0].filename == '':
                flash('Please upload at least one room image', 'danger')
                return redirect(url_for('rooms.create'))
            
            # Create ProductImageGroup first
            image_group = ProductImageGroup()
            db.session.add(image_group)
            db.session.flush()
            
            # Save each image
            saved_images = 0
            for file in image_files:
                if file and file.filename != '' and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    unique_filename = f"{uuid.uuid4().hex}.{ext}"
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(filepath)
                    
                    # ✨ NEW: Compress the image
                    compression_result = compress_image(filepath, is_chat_image=False)
                    if compression_result['success']:
                        current_app.logger.info(f"Room image compressed: {compression_result['message']}")
                    else:
                        current_app.logger.warning(f"Room image compression failed: {compression_result['message']}")
                    
                    product_image = ProductImage(
                        filename=unique_filename,
                        filepath=filepath,
                        group_id=image_group.id
                    )
                    db.session.add(product_image)
                    saved_images += 1
            
            if saved_images == 0:
                flash('No valid images were uploaded', 'danger')
                db.session.rollback()
                return redirect(url_for('rooms.create'))
            
            # Create room
            room = Product(
                title=title,
                hostel_name=hostel_name,
                location=location,
                description=description,
                price=price,
                deposit=deposit,
                commission_percentage=commission if is_commission else 0,
                is_commission_listing=is_commission,
                leave_date=leave_date,
                room_type=room_type,
                seller_id=current_user.id,
                category_id=1,
                condition='available',
                contact_info=current_user.phone or '',
                Token=1,
                status='available',
                is_active=True,
                image_group_id=image_group.id
            )
            
            db.session.add(room)
            db.session.commit()
            
            flash(f'Room listing created successfully with {saved_images} images!', 'success')
            return redirect(url_for('rooms.detail', room_id=room.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Room creation error: {str(e)}")
            flash(f'Error creating room: {str(e)}', 'danger')
            return redirect(url_for('rooms.create'))
    
    return render_template('rooms/create.html')


@rooms_bp.route('/<int:room_id>/unlock', methods=['POST'])
@login_required
def unlock(room_id):
    """Unlock room contact details"""
    room = Product.query.get_or_404(room_id)
    
    # Check if already unlocked
    if room.is_unlocked_by(current_user):
        return jsonify({'success': True, 'already_unlocked': True})
    
    # Can't unlock own room
    if room.seller_id == current_user.id:
        flash('You cannot unlock your own listing', 'danger')
        return redirect(url_for('rooms.detail', room_id=room.id))
    
    # Check if room is available
    if room.status not in ['available', 'pending']:
        flash('This room is not available for unlocking', 'danger')
        return redirect(url_for('rooms.detail', room_id=room.id))
    
    # Create unlock record
    unlock = ProductUnlock(
        user_id=current_user.id,
        product_id=room.id,
        seller_id=room.seller_id,
        amount=room.get_unlock_fee(),
        status='completed',
        completed_at=datetime.utcnow(),
        unlocked_at=datetime.utcnow()
    )
    
    db.session.add(unlock)
    db.session.flush()  # Get unlock ID without committing
    
    # Increment unlock count
    room.increment_unlock_count()
    
    # Create notification for seller - FIXED: unlock_id is now set
    notification = Notification(
        user_id=room.seller_id,
        product_id=room.id,
        unlock_id=unlock.id,  # Use unlock.id instead of None
        message=f"{current_user.username} unlocked your room: {room.title}"
    )
    db.session.add(notification)
    
    db.session.commit()
    
    flash('Room contact details unlocked!', 'success')
    return redirect(url_for('rooms.detail', room_id=room.id))


@rooms_bp.route('/<int:room_id>/offer', methods=['POST'])
@login_required
def make_offer(room_id):
    """Make an offer on a room"""
    room = Product.query.get_or_404(room_id)
    
    if not room.can_make_offer(current_user):
        flash('You cannot make an offer on this room', 'danger')
        return redirect(url_for('rooms.detail', room_id=room.id))
    
    deposit_offer = request.form.get('deposit_offer', type=float)
    commission_offer = request.form.get('commission_offer', type=float)
    move_in_date_str = request.form.get('move_in_date')
    message = request.form.get('message', '')
    
    if not deposit_offer and not commission_offer:
        flash('Please specify either deposit or commission offer', 'danger')
        return redirect(url_for('rooms.detail', room_id=room.id))
    
    move_in_date = None
    if move_in_date_str:
        try:
            move_in_date = datetime.strptime(move_in_date_str, '%Y-%m-%d')
        except:
            pass
    
    offer = Offer(
        product_id=room.id,
        buyer_id=current_user.id,
        seller_id=room.seller_id,
        deposit_offer=deposit_offer,
        commission_offer=commission_offer,
        move_in_date=move_in_date,
        message=message,
        original_deposit=room.deposit,
        original_commission=room.commission_percentage
    )
    offer.calculate_offer_value()
    
    db.session.add(offer)
    db.session.flush()
    
    # Notify seller
    notification_seller = Notification(
        user_id=room.seller_id,
        product_id=room.id,
        unlock_id=offer.id,
        message=f"📝 New offer from {current_user.username} on '{room.title}'"
    )
    db.session.add(notification_seller)
    
    # Notify buyer (the person who made the offer)
    notification_buyer = Notification(
        user_id=current_user.id,
        product_id=room.id,
        unlock_id=offer.id,
        message=f"✅ Your offer on '{room.title}' has been sent to the seller. You'll be notified if they respond."
    )
    db.session.add(notification_buyer)
    
    db.session.commit()
    
    flash('Offer submitted successfully!', 'success')
    return redirect(url_for('rooms.detail', room_id=room.id))


@rooms_bp.route('/offer/<int:offer_id>/accept', methods=['POST'])
@login_required
def accept_offer(offer_id):
    """Accept an offer (seller only)"""
    offer = Offer.query.get_or_404(offer_id)
    room = offer.product
    
    if current_user.id != room.seller_id:
        flash('You are not authorized to accept this offer', 'danger')
        return redirect(url_for('rooms.detail', room_id=room.id))
    
    offer.accept()
    
    # Notify buyer that their offer was accepted
    notification_buyer = Notification(
        user_id=offer.buyer_id,
        product_id=room.id,
        unlock_id=offer.id,
        message=f"🎉 Congratulations! Your offer on '{room.title}' has been ACCEPTED! The room is now pending for 48 hours. Contact the seller to finalize."
    )
    db.session.add(notification_buyer)
    
    db.session.commit()
    
    flash('Offer accepted! The room is now pending for 48 hours.', 'success')
    return redirect(url_for('rooms.detail', room_id=room.id))


@rooms_bp.route('/<int:room_id>/cancel-agreement', methods=['POST'])
@login_required
def cancel_agreement(room_id):
    """Cancel current agreement (seller only)"""
    room = Product.query.get_or_404(room_id)
    
    if current_user.id != room.seller_id:
        flash('You are not authorized to cancel this agreement', 'danger')
        return redirect(url_for('rooms.detail', room_id=room.id))
    
    # Get the user who had the agreement (if any)
    agreed_user_id = room.agreement_user_id
    
    room.cancel_agreement()
    
    # Notify the user whose agreement was cancelled
    if agreed_user_id:
        notification = Notification(
            user_id=agreed_user_id,
            product_id=room.id,
            unlock_id=None,
            message=f"⚠️ The agreement on '{room.title}' has been CANCELLED by the seller. The room is now available again."
        )
        db.session.add(notification)
    
    db.session.commit()
    
    flash('Agreement cancelled. Room is now available.', 'success')
    return redirect(url_for('rooms.detail', room_id=room.id))


@rooms_bp.route('/<int:room_id>/mark-booked', methods=['POST'])
@login_required
def mark_booked(room_id):
    """Mark room as booked (seller only)"""
    room = Product.query.get_or_404(room_id)
    
    if current_user.id != room.seller_id:
        flash('You are not authorized to mark this as booked', 'danger')
        return redirect(url_for('rooms.detail', room_id=room.id))
    
    room.mark_booked()
    db.session.commit()
    
    flash('Room marked as booked!', 'success')
    return redirect(url_for('rooms.detail', room_id=room.id))


@rooms_bp.route('/my-listings')
@login_required
def my_listings():
    """Show current user's room listings"""
    # Only show rooms (products with hostel_name not empty)
    listings = Product.query.filter(
        Product.seller_id == current_user.id,
        Product.hostel_name != ""  # Only rooms, not regular products
    ).order_by(Product.created_at.desc()).all()
    return render_template('rooms/my_listings.html', listings=listings)


@rooms_bp.route('/my-unlocks')
@login_required
def my_unlocks():
    """Show rooms unlocked by current user"""
    unlocks = ProductUnlock.query.filter_by(user_id=current_user.id, status='completed').all()
    rooms = [unlock.product for unlock in unlocks if unlock.product]
    return render_template('rooms/my_unlocks.html', rooms=rooms)
