from app import create_app
from extensions import db
from models import User, Product, Order, OrderItem, Review
import bcrypt
from datetime import datetime

app = create_app()

PRODUCTS = [
    ('Wireless Mouse',      'Ergonomic wireless mouse with 2.4 GHz connectivity.',  29.99, 50,  'Electronics'),
    ('Mechanical Keyboard', 'Tenkeyless mechanical keyboard with blue switches.',    79.99, 30,  'Electronics'),
    ('USB-C Hub',           '7-in-1 USB-C hub with HDMI, USB 3.0, and SD card.',    39.99, 45,  'Electronics'),
    ('Laptop Stand',        'Aluminium adjustable laptop stand for 11–17" laptops.', 34.99, 60,  'Accessories'),
    ('Webcam HD',           '1080p HD webcam with built-in microphone.',             59.99, 25,  'Electronics'),
    ('Desk Lamp',           'LED desk lamp with adjustable colour temperature.',     24.99, 80,  'Home Office'),
    ('Notebook A5',         'Dotted A5 notebook, 200 pages, hardcover.',              9.99, 120, 'Stationery'),
    ('Cable Organiser',     'Silicone cable clips for desk management.',              7.99, 200, 'Accessories'),
    ('Monitor Arm',         'Single monitor arm, supports up to 27" screens.',      49.99, 20,  'Accessories'),
    ('Mouse Pad XL',        'Extended mouse pad 900×400 mm, stitched edges.',       19.99, 75,  'Accessories'),
]

def hash_pw(plain):
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

with app.app_context():
    db.drop_all()
    db.create_all()

    # Users
    admin = User(username='admin', email='admin@vulnshop.local',
                 password_hash=hash_pw('Admin1234!'), role='admin')
    alice = User(username='alice', email='alice@example.com',
                 password_hash=hash_pw('Alice1234!'))
    bob   = User(username='bob',   email='bob@example.com',
                 password_hash=hash_pw('Bob1234!'))
    db.session.add_all([admin, alice, bob])
    db.session.flush()

    # Products
    products = []
    for name, desc, price, stock, cat in PRODUCTS:
        p = Product(name=name, description=desc, price=price, stock=stock, category=cat)
        db.session.add(p)
        products.append(p)
    db.session.flush()

    # Sample order for alice
    order = Order(user_id=alice.id, total=109.98, status='delivered',
                  created_at=datetime(2026, 4, 1))
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderItem(order_id=order.id, product_id=products[0].id,
                             quantity=1, unit_price=products[0].price))
    db.session.add(OrderItem(order_id=order.id, product_id=products[1].id,
                             quantity=1, unit_price=products[1].price))

    # Sample reviews
    db.session.add(Review(user_id=alice.id, product_id=products[0].id,
                          text='Great mouse, very comfortable!', rating=5))
    db.session.add(Review(user_id=bob.id, product_id=products[0].id,
                          text='Good value for money.', rating=4))
    db.session.add(Review(user_id=bob.id, product_id=products[1].id,
                          text='Clicky and satisfying to type on.', rating=5))

    db.session.commit()
    print("Database seeded.")
    print("  admin  / Admin1234!")
    print("  alice  / Alice1234!")
    print("  bob    / Bob1234!")
