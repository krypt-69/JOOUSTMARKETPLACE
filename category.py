from app import create_app, db
from app.models import Category

# Create app context
app = create_app()

with app.app_context():
    # Add categories
    categories = ['Electronics', 'Books', 'Furniture', 'Fashion', 'Sports', 'Others']
    
    for cat_name in categories:
        if not Category.query.filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name))
            print(f"Added: {cat_name}")
        else:
            print(f"Already exists: {cat_name}")
    
    db.session.commit()
    
    # Verify
    print("\n=== Categories in Database ===")
    for cat in Category.query.all():
        print(f"✓ {cat.id}: {cat.name}")