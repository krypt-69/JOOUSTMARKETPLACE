from flask import render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.announcements import announcements_bp
from app.models import Announcement, Reaction
from datetime import datetime

@announcements_bp.route('/')
def index():
    """Main announcements page - visible to all users"""
    # Get all announcements: pinned first, then newest to oldest
    pinned = Announcement.query.filter_by(is_pinned=True).first()
    others = Announcement.query.filter_by(is_pinned=False).order_by(Announcement.created_at.desc()).all()
    
    announcements = []
    if pinned:
        announcements.append(pinned)
    announcements.extend(others)
    
    return render_template('announcements/index.html', announcements=announcements)

@announcements_bp.route('/api/announcements')
def api_get_announcements():
    """API endpoint to get announcements data"""
    pinned = Announcement.query.filter_by(is_pinned=True).first()
    others = Announcement.query.filter_by(is_pinned=False).order_by(Announcement.created_at.desc()).all()
    
    announcements = []
    if pinned:
        announcements.append(pinned)
    announcements.extend(others)
    
    announcements_data = []
    for ann in announcements:
        announcements_data.append({
            'id': ann.id,
            'title': ann.title,
            'content_preview': ann.content_preview,
            'content_full': ann.content_full,
            'message_type': ann.message_type,
            'status': ann.status,
            'is_pinned': ann.is_pinned,
            'author_name': ann.author_name,
            'created_at': ann.created_at.isoformat(),
            'updated_at': ann.updated_at.isoformat() if ann.updated_at else None,
            'reaction_counts': ann.reaction_counts,
            'user_reaction': ann.get_user_reaction(current_user.id) if current_user.is_authenticated else None
        })
    
    return jsonify({'announcements': announcements_data})

@announcements_bp.route('/api/announcements/<int:announcement_id>/react', methods=['POST'])
@login_required
def api_add_reaction(announcement_id):
    """API endpoint to add/update/remove a reaction"""
    announcement = Announcement.query.get_or_404(announcement_id)
    data = request.get_json()
    reaction_type = data.get('reaction_type')
    
    if not reaction_type:
        return jsonify({'error': 'Reaction type required'}), 400
    
    success, message = announcement.add_reaction(current_user.id, reaction_type)
    
    if success:
        return jsonify({
            'success': True,
            'message': message,
            'reaction_counts': announcement.reaction_counts,
            'user_reaction': announcement.get_user_reaction(current_user.id)
        })
    else:
        return jsonify({'error': message}), 400

# Admin-only routes (you need to add admin check)
@announcements_bp.route('/admin')
@login_required
def admin():
    """Admin page to manage announcements"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('announcements.index'))
    
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('announcements/admin.html', announcements=announcements)

@announcements_bp.route('/admin/create', methods=['GET', 'POST'])
@login_required
def admin_create():
    """Create new announcement"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('announcements.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content_preview = request.form.get('content_preview')
        content_full = request.form.get('content_full')
        message_type = request.form.get('message_type', 'update')
        status = request.form.get('status', 'normal')
        
        # Validate
        if not all([title, content_preview, content_full]):
            flash('All fields are required', 'danger')
            return redirect(url_for('announcements.admin_create'))
        
        # Create announcement
        announcement = Announcement(
            title=title,
            content_preview=content_preview,
            content_full=content_full,
            message_type=message_type,
            author_id=current_user.id,
            author_name=current_user.username,
            status=status
        )
        
        # Handle pinning if checked
        if request.form.get('is_pinned') == 'on':
            announcement.toggle_pin()
        
        db.session.add(announcement)
        db.session.commit()
        
        flash('Announcement created successfully!', 'success')
        return redirect(url_for('announcements.admin'))
    
    return render_template('announcements/create.html')

@announcements_bp.route('/admin/edit/<int:announcement_id>', methods=['GET', 'POST'])
@login_required
def admin_edit(announcement_id):
    """Edit existing announcement"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('announcements.index'))
    
    announcement = Announcement.query.get_or_404(announcement_id)
    
    if request.method == 'POST':
        announcement.title = request.form.get('title')
        announcement.content_preview = request.form.get('content_preview')
        announcement.content_full = request.form.get('content_full')
        announcement.message_type = request.form.get('message_type')
        announcement.status = request.form.get('status')
        announcement.updated_at = datetime.utcnow()
        
        # Handle pinning
        was_pinned = announcement.is_pinned
        want_pinned = request.form.get('is_pinned') == 'on'
        
        if want_pinned and not was_pinned:
            announcement.toggle_pin()
        elif not want_pinned and was_pinned:
            announcement.toggle_pin()
        
        db.session.commit()
        
        flash('Announcement updated successfully!', 'success')
        return redirect(url_for('announcements.admin'))
    
    return render_template('announcements/edit.html', announcement=announcement)

@announcements_bp.route('/admin/delete/<int:announcement_id>', methods=['POST'])
@login_required
def admin_delete(announcement_id):
    """Delete announcement"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('announcements.index'))
    
    announcement = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    
    flash('Announcement deleted successfully!', 'success')
    return redirect(url_for('announcements.admin'))