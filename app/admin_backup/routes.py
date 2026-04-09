from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import User, Product, Category, Payment, ProductUnlock, Notification
from datetime import datetime, timedelta
import json
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin access"""
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if (not current_user.is_authenticated or 
            not current_user.is_admin):
            
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Redirect to the new dashboard"""
    return redirect(url_for('dashboard.dashboard'))

@admin_bp.route('/users')
@login_required
@admin_required
def users_management():
    """User Management"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """User Detail View"""
    user = User.query.get_or_404(user_id)
    
    # Get user stats
    products_count = Product.query.filter_by(seller_id=user_id).count()
    active_products = Product.query.filter_by(seller_id=user_id, is_active=True, is_sold=False).count()
    total_revenue = db.session.query(db.func.sum(ProductUnlock.amount)).filter(
        ProductUnlock.seller_id == user_id,
        ProductUnlock.status == 'completed'
    ).scalar() or 0
    
    recent_products = Product.query.filter_by(seller_id=user_id).order_by(Product.created_at.desc()).limit(5).all()
    recent_unlocks = ProductUnlock.query.filter_by(seller_id=user_id, status='completed').order_by(ProductUnlock.completed_at.desc()).limit(5).all()
    
    return render_template('admin/user_detail.html',
                         user=user,
                         products_count=products_count,
                         active_products=active_products,
                         total_revenue=total_revenue,
                         recent_products=recent_products,
                         recent_unlocks=recent_unlocks)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)
    
    # You might want to add an 'is_active' field to your User model
    # For now, we'll just flash a message
    flash(f'User status toggle would happen here for {user.username}', 'info')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/products')
@login_required
@admin_required
def products_management():
    """Product Management"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', 'all')
    
    query = Product.query.join(User).join(Category)
    
    if search:
        query = query.filter(
            (Product.title.ilike(f'%{search}%')) |
            (User.username.ilike(f'%{search}%'))
        )
    
    if status == 'active':
        query = query.filter(Product.is_active == True, Product.is_sold == False)
    elif status == 'sold':
        query = query.filter(Product.is_sold == True)
    elif status == 'inactive':
        query = query.filter(Product.is_active == False)
    
    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/products.html', products=products, search=search, status=status)

@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product_admin(product_id):
    """Admin product deletion"""
    product = Product.query.get_or_404(product_id)
    
    try:
        # Get product title for flash message
        product_title = product.title
        
        # Delete associated payments and unlocks
        Payment.query.filter_by(product_id=product_id).delete()
        ProductUnlock.query.filter_by(product_id=product_id).delete()
        Notification.query.filter_by(product_id=product_id).delete()
        
        # Delete the product
        db.session.delete(product)
        db.session.commit()
        
        flash(f'Product "{product_title}" has been deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error deleting product. Please try again.', 'error')
    
    return redirect(url_for('admin.products_management'))

@admin_bp.route('/products/<int:product_id>/toggle-sold', methods=['POST'])
@login_required
@admin_required
def toggle_product_sold(product_id):
    """Toggle product sold status"""
    product = Product.query.get_or_404(product_id)
    
    product.is_sold = not product.is_sold
    db.session.commit()
    
    status = "sold" if product.is_sold else "available"
    flash(f'Product marked as {status}.', 'success')
    
    return redirect(url_for('admin.products_management'))

@admin_bp.route('/transactions')
@login_required
@admin_required
def transactions_management():
    """Transaction Management"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    query = ProductUnlock.query.join(Product).join(User, ProductUnlock.user_id == User.id)
    
    if status != 'all':
        query = query.filter(ProductUnlock.status == status)
    
    transactions = query.order_by(ProductUnlock.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Stats
    total_revenue = db.session.query(db.func.sum(ProductUnlock.amount)).filter_by(status='completed').scalar() or 0
    pending_count = ProductUnlock.query.filter_by(status='pending').count()
    completed_count = ProductUnlock.query.filter_by(status='completed').count()
    failed_count = ProductUnlock.query.filter_by(status='failed').count()
    
    return render_template('admin/transactions.html',
                         transactions=transactions,
                         status=status,
                         total_revenue=total_revenue,
                         pending_count=pending_count,
                         completed_count=completed_count,
                         failed_count=failed_count)

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Advanced Analytics"""
    # User growth over time
    user_growth = db.session.query(
        db.func.date(User.created_at).label('date'),
        db.func.count(User.id).label('count')
    ).group_by(db.func.date(User.created_at)).order_by('date').all()
    
    # Product categories distribution
    categories_data = db.session.query(
        Category.name,
        db.func.count(Product.id).label('count')
    ).join(Product).group_by(Category.name).all()
    
    # Revenue by day
    revenue_by_day = db.session.query(
        db.func.date(ProductUnlock.completed_at).label('date'),
        db.func.sum(ProductUnlock.amount).label('revenue')
    ).filter(
        ProductUnlock.status == 'completed',
        ProductUnlock.completed_at.isnot(None)
    ).group_by(db.func.date(ProductUnlock.completed_at)).order_by('date').all()
    
    # Top products by unlocks
    top_products = db.session.query(
        Product.title,
        User.username,
        db.func.count(ProductUnlock.id).label('unlock_count'),
        db.func.sum(ProductUnlock.amount).label('revenue')
    ).join(ProductUnlock).join(User).filter(
        ProductUnlock.status == 'completed'
    ).group_by(Product.id, Product.title, User.username).order_by(
        db.func.count(ProductUnlock.id).desc()
    ).limit(10).all()
    
    return render_template('admin/analytics.html',
                         user_growth=user_growth,
                         categories_data=categories_data,
                         revenue_by_day=revenue_by_day,
                         top_products=top_products)

@admin_bp.route('/api/dashboard-stats')
@login_required
@admin_required
def dashboard_stats():
    """API endpoint for real-time dashboard stats"""
    # Real-time counts
    online_users = User.query.count()  # You might want to implement online tracking
    
    today = datetime.utcnow().date()
    today_users = User.query.filter(db.func.date(User.created_at) == today).count()
    today_products = Product.query.filter(db.func.date(Product.created_at) == today).count()
    today_revenue = db.session.query(db.func.sum(ProductUnlock.amount)).filter(
        db.func.date(ProductUnlock.completed_at) == today,
        ProductUnlock.status == 'completed'
    ).scalar() or 0
    
    return jsonify({
        'online_users': online_users,
        'today_users': today_users,
        'today_products': today_products,
        'today_revenue': float(today_revenue)
    })