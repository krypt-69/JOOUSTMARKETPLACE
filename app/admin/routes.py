from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Product, Category, ProductUnlock, Notification, Offer, AdminLog, ProductImage, ProductImageGroup
from datetime import datetime, timedelta
from sqlalchemy import func
from . import admin_bp
import os
import psutil

# ============================================
# ADMIN REQUIRED DECORATOR
# ============================================
def admin_required(f):
    """Decorator to ensure user is admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access admin area.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# ADMIN ACTION LOGGING DECORATOR
# ============================================
def log_admin_action(action, target_type=None, target_id=None, target_name=None, details=None):
    """Decorator to automatically log admin actions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get IP address
            ip_address = request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown')
            
            # Execute the route function
            response = f(*args, **kwargs)
            
            # Log the action
            try:
                # If target_id is in kwargs, use it
                actual_target_id = target_id
                actual_target_name = target_name
                
                # Try to extract from kwargs if not provided
                if 'user_id' in kwargs and not actual_target_id:
                    actual_target_id = kwargs['user_id']
                if 'product_id' in kwargs and not actual_target_id:
                    actual_target_id = kwargs['product_id']
                if 'room_id' in kwargs and not actual_target_id:
                    actual_target_id = kwargs['room_id']
                    
                log_entry = AdminLog(
                    admin_id=current_user.id,
                    admin_username=current_user.username,
                    action=action,
                    target_type=target_type,
                    target_id=actual_target_id,
                    target_name=actual_target_name,
                    details=details,
                    ip_address=ip_address
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Failed to log admin action: {e}")
            
            return response
        return decorated_function
    return decorator

# ============================================
# ADMIN AUTHENTICATION
# ============================================
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Separate admin login page"""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    if current_user.is_authenticated and not current_user.is_admin:
        flash('You do not have admin access.', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.is_admin and user.check_password(password):
            from flask_login import login_user
            login_user(user)
            flash('Welcome to Admin Panel!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials or insufficient permissions.', 'error')
    
    return render_template('admin/login.html')

# ============================================
# ADMIN DASHBOARD
# ============================================
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Main admin dashboard"""
    total_users = User.query.count()
    total_products = Product.query.filter(
        (Product.hostel_name == '') | (Product.hostel_name.is_(None))
    ).count()
    total_rooms = Product.query.filter(
        Product.hostel_name != '',
        Product.hostel_name.isnot(None)
    ).count()
    active_products = Product.query.filter_by(is_active=True, is_sold=False).count()
    total_revenue = db.session.query(func.sum(ProductUnlock.amount)).filter_by(status='completed').scalar() or 0
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_products = Product.query.filter(
        (Product.hostel_name == '') | (Product.hostel_name.is_(None))
    ).order_by(Product.created_at.desc()).limit(5).all()
    recent_rooms = Product.query.filter(
        Product.hostel_name != '',
        Product.hostel_name.isnot(None)
    ).order_by(Product.created_at.desc()).limit(5).all()
    recent_transactions = ProductUnlock.query.filter_by(status='completed').order_by(ProductUnlock.completed_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_rooms=total_rooms,
                         active_products=active_products,
                         total_revenue=total_revenue,
                         recent_users=recent_users,
                         recent_products=recent_products,
                         recent_rooms=recent_rooms,
                         recent_transactions=recent_transactions)

# ============================================
# USER MANAGEMENT (with logging)
# ============================================
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """View user details"""
    user = User.query.get_or_404(user_id)
    
    products_count = Product.query.filter_by(seller_id=user_id).count()
    active_products = Product.query.filter_by(seller_id=user_id, is_active=True, is_sold=False).count()
    total_spent = db.session.query(func.sum(ProductUnlock.amount)).filter(
        ProductUnlock.user_id == user_id,
        ProductUnlock.status == 'completed'
    ).scalar() or 0
    total_earned = db.session.query(func.sum(ProductUnlock.amount)).filter(
        ProductUnlock.seller_id == user_id,
        ProductUnlock.status == 'completed'
    ).scalar() or 0
    
    recent_products = Product.query.filter_by(seller_id=user_id).order_by(Product.created_at.desc()).limit(5).all()
    recent_purchases = ProductUnlock.query.filter_by(user_id=user_id, status='completed').order_by(ProductUnlock.completed_at.desc()).limit(5).all()
    
    return render_template('admin/user_detail.html',
                         user=user,
                         products_count=products_count,
                         active_products=active_products,
                         total_spent=total_spent,
                         total_earned=total_earned,
                         recent_products=recent_products,
                         recent_purchases=recent_purchases)

@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
@log_admin_action('toggle_admin', 'user', target_id='user_id')
def toggle_admin(user_id):
    """Toggle admin status for a user"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot change your own admin status.', 'error')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    old_status = user.is_admin
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = "granted" if user.is_admin else "revoked"
    flash(f'Admin privileges {status} for {user.username}.', 'success')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
@log_admin_action('delete_user', 'user', target_id='user_id')
def delete_user(user_id):
    """Delete a user and all their data"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own admin account.', 'error')
        return redirect(url_for('admin.users'))
    
    username = user.username
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {username} has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('admin.users'))

