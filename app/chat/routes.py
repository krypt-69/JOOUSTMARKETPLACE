import os
from flask import render_template, request, jsonify, current_app, abort, url_for, redirect
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from datetime import datetime
from app.chat import chat_bp
from app import db
from app.models import User, Product, ProductUnlock, Chat, Message, Notification
import uuid

# Allowed image extensions for chat
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def get_chat_directory():
    """Get or create chat upload directory"""
    upload_dir = current_app.config['CHAT_UPLOAD_FOLDER']
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    return upload_dir

@chat_bp.route('/')
@login_required
def index():
    """Main chat page showing all conversations"""
    # Get all chats where user is either buyer or seller
    chats = Chat.query.filter(
        (Chat.buyer_id == current_user.id) | (Chat.seller_id == current_user.id),
        Chat.is_active == True
    ).order_by(Chat.updated_at.desc()).all()
    
    # Format chats with last message and unread count
    formatted_chats = []
    for chat in chats:
        last_message = Message.query.filter_by(chat_id=chat.id)\
            .order_by(Message.created_at.desc()).first()
        
        unread_count = Message.query.filter_by(
            chat_id=chat.id,
            receiver_id=current_user.id,
            is_read=False
        ).count()
        
        other_user = chat.get_other_participant(current_user.id)
        
        formatted_chats.append({
            'chat_id': chat.id,
            'product': chat.product,
            'other_user': other_user,
            'last_message': last_message.content if last_message and not last_message.is_image else '[Image]' if last_message else None,
            'last_message_time': last_message.formatted_time if last_message else None,
            'unread_count': unread_count,
            'updated_at': chat.updated_at
        })
    
    return render_template('chat/index.html', chats=formatted_chats)

@chat_bp.route('/start/<int:product_id>', methods=['POST'])
@login_required
def start_chat(product_id):
    """Start a new chat for a product"""
    product = Product.query.get_or_404(product_id)
    
    # Check if user can chat (must have unlocked)
    if not product.is_unlocked_by(current_user):
        flash('You need to unlock this product first', 'danger')
        return redirect(url_for('products.detail', product_id=product.id))
    
    # Check if chat already exists
    existing_chat = Chat.query.filter_by(
        product_id=product.id,
        buyer_id=current_user.id,
        seller_id=product.seller_id
    ).first()
    
    if existing_chat:
        # Chat exists, redirect to it
        return redirect(url_for('chat.chat_room', chat_id=existing_chat.id))
    
    # Get the unlock record
    unlock = ProductUnlock.query.filter_by(
        product_id=product.id,
        user_id=current_user.id,
        status='completed'
    ).first()
    
    if not unlock:
        flash('No valid unlock found', 'danger')
        return redirect(url_for('products.detail', product_id=product.id))
    
    # Create new chat
    chat = Chat(
        buyer_id=current_user.id,
        seller_id=product.seller_id,
        product_id=product.id,
        unlock_id=unlock.id
    )
    
    db.session.add(chat)
    db.session.commit()
    
    # Redirect to the new chat
    return redirect(url_for('chat.chat_room', chat_id=chat.id))

@chat_bp.route('/<int:chat_id>')
@login_required
def chat_room(chat_id):
    """Chat room view"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Check if user is participant
    if chat.buyer_id != current_user.id and chat.seller_id != current_user.id:
        abort(403)
    
    # Mark messages as read for current user
    chat.mark_messages_as_read(current_user.id)
    
    # Get messages
    messages = Message.query.filter_by(chat_id=chat_id)\
        .order_by(Message.created_at.asc())\
        .all()
    
    other_user = chat.get_other_participant(current_user.id)
    
    return render_template('chat/room.html', 
                         chat=chat, 
                         messages=messages, 
                         other_user=other_user,
                         product=chat.product)

@chat_bp.route('/<int:chat_id>/messages')
@login_required
def get_messages(chat_id):
    """Get messages for a chat (AJAX endpoint)"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Check if user is participant
    if chat.buyer_id != current_user.id and chat.seller_id != current_user.id:
        abort(403)
    
    # Get messages after a specific ID if provided
    last_message_id = request.args.get('last_id', type=int)
    
    query = Message.query.filter_by(chat_id=chat_id)
    
    if last_message_id:
        query = query.filter(Message.id > last_message_id)
    
    messages = query.order_by(Message.created_at.asc()).all()
    
    # Mark as read
    unread_ids = [msg.id for msg in messages if msg.receiver_id == current_user.id and not msg.is_read]
    if unread_ids:
        Message.query.filter(Message.id.in_(unread_ids)).update({Message.is_read: True})
        db.session.commit()
    
    # Format messages for JSON response
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'content': msg.content,
            'is_image': msg.is_image,
            'image_url': msg.get_image_url() if msg.is_image else None,
            'created_at': msg.created_at.isoformat(),
            'formatted_time': msg.formatted_time,
            'is_mine': msg.sender_id == current_user.id
        })
    
    return jsonify({'messages': formatted_messages})

