from flask import current_app
from app import db
from app.models import Chat, ProductUnlock, Notification

def get_or_create_chat(product_id, buyer_id):
    """Get existing chat or create a new one for a product"""
    product = current_app.models.Product.query.get_or_404(product_id)
    
    # Check if user has unlocked this product
    unlock = ProductUnlock.query.filter_by(
        user_id=buyer_id,
        product_id=product_id,
        status='completed'
    ).first()
    
    if not unlock:
        return None, "You need to unlock this product first to chat with the seller"
    
    # Check if chat already exists
    existing_chat = Chat.query.filter_by(
        buyer_id=buyer_id,
        seller_id=product.seller_id,
        product_id=product_id,
        unlock_id=unlock.id
    ).first()
    
    if existing_chat:
        # Reactivate if inactive
        if not existing_chat.is_active:
            existing_chat.is_active = True
            db.session.commit()
        return existing_chat, None
    
    # Create new chat
    chat = Chat(
        buyer_id=buyer_id,
        seller_id=product.seller_id,
        product_id=product_id,
        unlock_id=unlock.id
    )
    
    db.session.add(chat)
    db.session.commit()
    
    # Create notification for seller about new chat
    from app.models import User
    buyer = User.query.get(buyer_id)
    
    notification = Notification(
        user_id=product.seller_id,
        product_id=product_id,
        unlock_id=unlock.id,
        message=f"New chat started by {buyer.username} about your product: {product.title}"
    )
    db.session.add(notification)
    db.session.commit()
    
    return chat, None