# ============================================
# PRODUCT MANAGEMENT (with logging)
# ============================================
@admin_bp.route('/products')
@login_required
@admin_required
def products():
    """List all products (excluding rooms)"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', 'all')
    
    query = Product.query.filter(
        (Product.hostel_name == '') | (Product.hostel_name.is_(None))
    )
    
    if search:
        query = query.filter(
            (Product.title.ilike(f'%{search}%')) |
            (Product.description.ilike(f'%{search}%'))
        )
    
    if status == 'active':
        query = query.filter(Product.is_active == True, Product.is_sold == False)
    elif status == 'sold':
        query = query.filter(Product.is_sold == True)
    elif status == 'inactive':
        query = query.filter(Product.is_active == False)
    
    products = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/products.html', products=products, search=search, status=status)

@admin_bp.route('/products/<int:product_id>/toggle-sold', methods=['POST'])
@login_required
@admin_required
@log_admin_action('toggle_product_sold', 'product', target_id='product_id')
def toggle_product_sold(product_id):
    """Toggle product sold status"""
    product = Product.query.get_or_404(product_id)
    
    product.is_sold = not product.is_sold
    db.session.commit()
    
    status = "marked as sold" if product.is_sold else "marked as available"
    flash(f'Product "{product.title}" {status}.', 'success')
    
    return redirect(url_for('admin.products'))

@admin_bp.route('/products/<int:product_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
@log_admin_action('toggle_product_active', 'product', target_id='product_id')
def toggle_product_active(product_id):
    """Toggle product active status"""
    product = Product.query.get_or_404(product_id)
    
    product.is_active = not product.is_active
    db.session.commit()
    
    status = "activated" if product.is_active else "deactivated"
    flash(f'Product "{product.title}" {status}.', 'success')
    
    return redirect(url_for('admin.products'))

@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
@log_admin_action('delete_product', 'product', target_id='product_id')
def delete_product(product_id):
    """Delete a product"""
    product = Product.query.get_or_404(product_id)
    title = product.title
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash(f'Product "{title}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')
    
    return redirect(url_for('admin.products'))

# ============================================
# ROOM MANAGEMENT (with logging)
# ============================================
@admin_bp.route('/rooms')
@login_required
@admin_required
def rooms():
    """List all room listings"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', 'all')
    location = request.args.get('location', '')
    
    query = Product.query.filter(
        Product.hostel_name != '',
        Product.hostel_name.isnot(None)
    )
    
    if search:
        query = query.filter(
            (Product.title.ilike(f'%{search}%')) |
            (Product.hostel_name.ilike(f'%{search}%')) |
            (Product.location.ilike(f'%{search}%'))
        )
    
    if location:
        query = query.filter(Product.location.ilike(f'%{location}%'))
    
    if status == 'available':
        query = query.filter(Product.status == 'available', Product.is_active == True)
    elif status == 'pending':
        query = query.filter(Product.status == 'pending')
    elif status == 'booked':
        query = query.filter(Product.status == 'booked')
    elif status == 'expired':
        query = query.filter(Product.status == 'expired')
    elif status == 'inactive':
        query = query.filter(Product.is_active == False)
    
    rooms = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    locations = db.session.query(Product.location).filter(
        Product.hostel_name != '',
        Product.location != ''
    ).distinct().all()
    locations = [loc[0] for loc in locations if loc[0]]
    
    return render_template('admin/rooms.html', rooms=rooms, search=search, status=status, location=location, locations=locations)

