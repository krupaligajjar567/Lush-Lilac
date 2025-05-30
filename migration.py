from app import app, db, Order, OrderItem
import sqlite3
from flask_migrate import Migrate
import os

# Initialize flask-migrate
migrate = Migrate(app, db)

def add_columns_to_order():
    """Add new columns to the Order table"""
    print("Checking for Order table columns...")
    with app.app_context():
        # Check if database file exists
        db_path = 'instance/lush_lilac.db'
        if not os.path.exists(db_path):
            print(f"Database file {db_path} does not exist.")
            print("Creating database tables...")
            db.create_all()
            print("Database tables created.")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute('PRAGMA table_info("order")')
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns in Order table: {columns}")
        
        # Add new columns if they don't exist
        if 'customer_name' not in columns:
            print("Adding customer_name column...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN customer_name TEXT')
        if 'email' not in columns:
            print("Adding email column...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN email TEXT')
        if 'phone' not in columns:
            print("Adding phone column...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN phone TEXT')
        if 'address' not in columns:
            print("Adding address column...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN address TEXT')
        if 'payment_method' not in columns:
            print("Adding payment_method column...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN payment_method TEXT DEFAULT "Credit Card"')
        if 'payment_status' not in columns:
            print("Adding payment_status column...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN payment_status TEXT DEFAULT "Paid"')
        if 'tracking_number' not in columns:
            print("Adding tracking_number column...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN tracking_number TEXT')
        
        conn.commit()
        conn.close()
        print("Order table updated successfully")

def add_model_to_order_item():
    """Add model column to OrderItem table"""
    print("Checking for OrderItem table columns...")
    with app.app_context():
        # Check if database file exists
        db_path = 'instance/lush_lilac.db'
        if not os.path.exists(db_path):
            print(f"Database file {db_path} does not exist, but should have been created in previous step.")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute('PRAGMA table_info("order_item")')
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns in OrderItem table: {columns}")
        
        # Add model column if it doesn't exist
        if 'model' not in columns:
            print("Adding model column to OrderItem table...")
            cursor.execute('ALTER TABLE "order_item" ADD COLUMN model TEXT')
        
        conn.commit()
        conn.close()
        print("OrderItem table updated successfully")

if __name__ == '__main__':
    print("Running database migration...")
    add_columns_to_order()
    add_model_to_order_item()
    print("Migration completed successfully!") 