import os
import sys
import unittest

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, Product, ProductUnlock, Chat, Message, Category

class ChatModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create test data
        self.buyer = User(username='buyer', email='buyer@test.com', password_hash='hash')
        self.seller = User(username='seller', email='seller@test.com', password_hash='hash')
        
        db.session.add(self.buyer)
        db.session.add(self.seller)
        db.session.commit()
        
        self.category = Category(name='Test')
        db.session.add(self.category)
        db.session.commit()
        
        self.product = Product(
            title='Test Product',
            description='Test',
            price=100.0,
            Token=1.0,
            category_id=self.category.id,
            seller_id=self.seller.id,
            condition='new'
        )
        db.session.add(self.product)
        db.session.commit()
        
        self.unlock = ProductUnlock(
            user_id=self.buyer.id,
            product_id=self.product.id,
            seller_id=self.seller.id,
            amount=1.0,
            status='completed'
        )
        db.session.add(self.unlock)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_chat_creation(self):
        chat = Chat(
            buyer_id=self.buyer.id,
            seller_id=self.seller.id,
            product_id=self.product.id,
            unlock_id=self.unlock.id
        )
        db.session.add(chat)
        db.session.commit()
        
        self.assertIsNotNone(chat.id)
        self.assertEqual(chat.buyer_id, self.buyer.id)
        self.assertEqual(chat.seller_id, self.seller.id)
    
    def test_message_creation(self):
        chat = Chat(
            buyer_id=self.buyer.id,
            seller_id=self.seller.id,
            product_id=self.product.id,
            unlock_id=self.unlock.id
        )
        db.session.add(chat)
        db.session.commit()
        
        message = Message(
            chat_id=chat.id,
            content='Hello',
            sender_id=self.buyer.id,
            receiver_id=self.seller.id
        )
        db.session.add(message)
        db.session.commit()
        
        self.assertIsNotNone(message.id)
        self.assertEqual(message.content, 'Hello')
        self.assertFalse(message.is_read)
    
    def test_can_chat_with(self):
        # Buyer can chat with seller
        self.assertTrue(self.buyer.can_chat_with(self.seller.id, self.product.id))
        
        # Seller can't chat with themselves
        self.assertFalse(self.seller.can_chat_with(self.seller.id))
        
        # New user can't chat
        new_user = User(username='new', email='new@test.com', password_hash='hash')
        db.session.add(new_user)
        db.session.commit()
        self.assertFalse(new_user.can_chat_with(self.seller.id, self.product.id))

if __name__ == '__main__':
    unittest.main()
