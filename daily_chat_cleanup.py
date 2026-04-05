#!/usr/bin/env python
"""
Daily chat cleanup script
Run this daily via cron to auto-close inactive chats
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models import Chat, Product

def daily_cleanup():
    """Perform daily chat cleanup"""
    app = create_app()
    
    with app.app_context():
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Starting daily chat cleanup...")
        
        closed_count = 0
        
        # 1. Close chats for sold products
        sold_products = Product.query.filter_by(is_sold=True).all()
        for product in sold_products:
            active_chats = Chat.query.filter_by(
                product_id=product.id,
                is_active=True
            ).all()
            
            for chat in active_chats:
                chat.close_chat('product_sold')
                closed_count += 1
                print(f"  Closed chat {chat.id}: Product '{product.title}' sold")
        
        # 2. Close chats inactive for 1 week
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        inactive_chats = Chat.query.filter(
            Chat.is_active == True,
            Chat.last_message_at < one_week_ago
        ).all()
        
        for chat in inactive_chats:
            last_msg = chat.last_message_at.strftime('%Y-%m-%d') if chat.last_message_at else 'never'
            days_inactive = (datetime.utcnow() - chat.last_message_at).days if chat.last_message_at else 999
            chat.close_chat('inactivity')
            closed_count += 1
            print(f"  Closed chat {chat.id}: Inactive for {days_inactive} days (last: {last_msg})")
        
        if closed_count > 0:
            db.session.commit()
            print(f"\n✅ Cleanup complete: {closed_count} chat(s) closed")
        else:
            print("\n✅ No chats needed closing")
        
        return closed_count

if __name__ == "__main__":
    try:
        count = daily_cleanup()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        sys.exit(1)
