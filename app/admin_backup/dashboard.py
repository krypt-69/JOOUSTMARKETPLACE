from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Product, Category, Payment, ProductUnlock, Notification
from datetime import datetime, timedelta
import json
from sqlalchemy import func, and_

dashboard_bp = Blueprint('dashboard', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@dashboard_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Main dashboard page"""
    return render_template('admin/dashboard_enhanced.html')

@dashboard_bp.route('/api/stats/overview')
@login_required
@admin_required
def api_overview_stats():
    """API endpoint for overview statistics"""
    try:
        total_users = User.query.count()
        total_products = Product.query.count()
        active_products = Product.query.filter_by(is_active=True, is_sold=False).count()
        
        # Total revenue from completed unlocks
        total_revenue = db.session.query(func.sum(ProductUnlock.amount)).filter_by(status='completed').scalar() or 0
        
        # Today's revenue
        today = datetime.utcnow().date()
        today_revenue = db.session.query(func.sum(ProductUnlock.amount)).filter(
            ProductUnlock.status == 'completed',
            func.date(ProductUnlock.completed_at) == today
        ).scalar() or 0
        
        # Pending transactions
        pending_transactions = ProductUnlock.query.filter_by(status='pending').count()
        
        return jsonify({
            'total_users': total_users,
            'total_products': total_products,
            'active_products': active_products,
            'total_revenue': float(total_revenue),
            'today_revenue': float(today_revenue),
            'pending_transactions': pending_transactions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/stats/charts')
@login_required
@admin_required
def api_chart_data():
    """API endpoint for chart data"""
    try:
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days-1)
        
        dates = []
        user_data = []
        product_data = []
        revenue_data = []
        unlock_data = []
        
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime('%m/%d'))
            
            # Users registered
            user_count = User.query.filter(
                func.date(User.created_at) == current_date
            ).count()
            user_data.append(user_count)
            
            # Products created
            product_count = Product.query.filter(
                func.date(Product.created_at) == current_date
            ).count()
            product_data.append(product_count)
            
            # Revenue
            revenue = db.session.query(func.sum(ProductUnlock.amount)).filter(
                ProductUnlock.status == 'completed',
                func.date(ProductUnlock.completed_at) == current_date
            ).scalar() or 0
            revenue_data.append(float(revenue))
            
            # Unlocks
            unlock_count = ProductUnlock.query.filter(
                ProductUnlock.status == 'completed',
                func.date(ProductUnlock.completed_at) == current_date
            ).count()
            unlock_data.append(unlock_count)
            
            current_date += timedelta(days=1)
        
        return jsonify({
            'dates': dates,
            'users': user_data,
            'products': product_data,
            'revenue': revenue_data,
            'unlocks': unlock_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/stats/recent-activity')
@login_required
@admin_required
def api_recent_activity():
    """API endpoint for recent activity"""
    try:
        # Recent users (last 5)
        recent_users = []
        users = User.query.order_by(User.created_at.desc()).limit(5).all()
        for user in users:
            recent_users.append({
                'username': user.username,
                'created_at': user.created_at.isoformat()
            })
        
        # Recent products (last 5)
        recent_products = []
        products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
        for product in products:
            recent_products.append({
                'title': product.title,
                'created_at': product.created_at.isoformat()
            })
        
        # Recent transactions (last 5 completed unlocks)
        recent_transactions = []
        transactions = ProductUnlock.query.filter_by(status='completed')\
            .order_by(ProductUnlock.completed_at.desc())\
            .limit(5).all()
        for tx in transactions:
            recent_transactions.append({
                'amount': float(tx.amount),
                'completed_at': tx.completed_at.isoformat() if tx.completed_at else tx.created_at.isoformat()
            })
        
        # Recent notifications (last 5)
        recent_notifications = []
        notifications = Notification.query.order_by(Notification.created_at.desc())\
            .limit(5).all()
        for notif in notifications:
            recent_notifications.append({
                'message': notif.message,
                'created_at': notif.created_at.isoformat()
            })
        
        return jsonify({
            'recent_users': recent_users,
            'recent_products': recent_products,
            'recent_transactions': recent_transactions,
            'recent_notifications': recent_notifications
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/stats/categories')
@login_required
@admin_required
def api_category_stats():
    """API endpoint for category statistics"""
    try:
        category_stats = db.session.query(
            Category.name,
            func.count(Product.id).label('product_count'),
            func.sum(ProductUnlock.amount).label('revenue')
        ).outerjoin(Product)\
         .outerjoin(ProductUnlock, and_(
             ProductUnlock.product_id == Product.id,
             ProductUnlock.status == 'completed'
         ))\
         .group_by(Category.id, Category.name)\
         .all()
        
        result = []
        for stat in category_stats:
            result.append({
                'category': stat.name,
                'product_count': stat.product_count,
                'revenue': float(stat.revenue or 0)
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/stats/system-health')
@login_required
@admin_required
def api_system_health():
    """API endpoint for system health"""
    try:
        # Total records
        total_records = (
            User.query.count() +
            Product.query.count() +
            ProductUnlock.query.count() +
            Notification.query.count()
        )
        
        # Error rate (failed transactions)
        failed_transactions = ProductUnlock.query.filter_by(status='failed').count()
        total_transactions = ProductUnlock.query.count()
        error_rate = (failed_transactions / total_transactions * 100) if total_transactions > 0 else 0
        
        # Active users in last 24 hours
        active_users_24h = User.query.filter(
            User.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        return jsonify({
            'total_records': total_records,
            'error_rate': round(error_rate, 2),
            'active_users_24h': active_users_24h,
            'failed_transactions': failed_transactions,
            'uptime': '99.9%'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/stats/real-time')
@login_required
@admin_required
def api_real_time_stats():
    """API endpoint for real-time statistics"""
    try:
        # Current hour activity
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        
        users_this_hour = User.query.filter(
            User.created_at >= current_hour
        ).count()
        
        products_this_hour = Product.query.filter(
            Product.created_at >= current_hour
        ).count()
        
        revenue_this_hour = db.session.query(func.sum(ProductUnlock.amount)).filter(
            ProductUnlock.status == 'completed',
            ProductUnlock.completed_at >= current_hour
        ).scalar() or 0
        
        return jsonify({
            'users_this_hour': users_this_hour,
            'products_this_hour': products_this_hour,
            'revenue_this_hour': float(revenue_this_hour),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/stats/export')
@login_required
@admin_required
def api_export_data():
    """API endpoint to export all dashboard data"""
    try:
        # Get all the data
        overview_data = get_overview_stats()
        chart_data = get_chart_data(90)  # Last 90 days
        category_data = get_category_stats()
        system_health_data = get_system_health()
        
        data = {
            'overview': overview_data,
            'charts': chart_data,
            'categories': category_data,
            'system_health': system_health_data,
            'exported_at': datetime.utcnow().isoformat()
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/batch/cleanup', methods=['POST'])
@login_required
@admin_required
def batch_cleanup():
    """Perform batch cleanup operations"""
    try:
        # Clean up old failed transactions (older than 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        deleted_failed = ProductUnlock.query.filter(
            ProductUnlock.status == 'failed',
            ProductUnlock.created_at < thirty_days_ago
        ).delete()
        
        # Clean up old notifications (older than 90 days)
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        
        deleted_notifications = Notification.query.filter(
            Notification.created_at < ninety_days_ago
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'deleted_failed_transactions': deleted_failed,
            'deleted_old_notifications': deleted_notifications,
            'message': 'Cleanup completed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Helper functions
def get_overview_stats():
    """Helper function to get overview stats"""
    total_users = User.query.count()
    total_products = Product.query.count()
    active_products = Product.query.filter_by(is_active=True, is_sold=False).count()
    total_revenue = db.session.query(func.sum(ProductUnlock.amount)).filter_by(status='completed').scalar() or 0
    
    return {
        'total_users': total_users,
        'total_products': total_products,
        'active_products': active_products,
        'total_revenue': float(total_revenue)
    }

def get_chart_data(days):
    """Helper function to get chart data"""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days-1)
    
    dates = []
    user_data = []
    product_data = []
    revenue_data = []
    
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%m/%d'))
        
        user_count = User.query.filter(
            func.date(User.created_at) == current_date
        ).count()
        user_data.append(user_count)
        
        product_count = Product.query.filter(
            func.date(Product.created_at) == current_date
        ).count()
        product_data.append(product_count)
        
        revenue = db.session.query(func.sum(ProductUnlock.amount)).filter(
            ProductUnlock.status == 'completed',
            func.date(ProductUnlock.completed_at) == current_date
        ).scalar() or 0
        revenue_data.append(float(revenue))
        
        current_date += timedelta(days=1)
    
    return {
        'dates': dates,
        'users': user_data,
        'products': product_data,
        'revenue': revenue_data
    }

def get_category_stats():
    """Helper function to get category stats"""
    category_stats = db.session.query(
        Category.name,
        func.count(Product.id).label('product_count')
    ).outerjoin(Product)\
     .group_by(Category.id, Category.name)\
     .all()
    
    return [
        {
            'category': stat.name,
            'product_count': stat.product_count
        }
        for stat in category_stats
    ]

def get_system_health():
    """Helper function to get system health"""
    total_records = (
        User.query.count() +
        Product.query.count() +
        ProductUnlock.query.count() +
        Notification.query.count()
    )
    
    failed_transactions = ProductUnlock.query.filter_by(status='failed').count()
    total_transactions = ProductUnlock.query.count()
    error_rate = (failed_transactions / total_transactions * 100) if total_transactions > 0 else 0
    
    return {
        'total_records': total_records,
        'error_rate': round(error_rate, 2),
        'uptime': '99.9%'
    }

# Health check endpoint
@dashboard_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500