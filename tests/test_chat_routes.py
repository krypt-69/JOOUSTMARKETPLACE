import os
import sys
import unittest
import json
from io import BytesIO

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, Product, ProductUnlock, Chat, Message, Category

class ChatRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
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
        
        self.client = self.app.test_client()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self, user):
        """Helper to login a user"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = user.id
            sess['_fresh'] = True
    
    def test_start_chat_authenticated(self):
        """Test starting a chat when authenticated and unlocked"""
        self.login(self.buyer)
        
        response = self.client.post(f'/chat/start/{self.product.id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('chat_id', data)
    
    def test_start_chat_not_unlocked(self):
        """Test starting a chat without unlocking product"""
        # Create another user who hasn't unlocked the product
        other_user = User(username='other', email='other@test.com', password_hash='hash')
        db.session.add(other_user)
        db.session.commit()
        
        self.login(other_user)
        
        response = self.client.post(f'/chat/start/{self.product.id}')
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_send_message(self):
        """Test sending a message in a chat"""
        # First create a chat
        chat = Chat(
            buyer_id=self.buyer.id,
            seller_id=self.seller.id,
            product_id=self.product.id,
            unlock_id=self.unlock.id
        )
        db.session.add(chat)
        db.session.commit()
        
        self.login(self.buyer)
        
        # Send text message
        response = self.client.post(f'/chat/{chat.id}/send', 
                                   data={'content': 'Hello there!'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['content'], 'Hello there!')
        
        # Verify message was saved
        message = Message.query.first()
        self.assertIsNotNone(message)
        self.assertEqual(message.content, 'Hello there!')
        self.assertEqual(message.chat_id, chat.id)
        self.assertEqual(message.sender_id, self.buyer.id)
    
    def test_get_messages(self):
        """Test retrieving messages from a chat"""
        # Create chat and messages
        chat = Chat(
            buyer_id=self.buyer.id,
            seller_id=self.seller.id,
            product_id=self.product.id,
            unlock_id=self.unlock.id
        )
        db.session.add(chat)
        db.session.commit()
        
        message1 = Message(
            chat_id=chat.id,
            content='First message',
            sender_id=self.buyer.id,
            receiver_id=self.seller.id
        )
        message2 = Message(
            chat_id=chat.id,
            content='Second message',
            sender_id=self.seller.id,
            receiver_id=self.buyer.id
        )
        db.session.add(message1)
        db.session.add(message2)
        db.session.commit()
        
        self.login(self.buyer)
        
        response = self.client.get(f'/chat/{chat.id}/messages')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('messages', data)
        self.assertEqual(len(data['messages']), 2)
    
    def test_chat_room_access(self):
        """Test accessing chat room"""
        chat = Chat(
            buyer_id=self.buyer.id,
            seller_id=self.seller.id,
            product_id=self.product.id,
            unlock_id=self.unlock.id
        )
        db.session.add(chat)
        db.session.commit()
        
        self.login(self.buyer)
        
        response = self.client.get(f'/chat/{chat.id}')
        self.assertEqual(response.status_code, 200)
    
    def test_chat_room_access_denied(self):
        """Test accessing someone else's chat"""
        chat = Chat(
            buyer_id=self.buyer.id,
            seller_id=self.seller.id,
            product_id=self.product.id,
            unlock_id=self.unlock.id
        )
        db.session.add(chat)
        db.session.commit()
        
        # Create another user
        other_user = User(username='other', email='other@test.com', password_hash='hash')
        db.session.add(other_user)
        db.session.commit()
        
        self.login(other_user)
        
        response = self.client.get(f'/chat/{chat.id}')
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()