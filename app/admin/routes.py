from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Product, Category, ProductUnlock, Notification, Offer
from datetime import datetime, timedelta
from sqlalchemy import func
from . import admin_bp

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
# USER MANAGEMENT
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
def toggle_admin(user_id):
    """Toggle admin status for a user"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot change your own admin status.', 'error')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = "granted" if user.is_admin else "revoked"
    flash(f'Admin privileges {status} for {user.username}.', 'success')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
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
# PRODUCT MANAGEMENT (Regular products only)
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
# ROOM MANAGEMENT
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
# CATEGORY MANAGEMENT
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
        
        category.name = name
        category.description = description
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
    
    flash(f'Category "{name}" deleted successfully.', 'success')
    return redirect(url_for('admin.categories'))

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
