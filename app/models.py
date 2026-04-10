from flask_login import UserMixin
from flask import current_app
from app import db, login_manager
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
from sqlalchemy import CheckConstraint

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Google OAuth fields
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    profile_picture = db.Column(db.String(500), nullable=True)
    
    # Relationships with back_populates
    products = db.relationship('Product', 
        foreign_keys='Product.seller_id',
        back_populates='seller', 
        lazy=True
    )
    
    payments = db.relationship('Payment', 
        back_populates='payment_user', 
        lazy=True
    )
    
    # New contact fields
    phone_number = db.Column(db.String(20))
    campus_location = db.Column(db.String(100))
    hostel_name = db.Column(db.String(100))
    hostel_room = db.Column(db.String(20))
    whatsapp_number = db.Column(db.String(20))
    
    # Seller preferences
    show_contact_details = db.Column(db.Boolean, default=True)
    contact_preference = db.Column(db.String(20), default='whatsapp')
    is_admin = db.Column(db.Boolean, default=False)
    
    # Chat relationships
    conversations_as_buyer = db.relationship('Chat', 
        foreign_keys='Chat.buyer_id',
        back_populates='buyer',
        lazy=True,
        cascade='all, delete-orphan'
    )
    conversations_as_seller = db.relationship('Chat', 
        foreign_keys='Chat.seller_id',
        back_populates='seller',
        lazy=True,
        cascade='all, delete-orphan'
    )
    sent_messages = db.relationship('Message',
        foreign_keys='Message.sender_id',
        back_populates='sender',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    # New relationships for offers
    sent_offers = db.relationship('Offer', 
        foreign_keys='Offer.buyer_id',
        back_populates='offer_buyer',
        lazy=True
    )
    received_offers = db.relationship('Offer',
        foreign_keys='Offer.seller_id',
        back_populates='offer_seller',
        lazy=True
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    @classmethod
    def create_from_google(cls, google_data):
        email = google_data['email']
        name = google_data.get('name', '').strip()
        google_id = google_data['id']
        profile_picture = google_data.get('picture', '')
        
        if not name:
            name = email.split('@')[0]
        
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        
        while cls.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = cls(
            username=username,
            email=email,
            google_id=google_id,
            profile_picture=profile_picture,
            password_hash=generate_password_hash(cls.generate_random_password())
        )
        
        user.show_contact_details = True
        user.contact_preference = 'whatsapp'
        
        return user
    
    @staticmethod
    def generate_random_password():
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(24))
    
    def update_google_info(self, google_data):
        if not self.google_id:
            self.google_id = google_data['id']
        
        if not self.profile_picture and google_data.get('picture'):
            self.profile_picture = google_data['picture']
    
    @property
    def is_google_user(self):
        return bool(self.google_id)
    
    def can_chat_with(self, other_user_id, product_id=None):
        if self.id == other_user_id:
            return False
            
        if product_id:
            unlock = ProductUnlock.query.filter_by(
                user_id=self.id,
                product_id=product_id,
                status='completed'
            ).first()
            return unlock is not None
        
        unlock = ProductUnlock.query.join(Product, ProductUnlock.product_id == Product.id)\
            .filter(
                ProductUnlock.user_id == self.id,
                Product.seller_id == other_user_id,
                ProductUnlock.status == 'completed'
            ).first()
        return unlock is not None
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    products = db.relationship('Product', back_populates='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class ProductImageGroup(db.Model):
    __tablename__ = 'product_image_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    images = db.relationship('ProductImage', back_populates='group', lazy=True, cascade='all, delete-orphan')
    product = db.relationship('Product', back_populates='image_group', lazy=True, uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ProductImageGroup {self.id}>'

class ProductImage(db.Model):
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    group_id = db.Column(db.Integer, db.ForeignKey('product_image_groups.id'))
    
    group = db.relationship('ProductImageGroup', back_populates='images')
    
    def __repr__(self):
        return f'<ProductImage {self.filename}>'

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(20))
    contact_info = db.Column(db.Text)
    is_fast_moving = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_sold = db.Column(db.Boolean, default=False)
    Token = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    image_group_id = db.Column(db.Integer, db.ForeignKey('product_image_groups.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Room exit fields
    hostel_name = db.Column(db.String(100), nullable=False, default='')
    location = db.Column(db.String(100), nullable=False, default='')
    leave_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    room_type = db.Column(db.String(20), default='single')
    deposit = db.Column(db.Float, default=0)
    commission_percentage = db.Column(db.Float, default=0)
    is_commission_listing = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='available')
    agreement_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    agreement_expires_at = db.Column(db.DateTime, nullable=True)
    booked_at = db.Column(db.DateTime, nullable=True)
    total_unlocks = db.Column(db.Integer, default=0)
    last_interest_update = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', back_populates='product', lazy=True, cascade="all, delete-orphan")
    chats = db.relationship('Chat', back_populates='product', lazy=True, cascade='all, delete-orphan')
    offers = db.relationship('Offer', back_populates='product', lazy=True, cascade='all, delete-orphan')
    unlocks = db.relationship(
    'ProductUnlock',
    back_populates='product',
    cascade='all, delete-orphan'
)
    notifications = db.relationship(
    'Notification',
    back_populates='product',
    cascade='all, delete-orphan'
)
    agreement_user = db.relationship('User', foreign_keys=[agreement_user_id])
    category = db.relationship('Category', back_populates='products')
    seller = db.relationship('User', foreign_keys=[seller_id], back_populates='products')
    image_group = db.relationship('ProductImageGroup', back_populates='product')


    @property
    def image(self):
        if self.image_group and self.image_group.images:
            return self.image_group.images[0].filename
        return None
    
    @property
    def images(self):
        if self.image_group:
            return self.image_group.images
        return []
    
    @property
    def image_urls(self):
        if self.image_group:
            return [img.filename for img in self.image_group.images]
        return []

    def is_unlocked_by(self, user):
        if not user or not user.is_authenticated:
            return False
            
        unlock = ProductUnlock.query.filter_by(
            product_id=self.id,
            user_id=user.id,
            status='completed'
        ).first()
        
        return unlock is not None
    
    def get_unlock_fee(self):
        base_fee = current_app.config.get('UNLOCK_FEE', 1)
        return base_fee
    
    def get_commission_amount(self):
        if self.is_commission_listing and self.commission_percentage > 0:
            return (self.price * self.commission_percentage) / 100
        return 0
    
    def get_deposit_display(self):
        if self.deposit and self.deposit > 0:
            return f"KES {self.deposit:,.0f}"
        return "No Deposit"
    
    def get_commission_display(self):
        if self.is_commission_listing and self.commission_percentage > 0:
            amount = self.get_commission_amount()
            return f"{self.commission_percentage}% (KES {amount:,.0f})"
        return "No Commission"
    
    def days_until_leave(self):
        if not self.leave_date:
            return 0
        delta = self.leave_date - datetime.utcnow()
        return max(0, delta.days)
    
    def is_expired(self):
        return self.leave_date and self.leave_date < datetime.utcnow()
    
    def update_status(self):
        now = datetime.utcnow()
        
        if self.is_expired():
            self.status = 'expired'
            return
        
        if self.status == 'pending' and self.agreement_expires_at:
            if self.agreement_expires_at < now:
                self.status = 'available'
                self.agreement_user_id = None
                self.agreement_expires_at = None
        
        if self.is_sold:
            self.status = 'booked'
    
    def can_make_offer(self, user):
        if not user or not user.is_authenticated:
            return False
        
        if not self.is_unlocked_by(user):
            return False
        
        if user.id == self.seller_id:
            return False
        
        if self.status not in ['available', 'pending']:
            return False
        
        offer_count = Offer.query.filter_by(
            product_id=self.id,
            buyer_id=user.id,
            status='active'
        ).count()
        
        return offer_count < 3
    
    def mark_agreement(self, user_id):
        from datetime import timedelta
        
        self.status = 'pending'
        self.agreement_user_id = user_id
        self.agreement_expires_at = datetime.utcnow() + timedelta(hours=48)
        
        # Accept the chosen user's offer
        Offer.query.filter(
            Offer.product_id == self.id,
            Offer.buyer_id == user_id,
            Offer.status == 'active'
        ).update({'status': 'accepted'}, synchronize_session=False)
        
        # Reject all other active offers
        Offer.query.filter(
            Offer.product_id == self.id,
            Offer.status == 'active',
            Offer.buyer_id != user_id
        ).update({'status': 'rejected'}, synchronize_session=False)
    
    def cancel_agreement(self):
        self.status = 'available'
        self.agreement_user_id = None
        self.agreement_expires_at = None
        
        # Fix: Use .in_() instead of __in
        Offer.query.filter(
            Offer.product_id == self.id,
            Offer.status.in_(['accepted', 'rejected'])
        ).update({'status': 'active'}, synchronize_session=False)
    
    def mark_booked(self):
        self.is_sold = True
        self.status = 'booked'
        self.booked_at = datetime.utcnow()
        
        for chat in self.chats:
            chat.close_chat('booked')
    
    def increment_unlock_count(self):
        self.total_unlocks += 1
        self.last_interest_update = datetime.utcnow()
    
    def __repr__(self):
        return f'<Product {self.title}>'

class Offer(db.Model):
    __tablename__ = 'offers'
    
    id = db.Column(db.Integer, primary_key=True)
    
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    deposit_offer = db.Column(db.Float, nullable=True)
    commission_offer = db.Column(db.Float, nullable=True)
    move_in_date = db.Column(db.DateTime, nullable=True)
    message = db.Column(db.Text, nullable=True)
    
    original_deposit = db.Column(db.Float)
    original_commission = db.Column(db.Float)
    
    offer_value = db.Column(db.Float)
    
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    parent_offer_id = db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=True)
    is_counter = db.Column(db.Boolean, default=False)
    
    # Relationships
    product = db.relationship('Product', back_populates='offers')
    offer_buyer = db.relationship('User', foreign_keys=[buyer_id], back_populates='sent_offers')
    offer_seller = db.relationship('User', foreign_keys=[seller_id], back_populates='received_offers')
    parent_offer = db.relationship('Offer', remote_side=[id], backref='counter_offers')
    
    def calculate_offer_value(self):
        value = 0
        
        if self.deposit_offer:
            value += self.deposit_offer
        
        if self.commission_offer and self.product:
            value += (self.product.price * self.commission_offer) / 100
        
        self.offer_value = value
        return value
    
    def is_better_than(self, other_offer):
        if not other_offer:
            return True
        return (self.offer_value or 0) > (other_offer.offer_value or 0)
    
    def accept(self):
        self.status = 'accepted'
        self.product.mark_agreement(self.buyer_id)
    
    def reject(self):
        self.status = 'rejected'
    
    def withdraw(self):
        self.status = 'withdrawn'
    
    def create_counter(self, deposit=None, commission=None, message=None):
        counter = Offer(
            product_id=self.product_id,
            buyer_id=self.buyer_id,
            seller_id=self.seller_id,
            deposit_offer=deposit if deposit is not None else self.deposit_offer,
            commission_offer=commission if commission is not None else self.commission_offer,
            move_in_date=self.move_in_date,
            message=message,
            original_deposit=self.product.deposit,
            original_commission=self.product.commission_percentage,
            parent_offer_id=self.id,
            is_counter=True
        )
        counter.calculate_offer_value()
        self.status = 'countered'
        return counter
    
    def __repr__(self):
        return f'<Offer {self.id}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    checkout_request_id = db.Column(db.String(100), unique=True)
    merchant_request_id = db.Column(db.String(100))
    mpesa_receipt_number = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')
    transaction_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    product = db.relationship('Product', back_populates='payments')
    payment_user = db.relationship('User', foreign_keys=[user_id], back_populates='payments')

class ProductUnlock(db.Model):
    __tablename__ = 'product_unlocks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)
    phone_number = db.Column(db.String(20))
    checkout_request_id = db.Column(db.String(100), unique=True)
    merchant_request_id = db.Column(db.String(100))
    mpesa_receipt_number = db.Column(db.String(50))
    
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    unlocked_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='unlocked_products')
    product = db.relationship('Product', back_populates='unlocks')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='buyer_unlocks')
    chat = db.relationship('Chat', back_populates='unlock', lazy=True, uselist=False)

    def __repr__(self):
        return f'<ProductUnlock {self.id}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    unlock_id = db.Column(db.Integer, db.ForeignKey('product_unlocks.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications')
    product = db.relationship('Product', back_populates='notifications')
    unlock = db.relationship('ProductUnlock', backref='notification')

    def __repr__(self):
        return f'<Notification {self.id}>'

