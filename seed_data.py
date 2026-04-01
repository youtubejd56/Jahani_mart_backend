#!/usr/bin/env python
"""
Seed script to populate the database with sample data.
Run with: python manage.py shell < seed_data.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from api.models import Category, Product

def seed_categories():
    """Create sample categories"""
    categories_data = [
        {'name': 'Electronics', 'icon': 'laptop', 'image': 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=400'},
        {'name': 'Fashion', 'icon': 'shirt', 'image': 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=400'},
        {'name': 'Home & Living', 'icon': 'home', 'image': 'https://images.unsplash.com/photo-1484101403633-562f891dc89a?w=400'},
        {'name': 'Sports', 'icon': 'dumbbell', 'image': 'https://images.unsplash.com/photo-1461896836934- voices-of-liberty?w=400'},
        {'name': 'Books', 'icon': 'book', 'image': 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400'},
        {'name': 'Perfumes', 'icon': 'sparkles', 'image': 'https://images.unsplash.com/photo-1541643600914-78b084683601?w=400'},
        {'name': 'Spices', 'icon': 'container', 'image': 'https://images.unsplash.com/photo-1532336414038-cf19250c5757?w=400'},
        {'name': 'Gemstones', 'icon': 'gem', 'image': 'https://images.unsplash.com/photo-1551300732-2628439403ba?w=400'},
        {'name': 'Premium Collections', 'icon': 'star', 'image': 'https://images.unsplash.com/photo-1513507643584-8bbd8c6d4817?w=400'},
    ]
    
    categories = []
    for cat_data in categories_data:
        cat, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        categories.append(cat)
        if created:
            print(f"Created category: {cat.name}")
        else:
            print(f"Category already exists: {cat.name}")
    
    return categories

def seed_products(categories):
    """Create sample products"""
    products_data = [
        # Electronics
        {'name': 'Wireless Bluetooth Headphones', 'description': 'Premium sound quality with noise cancellation', 'price': 2999, 'original_price': 5999, 'rating': 4.5, 'category': categories[0], 'image': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400', 'stock': 50},
        {'name': 'Smart Watch Pro', 'description': 'Track your fitness and stay connected', 'price': 4999, 'original_price': 8999, 'rating': 4.3, 'category': categories[0], 'image': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400', 'stock': 30},
        {'name': 'Portable Speaker', 'description': '360-degree surround sound', 'price': 1999, 'original_price': 3999, 'rating': 4.2, 'category': categories[0], 'image': 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400', 'stock': 45},
        {'name': 'Wireless Mouse', 'description': 'Ergonomic design with precision tracking', 'price': 899, 'original_price': 1499, 'rating': 4.4, 'category': categories[0], 'image': 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400', 'stock': 100},
        
        # Fashion
        {'name': 'Classic Denim Jacket', 'description': 'Timeless style for every season', 'price': 2499, 'original_price': 3999, 'rating': 4.6, 'category': categories[1], 'image': 'https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=400', 'stock': 25},
        {'name': 'Premium Cotton T-Shirt', 'description': '100% organic cotton, comfortable fit', 'price': 899, 'original_price': 1499, 'rating': 4.3, 'category': categories[1], 'image': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400', 'stock': 80},
        {'name': 'Running Shoes', 'description': 'Lightweight with superior grip', 'price': 3499, 'original_price': 5999, 'rating': 4.5, 'category': categories[1], 'image': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400', 'stock': 40},
        
        # Home & Living
        {'name': 'Modern Table Lamp', 'description': 'Elegant design with LED bulb', 'price': 1299, 'original_price': 2499, 'rating': 4.1, 'category': categories[2], 'image': 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400', 'stock': 35},
        {'name': 'Decorative Cushion Set', 'description': 'Set of 4 premium cushions', 'price': 1599, 'original_price': 2999, 'rating': 4.4, 'category': categories[2], 'image': 'https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=400', 'stock': 60},
        {'name': 'Wall Clock', 'description': 'Silent movement, modern design', 'price': 799, 'original_price': 1299, 'rating': 4.2, 'category': categories[2], 'image': 'https://images.unsplash.com/photo-1563861826100-9cb868fdbe1c?w=400', 'stock': 55},
        
        # Sports
        {'name': 'Yoga Mat Premium', 'description': 'Non-slip, eco-friendly material', 'price': 999, 'original_price': 1999, 'rating': 4.7, 'category': categories[3], 'image': 'https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=400', 'stock': 70},
        {'name': 'Adjustable Dumbbells', 'description': '5-25 lbs adjustable set', 'price': 4999, 'original_price': 7999, 'rating': 4.5, 'category': categories[3], 'image': 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400', 'stock': 20},
        
        # Books
        {'name': 'The Art of Programming', 'description': 'Comprehensive guide to coding', 'price': 599, 'original_price': 999, 'rating': 4.8, 'category': categories[4], 'image': 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400', 'stock': 120},
        {'name': 'Business Strategy Masterclass', 'description': 'Learn from industry experts', 'price': 449, 'original_price': 799, 'rating': 4.4, 'category': categories[4], 'image': 'https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=400', 'stock': 90},
        
        # New Categories: Perfumes, Spices, Gemstones (Categories 5, 6, 7)
        # Perfumes
        {'name': 'Royal Orchid Perfume', 'description': 'Long-lasting floral fragrance with musk base notes', 'price': 2699, 'original_price': 2999, 'discount': 10, 'rating': 4.9, 'category': categories[5], 'image_url': 'https://images.unsplash.com/photo-1594035910387-fea47794261f?w=400', 'stock': 40},
        
        # Spices
        {'name': 'Organic Saffron (1g)', 'description': 'Premium grade A Kashmiri saffron', 'price': 315, 'original_price': 350, 'discount': 10, 'rating': 4.8, 'category': categories[6], 'image_url': 'https://images.unsplash.com/photo-1615485290382-441e4d0c9cb5?w=400', 'stock': 100},
        
        # Gemstones
        {'name': 'Pure Raw Ruby', 'description': 'High-quality unheated raw ruby gemstone from Myanmar', 'price': 8999, 'original_price': 9999, 'discount': 10, 'rating': 5.0, 'category': categories[7], 'image_url': 'https://images.unsplash.com/photo-1588444839799-eb0c29ec8b89?w=400', 'stock': 10},
        
        # Premium Collections (Mixed Products) - Category 8
        {'name': 'Luxury Trio Gift Set', 'description': 'Exquisite collection featuring our signature Royal Orchid Perfume, Organic Saffron, and a Pure Raw Ruby gemstone.', 'price': 10800, 'original_price': 12000, 'discount': 10, 'rating': 5.0, 'category': categories[8], 'image_url': 'https://images.unsplash.com/photo-1513507643584-8bbd8c6d4817?w=400', 'stock': 15},
    ]
    
    for prod_data in products_data:
        prod, created = Product.objects.get_or_create(
            name=prod_data['name'],
            defaults=prod_data
        )
        if created:
            print(f"Created product: {prod.name}")
        else:
            print(f"Product already exists: {prod.name}")

def main():
    print("Starting seed data...")
    print("-" * 50)
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    # Product.objects.all().delete()
    # Category.objects.all().delete()
    
    categories = seed_categories()
    print("-" * 50)
    seed_products(categories)
    print("-" * 50)
    print("Seed data completed!")
    print(f"Total Categories: {Category.objects.count()}")
    print(f"Total Products: {Product.objects.count()}")

if __name__ == '__main__':
    main()