@chat_bp.route('/<int:chat_id>/send', methods=['POST'])
@login_required
def send_message(chat_id):
    """Send a new message (text or image)"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Check if user is participant
    if chat.buyer_id != current_user.id and chat.seller_id != current_user.id:
        abort(403)
    
    # Check if chat is active
    if not chat.is_active:
        return jsonify({'error': 'This chat is no longer active'}), 400
    
    # Determine receiver
    receiver_id = chat.seller_id if current_user.id == chat.buyer_id else chat.buyer_id
    
    content = request.form.get('content', '').strip()
    image_file = request.files.get('image')
    
    # Validate: must have either content or image
    if not content and not image_file:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    message = Message(
        chat_id=chat_id,
        sender_id=current_user.id,
        receiver_id=receiver_id
    )
    
    # Handle image upload
    if image_file and image_file.filename:
        if not allowed_file(image_file.filename):
            return jsonify({'error': 'File type not allowed. Only images are permitted.'}), 400
        
        # Generate unique filename
        filename = secure_filename(image_file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Save file
        upload_dir = get_chat_directory()
        filepath = os.path.join(upload_dir, unique_filename)
        image_file.save(filepath)
        
        message.is_image = True
        message.image_filename = unique_filename
        # Optional: you can add image caption
        message.content = content if content else None
    else:
        # Text message
        message.content = content
    
    db.session.add(message)
    
    # Update chat's updated_at timestamp
    chat.updated_at = datetime.utcnow()
    
    # ⚠️ NOTIFICATION REMOVED - No longer creating notifications for individual messages
    # This prevents spam/space-taking notifications
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message_id': message.id,
        'content': message.content,
        'is_image': message.is_image,
        'image_url': message.get_image_url() if message.is_image else None,
        'created_at': message.created_at.isoformat(),
        'formatted_time': message.formatted_time
    })

@chat_bp.route('/<int:chat_id>/close', methods=['POST'])
@login_required
def close_chat(chat_id):
    """Close a chat (mark as inactive)"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Check if user is participant
    if chat.buyer_id != current_user.id and chat.seller_id != current_user.id:
        abort(403)
    
    chat.is_active = False
    db.session.commit()
    
    return jsonify({'success': True})

@chat_bp.route('/unread_count')
@login_required
def get_unread_count():
    """Get total unread messages count for current user"""
    # Count unread messages in all active chats
    unread_count = Message.query.join(Chat, Message.chat_id == Chat.id)\
        .filter(
            Message.receiver_id == current_user.id,
            Message.is_read == False,
            Chat.is_active == True
        ).count()
    
    return jsonify({'unread_count': unread_count})