@admin_bp.route('/rooms/<int:room_id>')
@login_required
@admin_required
def room_detail(room_id):
    """View room details"""
    room = Product.query.get_or_404(room_id)
    
    if not room.hostel_name:
        flash('This is not a room listing.', 'error')
        return redirect(url_for('admin.rooms'))
    
    unlocks = ProductUnlock.query.filter_by(product_id=room_id, status='completed').order_by(ProductUnlock.created_at.desc()).all()
    offers = Offer.query.filter_by(product_id=room_id).order_by(Offer.created_at.desc()).all()
    
    return render_template('admin/room_detail.html', room=room, unlocks=unlocks, offers=offers)

@admin_bp.route('/rooms/<int:room_id>/update-status', methods=['POST'])
@login_required
@admin_required
@log_admin_action('update_room_status', 'room', target_id='room_id')
def update_room_status(room_id):
    """Update room status"""
    room = Product.query.get_or_404(room_id)
    new_status = request.form.get('status')
    
    valid_statuses = ['available', 'pending', 'booked', 'expired']
    
    if new_status not in valid_statuses:
        flash('Invalid status.', 'error')
        return redirect(url_for('admin.room_detail', room_id=room_id))
    
    room.status = new_status
    
    if new_status == 'booked':
        room.is_sold = True
        room.booked_at = datetime.utcnow()
    elif new_status == 'available':
        room.is_sold = False
        room.agreement_user_id = None
        room.agreement_expires_at = None
    
    db.session.commit()
    
    flash(f'Room status updated to {new_status}.', 'success')
    return redirect(url_for('admin.room_detail', room_id=room_id))

@admin_bp.route('/rooms/<int:room_id>/delete', methods=['POST'])
@login_required
@admin_required
@log_admin_action('delete_room', 'room', target_id='room_id')
def delete_room(room_id):
    """Delete a room listing"""
    room = Product.query.get_or_404(room_id)
    title = room.title
    
    try:
        db.session.delete(room)
        db.session.commit()
        flash(f'Room "{title}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting room: {str(e)}', 'error')
    
    return redirect(url_for('admin.rooms'))