class Chat(db.Model):
    __tablename__ = 'chats'
    
    id = db.Column(db.Integer, primary_key=True)
    
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    unlock_id = db.Column(db.Integer, db.ForeignKey('product_unlocks.id'), nullable=False, unique=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    closed_reason = db.Column(db.String(50), nullable=True)
    
    has_agreement = db.Column(db.Boolean, default=False)
    agreement_made_at = db.Column(db.DateTime, nullable=True)
    
    __table_args__ = (
        CheckConstraint('buyer_id != seller_id', name='different_participants'),
    )
    
    # Relationships
    messages = db.relationship('Message', back_populates='chat', lazy=True, 
                              cascade='all, delete-orphan', 
                              order_by='Message.created_at.asc()')
    
    buyer = db.relationship('User', foreign_keys=[buyer_id], back_populates='conversations_as_buyer')
    seller = db.relationship('User', foreign_keys=[seller_id], back_populates='conversations_as_seller')
    product = db.relationship('Product', back_populates='chats')
    unlock = db.relationship('ProductUnlock', back_populates='chat')
    
    def get_other_participant(self, current_user_id):
        if current_user_id == self.buyer_id:
            return self.seller
        return self.buyer
    
    def mark_messages_as_read(self, user_id):
        unread_messages = Message.query.filter_by(
            chat_id=self.id,
            receiver_id=user_id,
            is_read=False,
            is_deleted=False
        ).all()
        
        for message in unread_messages:
            message.is_read = True
        
        db.session.commit()
    
    @property
    def unread_count(self, user_id):
        return Message.query.filter_by(
            chat_id=self.id,
            receiver_id=user_id,
            is_read=False,
            is_deleted=False
        ).count()
    
    def close_chat(self, reason='manual'):
        self.is_active = False
        self.closed_at = datetime.utcnow()
        self.closed_reason = reason
        self.updated_at = datetime.utcnow()
    
    def should_auto_close(self):
        if not self.is_active:
            return False
        
        if self.product.is_sold:
            return True
        
        from datetime import timedelta
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        if self.last_message_at and self.last_message_at < one_week_ago:
            return True
        
        return False
    
    def get_messages_for_user(self, user_id):
        return [msg for msg in self.messages if msg.is_visible_to(user_id)]
    
    def mark_agreement(self):
        self.has_agreement = True
        self.agreement_made_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Chat {self.id}>'

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=True)
    is_image = db.Column(db.Boolean, default=False)
    image_filename = db.Column(db.String(255), nullable=True)
    
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    offer_id = db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=True)
    
    __table_args__ = (
        CheckConstraint('sender_id != receiver_id', name='different_sender_receiver'),
    )
    
    # Relationships
    chat = db.relationship('Chat', back_populates='messages')
    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    deleted_by = db.relationship('User', foreign_keys=[deleted_by_id], backref='deleted_messages')
    offer = db.relationship('Offer', backref='message_refs')
    
    def get_image_url(self):
        if self.is_image and self.image_filename:
            return f'/static/uploads/chat_images/{self.image_filename}'
        return None
    
    @property
    def formatted_time(self):
        now = datetime.utcnow()
        diff = now - self.created_at
        
        if diff.days == 0:
            if diff.seconds < 60:
                return "Just now"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60}m ago"
            else:
                return f"{diff.seconds // 3600}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        else:
            return self.created_at.strftime("%b %d, %Y")
    
    def delete(self, user_id):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by_id = user_id
        self.content = "[Message deleted]"
        if self.is_image:
            self.image_filename = None
    
    def is_visible_to(self, user_id):
        if not self.is_deleted:
            return True
        return self.deleted_by_id == user_id
    
    def get_display_content(self, user_id):
        if self.is_deleted:
            if self.deleted_by_id == user_id:
                return "[You deleted this message]"
            else:
                return "[Message deleted]"
        return self.content