@chat_bp.route('/check_new/<int:chat_id>')
@login_required
def check_new_messages(chat_id):
    """Check for new messages (for polling)"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Check if user is participant
    if chat.buyer_id != current_user.id and chat.seller_id != current_user.id:
        abort(403)
    
    last_message_id = request.args.get('last_id', type=int)
    
    if not last_message_id:
        return jsonify({'has_new': False})
    
    # Check if there are new messages
    has_new = Message.query.filter(
        Message.chat_id == chat_id,
        Message.id > last_message_id
    ).first() is not None
    
    return jsonify({'has_new': has_new})

# ===== MESSAGE DELETION AND CLEANUP ROUTES =====

@chat_bp.route('/<int:chat_id>/messages/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(chat_id, message_id):
    """Delete a message (soft delete)"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Check if user is participant
    if chat.buyer_id != current_user.id and chat.seller_id != current_user.id:
        abort(403)
    
    # Check if chat is active
    if not chat.is_active:
        return jsonify({'error': 'This chat is no longer active'}), 400
    
    message = Message.query.get_or_404(message_id)
    
    # Check if message belongs to this chat
    if message.chat_id != chat_id:
        return jsonify({'error': 'Message not found in this chat'}), 404
    
    # Check if user can delete this message (must be sender or receiver)
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        return jsonify({'error': 'You can only delete your own messages'}), 403
    
    # Soft delete the message
    message.delete(current_user.id)
    
    # Update chat's last activity
    chat.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Message deleted',
        'display_content': message.get_display_content(current_user.id)
    })

@chat_bp.route('/<int:chat_id>/clear', methods=['POST'])
@login_required
def clear_chat(chat_id):
    """Clear all messages in a chat (soft delete user's side only)"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Check if user is participant
    if chat.buyer_id != current_user.id and chat.seller_id != current_user.id:
        abort(403)
    
    # Soft delete all messages for this user
    messages_to_delete = Message.query.filter_by(
        chat_id=chat_id
    ).filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).all()
    
    for message in messages_to_delete:
        message.delete(current_user.id)
    
    # Update chat's last activity
    chat.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Cleared {len(messages_to_delete)} messages',
        'cleared_count': len(messages_to_delete)
    })

@chat_bp.route('/admin/cleanup', methods=['POST'])
@login_required
def cleanup_chats():
    """Admin endpoint to auto-close inactive chats"""
    if not current_user.is_admin:
        abort(403)
    
    closed_chats = []
    
    # Find chats that should be auto-closed
    chats_to_close = Chat.query.filter_by(is_active=True).all()
    
    for chat in chats_to_close:
        if chat.should_auto_close():
            reason = 'product_sold' if chat.product.is_sold else 'inactivity'
            chat.close_chat(reason)
            closed_chats.append({
                'id': chat.id,
                'product': chat.product.title,
                'reason': reason
            })
    
    if closed_chats:
        db.session.commit()
    
    return jsonify({
        'success': True,
        'closed_count': len(closed_chats),
        'closed_chats': closed_chats
    })
@chat_bp.route('/<int:chat_id>/mark-read', methods=['POST'])
@login_required
def mark_chat_read(chat_id):
    """Mark all messages in a chat as read"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Check if user is participant
    if chat.buyer_id != current_user.id and chat.seller_id != current_user.id:
        abort(403)
    
    # Mark all messages as read
    Message.query.filter_by(
        chat_id=chat_id,
        receiver_id=current_user.id,
        is_read=False
    ).update({Message.is_read: True})
    
    db.session.commit()
    
    return jsonify({'success': True})

@chat_bp.route('/<int:chat_id>/delete', methods=['POST'])
@login_required
def delete_chat(chat_id):
    """Delete an entire chat (soft delete)"""
    chat = Chat.query.get_or_404(chat_id)
    
    # Check if user is participant
    if chat.buyer_id != current_user.id and chat.seller_id != current_user.id:
        abort(403)
    
    # Soft delete all messages
    messages = Message.query.filter_by(chat_id=chat_id).all()
    for message in messages:
        message.delete(current_user.id)
    
    # Soft delete the chat (mark as inactive)
    chat.is_active = False
    chat.closed_reason = 'user_deleted'
    chat.closed_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})
@chat_bp.route('/find-by-product/<int:product_id>', methods=['GET'])
@login_required
def find_chat_by_product(product_id):
    """Find chat for a product where current user is seller"""
    product = Product.query.get_or_404(product_id)
    
    # Check if user is the seller
    if product.seller_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Find the first chat for this product
    chat = Chat.query.filter_by(product_id=product_id).first()
    
    if chat:
        return jsonify({'chat_id': chat.id})
    else:
        return jsonify({'chat_id': None}), 404