# ============================================
# TRANSACTION MANAGEMENT
# ============================================
@admin_bp.route('/transactions')
@login_required
@admin_required
def transactions():
    """List all transactions"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = ProductUnlock.query
    
    if status_filter != 'all':
        query = query.filter(ProductUnlock.status == status_filter)
    
    transactions = query.order_by(ProductUnlock.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    total_revenue = db.session.query(func.sum(ProductUnlock.amount)).filter_by(status='completed').scalar() or 0
    pending_count = ProductUnlock.query.filter_by(status='pending').count()
    completed_count = ProductUnlock.query.filter_by(status='completed').count()
    failed_count = ProductUnlock.query.filter_by(status='failed').count()
    
    return render_template('admin/transactions.html',
                         transactions=transactions,
                         status_filter=status_filter,
                         total_revenue=total_revenue,
                         pending_count=pending_count,
                         completed_count=completed_count,
                         failed_count=failed_count)

# ============================================
# CATEGORY MANAGEMENT (with logging)
# ============================================
@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    """List all categories"""
    categories = Category.query.order_by(Category.name).all()
    
    for category in categories:
        category.product_count = Product.query.filter_by(category_id=category.id).count()
    
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    """Create a new category"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Category name is required.', 'error')
            return redirect(url_for('admin.create_category'))
        
        existing = Category.query.filter_by(name=name).first()
        if existing:
            flash(f'Category "{name}" already exists.', 'error')
            return redirect(url_for('admin.create_category'))
        
        category = Category(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        
        # Log category creation
        log = AdminLog(
            admin_id=current_user.id,
            admin_username=current_user.username,
            action='create_category',
            target_type='category',
            target_id=category.id,
            target_name=name,
            ip_address=request.remote_addr or 'unknown'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Category "{name}" created successfully.', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html', title='Create Category', category=None)

@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    """Edit a category"""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Category name is required.', 'error')
            return redirect(url_for('admin.edit_category', category_id=category_id))
        
        existing = Category.query.filter(Category.name == name, Category.id != category_id).first()
        if existing:
            flash(f'Category "{name}" already exists.', 'error')
            return redirect(url_for('admin.edit_category', category_id=category_id))
        
        old_name = category.name
        category.name = name
        category.description = description
        db.session.commit()
        
        # Log category edit
        log = AdminLog(
            admin_id=current_user.id,
            admin_username=current_user.username,
            action='edit_category',
            target_type='category',
            target_id=category.id,
            target_name=f"{old_name} -> {name}",
            ip_address=request.remote_addr or 'unknown'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Category "{name}" updated successfully.', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html', title='Edit Category', category=category)

@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """Delete a category"""
    category = Category.query.get_or_404(category_id)
    
    product_count = Product.query.filter_by(category_id=category_id).count()
    
    if product_count > 0:
        flash(f'Cannot delete "{category.name}" - it has {product_count} products assigned.', 'error')
        return redirect(url_for('admin.categories'))
    
    name = category.name
    db.session.delete(category)
    db.session.commit()
    
    # Log category deletion
    log = AdminLog(
        admin_id=current_user.id,
        admin_username=current_user.username,
        action='delete_category',
        target_type='category',
        target_id=category_id,
        target_name=name,
        ip_address=request.remote_addr or 'unknown'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'Category "{name}" deleted successfully.', 'success')
    return redirect(url_for('admin.categories'))

# ============================================
# ADMIN ACTIVITY LOGS
# ============================================
@admin_bp.route('/admin-logs')
@login_required
@admin_required
def admin_logs():
    """View admin activity logs"""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    admin_filter = request.args.get('admin', '')
    
    query = AdminLog.query
    
    if action_filter:
        query = query.filter(AdminLog.action == action_filter)
    
    if admin_filter:
        query = query.filter(AdminLog.admin_username == admin_filter)
    
    logs = query.order_by(AdminLog.created_at.desc()).paginate(page=page, per_page=50, error_out=False)
    
    # Get unique actions and admins for filters
    actions = db.session.query(AdminLog.action).distinct().all()
    actions = [a[0] for a in actions]
    admins = db.session.query(AdminLog.admin_username).distinct().all()
    admins = [a[0] for a in admins]
    
    return render_template('admin/admin_logs.html', 
                         logs=logs, 
                         actions=actions, 
                         admins=admins,
                         action_filter=action_filter,
                         admin_filter=admin_filter)

# ============================================
# SYSTEM HEALTH
# ============================================
@admin_bp.route('/system-health')
@login_required
@admin_required
def system_health():
    """System health dashboard"""
    # Database info
    db_path = 'instance/marketplace.db'
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    
    # Alternative database location
    alt_db_path = 'marketplace.db'
    alt_db_size = os.path.getsize(alt_db_path) if os.path.exists(alt_db_path) else 0
    
    # Storage info
    uploads_path = 'app/static/uploads'
    uploads_size = 0
    product_images_size = 0
    chat_images_size = 0
    product_image_count = 0
    chat_image_count = 0
    
    if os.path.exists(uploads_path):
        for root, dirs, files in os.walk(uploads_path):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(filepath)
                    uploads_size += file_size
                    if 'product_images' in root:
                        product_images_size += file_size
                        product_image_count += 1
                    elif 'chat_images' in root:
                        chat_images_size += file_size
                        chat_image_count += 1
                except:
                    pass
    
    # Database counts
    total_users = User.query.count()
    total_products = Product.query.filter((Product.hostel_name == '') | (Product.hostel_name.is_(None))).count()
    total_rooms = Product.query.filter(Product.hostel_name != '', Product.hostel_name.isnot(None)).count()
    total_transactions = ProductUnlock.query.count()
    total_admins = User.query.filter_by(is_admin=True).count()
    total_logs = AdminLog.query.count()
    
    # Disk space
    disk_usage = psutil.disk_usage('.')
    
    # Recent errors (check for 500 errors in logs)
    error_count = 0
    if os.path.exists('logs'):
        try:
            import glob
            log_files = glob.glob('logs/*.log')
            for log_file in log_files:
                with open(log_file, 'r') as f:
                    content = f.read()
                    error_count += content.count('ERROR')
        except:
            pass
    
    return render_template('admin/system_health.html',
                         db_size=db_size,
                         alt_db_size=alt_db_size,
                         uploads_size=uploads_size,
                         product_images_size=product_images_size,
                         chat_images_size=chat_images_size,
                         product_image_count=product_image_count,
                         chat_image_count=chat_image_count,
                         total_users=total_users,
                         total_products=total_products,
                         total_rooms=total_rooms,
                         total_transactions=total_transactions,
                         total_admins=total_admins,
                         total_logs=total_logs,
                         disk_usage=disk_usage,
                         error_count=error_count)

# ============================================
# ANNOUNCEMENT MANAGEMENT - Redirect to existing blueprint
# ============================================
@admin_bp.route('/announcements')
@login_required
@admin_required
def announcements():
    """Redirect to announcements admin page"""
    return redirect(url_for('announcements.admin'))

@admin_bp.route('/announcements/create')
@login_required
@admin_required
def create_announcement():
    """Redirect to create announcement page"""
    return redirect(url_for('announcements.admin_create'))

@admin_bp.route('/announcements/edit/<int:announcement_id>')
@login_required
@admin_required
def edit_announcement(announcement_id):
    """Redirect to edit announcement page"""
    return redirect(url_for('announcements.admin_edit', announcement_id=announcement_id))

# ============================================
# API ENDPOINTS
# ============================================
@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API endpoint for dashboard statistics"""
    today = datetime.utcnow().date()
    
    today_users = User.query.filter(func.date(User.created_at) == today).count()
    today_products = Product.query.filter(func.date(Product.created_at) == today).count()
    today_revenue = db.session.query(func.sum(ProductUnlock.amount)).filter(
        func.date(ProductUnlock.completed_at) == today,
        ProductUnlock.status == 'completed'
    ).scalar() or 0
    
    seven_days_ago = today - timedelta(days=7)
    daily_stats = []
    
    for i in range(7):
        day = today - timedelta(days=i)
        day_start = day
        day_end = day + timedelta(days=1)
        
        users_count = User.query.filter(
            User.created_at >= day_start,
            User.created_at < day_end
        ).count()
        
        products_count = Product.query.filter(
            Product.created_at >= day_start,
            Product.created_at < day_end
        ).count()
        
        revenue = db.session.query(func.sum(ProductUnlock.amount)).filter(
            ProductUnlock.completed_at >= day_start,
            ProductUnlock.completed_at < day_end,
            ProductUnlock.status == 'completed'
        ).scalar() or 0
        
        daily_stats.append({
            'date': day.strftime('%Y-%m-%d'),
            'users': users_count,
            'products': products_count,
            'revenue': float(revenue)
        })
    
    return jsonify({
        'total_users': User.query.count(),
        'total_products': Product.query.filter(
            (Product.hostel_name == '') | (Product.hostel_name.is_(None))
        ).count(),
        'total_rooms': Product.query.filter(
            Product.hostel_name != '',
            Product.hostel_name.isnot(None)
        ).count(),
        'active_products': Product.query.filter_by(is_active=True, is_sold=False).count(),
        'total_revenue': float(db.session.query(func.sum(ProductUnlock.amount)).filter_by(status='completed').scalar() or 0),
        'today_users': today_users,
        'today_products': today_products,
        'today_revenue': float(today_revenue),
        'daily_stats': daily_stats[::-1]
    })

# ============================================
# SYSTEM CLEANUP TOOLS
# ============================================
@admin_bp.route('/cleanup-orphaned-images', methods=['POST'])
@login_required
@admin_required
@log_admin_action('cleanup_orphaned_images', 'system', target_name='orphaned_images')
def cleanup_orphaned_images():
    """Delete image files that aren't linked to any product or room"""
    import os
    
    deleted_count = 0
    freed_space = 0
    errors = []
    
    # Check product_images folder
    product_images_dir = 'app/static/uploads/product_images/'
    
    # Get all valid image filenames from database (products and rooms)
    valid_images = set()
    all_images = ProductImage.query.all()
    for img in all_images:
        valid_images.add(img.filename)
    
    # Also check if any images are referenced by products directly (legacy)
    
    # Scan and delete orphaned files in product_images
    if os.path.exists(product_images_dir):
        for file in os.listdir(product_images_dir):
            if file not in valid_images:
                filepath = os.path.join(product_images_dir, file)
                try:
                    if os.path.isfile(filepath):
                        size = os.path.getsize(filepath)
                        os.remove(filepath)
                        deleted_count += 1
                        freed_space += size
                        print(f"Deleted orphaned: {file}")
                except Exception as e:
                    errors.append(f"Failed to delete {file}: {str(e)}")
    
    # Check chat_images folder (these might be orphaned too)
    chat_images_dir = 'app/static/uploads/chat_images/'
    if os.path.exists(chat_images_dir):
        # For chat images, we need to check if they're referenced in messages
        from app.models import Message
        valid_chat_images = set()
        messages_with_images = Message.query.filter(Message.is_image == True, Message.image_filename.isnot(None)).all()
        for msg in messages_with_images:
            if msg.image_filename:
                valid_chat_images.add(msg.image_filename)
        
        for file in os.listdir(chat_images_dir):
            if file not in valid_chat_images:
                filepath = os.path.join(chat_images_dir, file)
                try:
                    if os.path.isfile(filepath):
                        size = os.path.getsize(filepath)
                        os.remove(filepath)
                        deleted_count += 1
                        freed_space += size
                        print(f"Deleted orphaned chat image: {file}")
                except Exception as e:
                    errors.append(f"Failed to delete chat image {file}: {str(e)}")
    
    if deleted_count > 0:
        flash(f'🧹 Cleaned up {deleted_count} orphaned images, freed {freed_space / 1024 / 1024:.2f} MB', 'success')
    else:
        flash('✅ No orphaned images found. All files are clean!', 'success')
    
    if errors:
        for error in errors[:5]:  # Show first 5 errors
            flash(f'⚠️ {error}', 'warning')
    
    return redirect(url_for('admin.system_health'))

@admin_bp.route('/analyze-storage', methods=['GET'])
@login_required
@admin_required
def analyze_storage():
    """Analyze storage usage and return JSON for detailed view"""
    import os
    from collections import defaultdict
    
    result = {
        'product_images': {'count': 0, 'size': 0, 'orphaned': 0, 'orphaned_size': 0},
        'chat_images': {'count': 0, 'size': 0, 'orphaned': 0, 'orphaned_size': 0},
        'largest_files': []
    }
    
    # Get valid product images from database
    valid_product_images = set()
    all_images = ProductImage.query.all()
    for img in all_images:
        valid_product_images.add(img.filename)
    
    # Check product_images folder
    product_images_dir = 'app/static/uploads/product_images/'
    if os.path.exists(product_images_dir):
        for file in os.listdir(product_images_dir):
            filepath = os.path.join(product_images_dir, file)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                result['product_images']['count'] += 1
                result['product_images']['size'] += size
                
                if file not in valid_product_images:
                    result['product_images']['orphaned'] += 1
                    result['product_images']['orphaned_size'] += size
                
                # Track largest files
                result['largest_files'].append({
                    'name': file,
                    'size': size,
                    'type': 'product_image',
                    'orphaned': file not in valid_product_images
                })
    
    # Check chat_images folder
    chat_images_dir = 'app/static/uploads/chat_images/'
    if os.path.exists(chat_images_dir):
        from app.models import Message
        valid_chat_images = set()
        messages_with_images = Message.query.filter(Message.is_image == True, Message.image_filename.isnot(None)).all()
        for msg in messages_with_images:
            if msg.image_filename:
                valid_chat_images.add(msg.image_filename)
        
        for file in os.listdir(chat_images_dir):
            filepath = os.path.join(chat_images_dir, file)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                result['chat_images']['count'] += 1
                result['chat_images']['size'] += size
                
                if file not in valid_chat_images:
                    result['chat_images']['orphaned'] += 1
                    result['chat_images']['orphaned_size'] += size
                
                result['largest_files'].append({
                    'name': file,
                    'size': size,
                    'type': 'chat_image',
                    'orphaned': file not in valid_chat_images
                })
    
    # Sort largest files
    result['largest_files'].sort(key=lambda x: x['size'], reverse=True)
    result['largest_files'] = result['largest_files'][:20]  # Top 20
    
    return jsonify(result)