class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content_preview = db.Column(db.String(500), nullable=False)
    content_full = db.Column(db.Text, nullable=False)
    
    # Message type: important, update, idea, issue, improvement
    message_type = db.Column(db.String(20), nullable=False, default='update')
    
    # Status: normal, in_progress, completed
    status = db.Column(db.String(20), nullable=False, default='normal')
    
    # Pinning: only one can be True at a time
    is_pinned = db.Column(db.Boolean, default=False)
    
    # Author information (you as admin)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author_name = db.Column(db.String(80), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reactions = db.relationship('Reaction', back_populates='announcement', lazy=True, 
                                cascade='all, delete-orphan')
    author = db.relationship('User', foreign_keys=[author_id], backref='announcements')
    
    def __init__(self, title, content_preview, content_full, message_type, author_id, author_name, status='normal'):
        self.title = title
        self.content_preview = content_preview
        self.content_full = content_full
        self.message_type = message_type
        self.author_id = author_id
        self.author_name = author_name
        self.status = status
    
    @property
    def reaction_counts(self):
        """Return dictionary of reaction counts for this announcement"""
        counts = {'like': 0, 'dislike': 0, 'useful': 0, 'watching': 0}
        
        for reaction in self.reactions:
            if reaction.reaction_type in counts:
                counts[reaction.reaction_type] += 1
        
        return counts
    
    def get_user_reaction(self, user_id):
        """Get the reaction type for a specific user"""
        reaction = Reaction.query.filter_by(
            announcement_id=self.id,
            user_id=user_id
        ).first()
        
        return reaction.reaction_type if reaction else None
    
    def add_reaction(self, user_id, reaction_type):
        """Add or update a user's reaction"""
        # Validate reaction type
        valid_types = ['like', 'dislike', 'useful', 'watching']
        if reaction_type not in valid_types:
            return False, "Invalid reaction type"
        
        # Check if user already reacted
        existing = Reaction.query.filter_by(
            announcement_id=self.id,
            user_id=user_id
        ).first()
        
        if existing:
            if existing.reaction_type == reaction_type:
                # Remove reaction if same (toggle off)
                db.session.delete(existing)
                db.session.commit()
                return True, "Reaction removed"
            else:
                # Update reaction
                existing.reaction_type = reaction_type
                existing.created_at = datetime.utcnow()
                db.session.commit()
                return True, "Reaction updated"
        else:
            # Create new reaction
            reaction = Reaction(
                announcement_id=self.id,
                user_id=user_id,
                reaction_type=reaction_type
            )
            db.session.add(reaction)
            db.session.commit()
            return True, "Reaction added"
    
    def toggle_pin(self):
        """Toggle pinned status, ensuring only one pinned message"""
        if self.is_pinned:
            self.is_pinned = False
        else:
            # Unpin all other announcements
            Announcement.query.filter_by(is_pinned=True).update({'is_pinned': False})
            self.is_pinned = True
        
        db.session.commit()
        return self.is_pinned
    
    def update_status(self, new_status):
        """Update the status of the announcement"""
        valid_statuses = ['normal', 'in_progress', 'completed']
        if new_status in valid_statuses:
            self.status = new_status
            db.session.commit()
            return True
        return False
    
    def __repr__(self):
        return f'<Announcement {self.id}: {self.title[:30]}>'


class Reaction(db.Model):
    __tablename__ = 'reactions'
    
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcements.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)  # like, dislike, useful, watching
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    announcement = db.relationship('Announcement', back_populates='reactions')
    user = db.relationship('User', backref='reactions')
    
    __table_args__ = (
        db.UniqueConstraint('announcement_id', 'user_id', name='unique_user_announcement_reaction'),
    )
    
    def __repr__(self):
        return f'<Reaction {self.id}: {self.reaction_type}>'
# Add this to app/models.py at the end of the file, before the last __repr__

class AdminLog(db.Model):
    """Track all admin actions for security audit"""
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    admin_username = db.Column(db.String(80), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # e.g., 'delete_user', 'toggle_admin', 'delete_product'
    target_type = db.Column(db.String(50))  # 'user', 'product', 'room', 'transaction', 'category'
    target_id = db.Column(db.Integer)
    target_name = db.Column(db.String(200))  # Store name/title for reference
    details = db.Column(db.Text)  # Additional JSON data or description
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    admin = db.relationship('User', foreign_keys=[admin_id], backref='admin_logs')
    
    def __repr__(self):
        return f'<AdminLog {self.id}: {self.admin_username} - {self.action}>'
    
    def __repr__(self):
        return f'<Message {self.id}>'
