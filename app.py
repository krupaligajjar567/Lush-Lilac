from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lush_lilac.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'lushlilac30@gmail.com'  # <-- Replace with your email
app.config['MAIL_PASSWORD'] = 'cdct znqj rdhy eyfy'     # <-- Replace with your app password
app.config['MAIL_DEFAULT_SENDER'] = 'lushlilac30@gmail.com'  # <-- Replace with your email
app.config['RAZORPAY_KEY_ID'] = 'rzp_test_rzL2OfNMDQTHdN'
app.config['RAZORPAY_KEY_SECRET'] = 'GJiZl9ZACUFfyrT4m5VzlEGh'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

mail = Mail(app)

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    user_type = db.Column(db.String(20), default='customer')  # 'customer' or 'admin'
    orders = db.relationship('Order', backref='user', lazy=True)
    wishlists = db.relationship('Wishlist', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(255))  # New field for image filename
    category = db.Column(db.String(50))  # New field for category
    is_bestseller = db.Column(db.Boolean, default=False) # New field for bestseller status
    is_new = db.Column(db.Boolean, default=False) # New field for new arrival status
    is_new_arrival = db.Column(db.Boolean, default=False) # New field for new arrival status
    wishlists = db.relationship('Wishlist', backref='product', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    total_amount = db.Column(db.Float, nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)
    customer_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    payment_method = db.Column(db.String(50), default='Credit Card')
    payment_status = db.Column(db.String(20), default='Paid')
    tracking_number = db.Column(db.String(50))
    razorpay_order_id = db.Column(db.String(100), unique=True, nullable=True) # Add field to store Razorpay order ID

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    model = db.Column(db.String(100))  # Add model field for customization
    custom_image = db.Column(db.String(255))  # New field for customization image

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    model = db.Column(db.String(100))  # New field for phone model
    custom_image = db.Column(db.String(255))  # New field for customization image
    product = db.relationship('Product')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    # Fetch bestseller products for the homepage
    bestsellers = Product.query.filter_by(is_bestseller=True).all()
    
    # Fetch new arrival products for the homepage (latest 10)
    new_arrivals = Product.query.filter_by(is_new_arrival=True).order_by(Product.id.desc()).limit(10).all()

    print(f"Debug: New Arrivals fetched in index route: {[p.name for p in new_arrivals]}") # Debug print product names

    # You might also want to fetch a few other featured products for the main section,
    # but for now, let's just pass bestsellers and new arrivals.

    return render_template('index.html', 
                           bestsellers=bestsellers,
                           new_arrivals=new_arrivals)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject', 'Message from Lush Lilac Website')
        message_content = request.form.get('message')
        
        # Send email to admin
        try:
            msg = Message(
                subject=f"Contact Form: {subject}",
                recipients=[app.config['MAIL_USERNAME']],
                html=f"""
                <div style='font-family:Quicksand,sans-serif; padding:24px; color:#7D5E7A;'>
                    <h2>New message from {name}</h2>
                    <p><strong>From:</strong> {name} ({email})</p>
                    <p><strong>Subject:</strong> {subject}</p>
                    <h3>Message:</h3>
                    <p>{message_content}</p>
                </div>
                """
            )
            mail.send(msg)
            
            # Send confirmation to user
            user_msg = Message(
                subject="Thank you for contacting Lush Lilac",
                recipients=[email],
                html=f"""
                <div style='font-family:Quicksand,sans-serif; background:#FFF9FD; padding:24px; color:#7D5E7A;'>
                    <h2>Thank you for reaching out, {name}!</h2>
                    <p>We've received your message and will get back to you shortly.</p>
                    <p>For reference, here's a copy of your message:</p>
                    <div style='background:#F9F0F7; padding:15px; border-radius:8px; margin:15px 0;'>
                        <p><strong>Subject:</strong> {subject}</p>
                        <p>{message_content}</p>
                    </div>
                    <p>With love,<br>Lush Lilac Team</p>
                </div>
                """
            )
            mail.send(user_msg)
            
            flash('Thank you for your message! We will get back to you soon.', 'success')
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            flash('There was an error sending your message. Please try again later.', 'error')
        
        return redirect(url_for('contact'))

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()

        print(f"Registration attempt - Username: {username}, Email: {email}")

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Username already exists: {username}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Username already exists'}), 400
            flash('Username already exists')
            return redirect(url_for('index'))
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            print(f"Email already registered: {email}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Email already registered'}), 400
            flash('Email already registered')
            return redirect(url_for('index'))

        # Create new user
        user = User(username=username, email=email, user_type='customer')
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            print(f"User created successfully: {username}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Registration successful! Please login.'})
            flash('Registration successful! Please login.')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'An error occurred during registration'}), 500
            flash('An error occurred during registration')
            return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username').strip()
    password = request.form.get('password').strip()
    
    print(f"Login attempt for username: {username}")  # Debug print
    
    user = User.query.filter_by(username=username).first()
    print(f"User found: {user is not None}")  # Debug print
    
    if user and user.check_password(password):
        print("Password check passed")  # Debug print
        login_user(user)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': 'Login successful!',
                'username': user.username,
                'redirect': url_for('index')
            })
        flash('Login successful!', 'success')
        return redirect(url_for('index'))
    else:
        print("Login failed - Invalid credentials")  # Debug print
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': 'Invalid username or password'
            }), 401
        flash('Invalid username or password', 'error')
        return redirect(url_for('index'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, user_type='admin').first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Welcome to admin dashboard!')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials')
            return redirect(url_for('admin_login'))
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.user_type != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    # Get statistics
    total_orders = Order.query.count()
    total_customers = User.query.filter_by(user_type='customer').count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    pending_orders = Order.query.filter_by(status='pending').count()
    
    # Get recent orders (last 10)
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(10).all()
    
    # Get all customers
    customers = User.query.filter_by(user_type='customer').all()
    
    # Debug: Print variables being passed to the template
    print(f"Debug -- total_orders: {total_orders}")
    print(f"Debug -- total_customers: {total_customers}")
    print(f"Debug -- total_revenue: {total_revenue}")
    print(f"Debug -- pending_orders: {pending_orders}")
    print(f"Debug -- recent_orders: {recent_orders}")
    # For recent_orders, print details of the first few to check structure and values
    if recent_orders:
        print("Debug -- Details of first recent order:")
        print(f"  ID: {recent_orders[0].id}")
        print(f"  Date: {recent_orders[0].order_date}")
        print(f"  Total Amount: {recent_orders[0].total_amount}")
        print(f"  Status: {recent_orders[0].status}")
        if recent_orders[0].user:
            print(f"  User: {recent_orders[0].user.username}")
        else:
            print("  User: None")
        if recent_orders[0].items:
            print(f"  Number of Items: {len(recent_orders[0].items)}")
            print(f"  First Item Product Name: {recent_orders[0].items[0].product_name if recent_orders[0].items[0].product_name else 'None'}")
        else:
            print("  Items: None or Empty")
    else:
        print("Debug -- recent_orders is empty")
    print(f"Debug -- customers count: {len(customers)}")
    
    return render_template('admin_dashboard.html',
                         total_orders=total_orders,
                         total_customers=total_customers,
                         total_revenue=total_revenue,
                         pending_orders=pending_orders,
                         recent_orders=recent_orders,
                         customers=customers)

@app.route('/admin/orders')
@login_required
def admin_orders():
    if current_user.user_type != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    # Get filter parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    product_search = request.args.get('product')
    status = request.args.get('status')
    
    # Build query
    query = Order.query
    
    # Apply filters if provided
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Order.order_date >= date_from)
        except ValueError:
            flash('Invalid date format for "Date From"')
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            # Add a day to include the end date
            date_to = date_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Order.order_date <= date_to)
        except ValueError:
            flash('Invalid date format for "Date To"')
    
    if status:
        query = query.filter(Order.status == status)
    
    # Get orders (sorted by most recent first)
    orders = query.order_by(Order.order_date.desc()).all()
    
    # Filter by product if specified
    if product_search:
        filtered_orders = []
        product_search = product_search.lower()
        for order in orders:
            for item in order.items:
                if product_search in item.product_name.lower():
                    filtered_orders.append(order)
                    break
        orders = filtered_orders
    
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>/details')
@login_required
def admin_order_details_json(order_id):
    if current_user.user_type != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    order = Order.query.get_or_404(order_id)
    items = []
    
    for item in order.items:
        items.append({
            'product_name': item.product_name,
            'quantity': item.quantity,
            'price': item.price,
            'model': item.model or '',
            'custom_image': item.custom_image or ''  # Add custom image to response
        })
    
    # Get customer details from the order or user
    customer_name = order.customer_name or order.user.username
    email = order.email or order.user.email
    
    order_data = {
        'id': order.id,
        'order_date': order.order_date.strftime('%Y-%m-%d %H:%M'),
        'status': order.status,
        'total_amount': order.total_amount,
        'items': items,
        'customer_name': customer_name,
        'email': email,
        'phone': order.phone or 'Not provided',
        'address': order.address or 'Not provided',
        'payment_method': order.payment_method,
        'payment_status': order.payment_status,
        'tracking_number': order.tracking_number
    }
    
    return jsonify({'success': True, 'order': order_data})

@app.route('/admin/order/<int:order_id>/update', methods=['POST'])
@login_required
def admin_update_order_extended(order_id):
    if current_user.user_type != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    tracking_number = request.form.get('tracking_number')
    
    if new_status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
        order.status = new_status
        if tracking_number:
            order.tracking_number = tracking_number
        
        db.session.commit()
        flash(f'Order #{order_id} status updated to {new_status.title()}')
        
        # Send notification email to customer if the order status has changed
        try:
            if order.email:
                status_message = {
                    'processing': 'your order is now being processed',
                    'shipped': 'your order has been shipped',
                    'delivered': 'your order has been delivered',
                    'cancelled': 'your order has been cancelled'
                }.get(new_status, f'your order status has been updated to {new_status}')
                
                tracking_info = ""
                if tracking_number and new_status == 'shipped':
                    tracking_info = f"<p>Your tracking number is: <strong>{tracking_number}</strong></p>"
                
                msg = Message(
                    subject=f'Order #{order_id} Status Update - Lush Lilac',
                    recipients=[order.email],
                    html=f"""
                    <div style='font-family:Quicksand,sans-serif; background:#FFF9FD; padding:24px; color:#7D5E7A;'>
                        <h2>Order Status Update</h2>
                        <p>Dear {order.customer_name or order.user.username},</p>
                        <p>We're writing to let you know that {status_message}.</p>
                        {tracking_info}
                        <p>You can check the details of your order by logging into your account.</p>
                        <p>Thank you for shopping with Lush Lilac!</p>
                    </div>
                    """
                )
                mail.send(msg)
        except Exception as e:
            print(f"Error sending status update email: {str(e)}")
    else:
        flash('Invalid status')
    
    return redirect(url_for('admin_orders'))

@app.route('/admin/customer/<int:customer_id>')
@login_required
def admin_customer_details(customer_id):
    if current_user.user_type != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    customer = User.query.get_or_404(customer_id)
    orders = Order.query.filter_by(user_id=customer_id).order_by(Order.order_date.desc()).all()
    return render_template('admin_customer_details.html', customer=customer, orders=orders)

@app.route('/my_orders')
@login_required
def my_orders():
    try:
        # Get all orders for the current user
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
        
        # If no orders exist, create a sample order
        if not orders:
            sample_order = Order(
                user_id=current_user.id,
                order_date=datetime.utcnow(),
                status='pending',
                total_amount=29.99
            )
            db.session.add(sample_order)
            
            # Add a sample order item
            sample_item = OrderItem(
                order=sample_order,
                product_name='Sample Product',
                quantity=1,
                price=29.99
            )
            db.session.add(sample_item)
            
            try:
                db.session.commit()
                orders = [sample_order]
            except Exception as e:
                db.session.rollback()
                print(f"Error creating sample order: {str(e)}")
                flash('Error creating sample order')
        
        return render_template('my_orders.html', orders=orders)
    except Exception as e:
        print(f"Error in my_orders route: {str(e)}")
        flash('Error loading orders')
        return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully!')
    return redirect(url_for('index'))

@app.route('/admin/update_password', methods=['POST'])
@login_required
def update_admin_password():
    if current_user.user_type != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    new_password = request.form.get('new_password')
    if new_password:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Admin password updated successfully')
    else:
        flash('Invalid password')
    
    return redirect(url_for('admin_dashboard'))

# Create admin user if not exists
def create_admin():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@lushlilac.com', user_type='admin')
        admin.set_password('Lushlilac!3031')  # Change this to your desired password
        db.session.add(admin)
        db.session.commit()

# Initialize database and create admin user
with app.app_context():
    db.create_all()
    create_admin()

@app.route('/wishlist')
def view_wishlist():
    if not current_user.is_authenticated:
        flash('Please log in to view your wishlist', 'info')
        return redirect(url_for('index'))
    
    try:
        # Get all wishlist items for the current user
        wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
        # Extract products from wishlist items
        products = [item.product for item in wishlist_items if item.product]
        return render_template('wishlist.html', products=products)
    except Exception as e:
        print(f"Error loading wishlist: {str(e)}")
        flash('Error loading wishlist. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/add_to_wishlist/<int:product_id>', methods=['POST'])
def add_to_wishlist(product_id):
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please log in to add items to your wishlist'})
    
    try:
        # Check if product exists
        product = Product.query.get_or_404(product_id)
        
        # Check if already in wishlist
        existing_item = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()
        
        if existing_item:
            return jsonify({'success': False, 'message': 'Item is already in your wishlist'})
        
        # Add to wishlist
        wishlist_item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Added to wishlist successfully',
            'wishlist_count': len(current_user.wishlists)
        })
    except Exception as e:
        print(f"Error adding to wishlist: {str(e)}")
        return jsonify({'success': False, 'message': 'Error adding to wishlist. Please try again.'})

@app.route('/remove_from_wishlist/<int:product_id>', methods=['POST'])
def remove_from_wishlist(product_id):
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please log in to remove items from your wishlist'})
    
    try:
        # Find and remove the wishlist item
        wishlist_item = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()
        
        if wishlist_item:
            db.session.delete(wishlist_item)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Removed from wishlist successfully',
                'wishlist_count': len(current_user.wishlists)
            })
        else:
            return jsonify({'success': False, 'message': 'Item not found in wishlist'})
    except Exception as e:
        print(f"Error removing from wishlist: {str(e)}")
        return jsonify({'success': False, 'message': 'Error removing from wishlist. Please try again.'})

@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if current_user.user_type != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    categories = [
        'Phone Cases', 'Mouse Pads', 'Candles', 'Bags', 'Glass Tumblers', 'Nails', 'Accessories', 'Decors', 'Stationary'
    ]
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        stock = request.form.get('stock')
        category = request.form.get('category')
        image_file = request.files.get('image')
        image_filename = None
        if image_file and image_file.filename:
            image_filename = image_file.filename
            image_dir = os.path.join('static', 'images')
            os.makedirs(image_dir, exist_ok=True)
            image_path = os.path.join(image_dir, image_filename)
            image_file.save(image_path)
        if not name or not price or not stock or not category:
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('admin_add_product'))
        try:
            product = Product(
                name=name,
                description=description,
                price=float(price),
                stock=int(stock),
                image=image_filename,
                category=category
            )
            db.session.add(product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin_add_product'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding product: ' + str(e), 'error')
            return redirect(url_for('admin_add_product'))
    # GET: show form and product list
    products = Product.query.all()
    return render_template('admin_add_product.html', products=products, categories=categories)

@app.route('/admin/bestsellers', methods=['GET', 'POST'])
@login_required
def admin_bestsellers():
    if current_user.user_type != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))

    if request.method == 'POST':
        product_id = request.form.get('product_id')
        action = request.form.get('action')
        product = Product.query.get(product_id)

        if product:
            try:
                if action == 'add':
                    product.is_bestseller = True
                    db.session.commit()
                    flash(f'Product "{product.name}" added to Bestsellers!', 'success')
                elif action == 'remove':
                    product.is_bestseller = False
                    db.session.commit()
                    flash(f'Product "{product.name}" removed from Bestsellers!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating bestseller status: {str(e)}', 'error')
        else:
            flash('Product not found', 'error')

        return redirect(url_for('admin_bestsellers'))

    # GET request
    bestsellers = Product.query.filter_by(is_bestseller=True).all()
    all_products = Product.query.all()
    return render_template('admin_bestsellers.html', bestsellers=bestsellers, all_products=all_products)

@app.route('/admin/new_arrivals', methods=['GET', 'POST'])
@login_required
def admin_new_arrivals():
    if current_user.user_type != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))

    if request.method == 'POST':
        product_id = request.form.get('product_id')
        action = request.form.get('action')
        product = Product.query.get(product_id)

        if product:
            try:
                if action == 'add':
                    product.is_new_arrival = True
                    db.session.commit()
                    flash(f'Product "{product.name}" added to New Arrivals!', 'success')
                elif action == 'remove':
                    product.is_new_arrival = False
                    db.session.commit()
                    flash(f'Product "{product.name}" removed from New Arrivals!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating new arrival status: {str(e)}', 'error')
        else:
            flash('Product not found', 'error')

        return redirect(url_for('admin_new_arrivals'))

    # GET request
    new_arrivals = Product.query.filter_by(is_new_arrival=True).order_by(Product.id.desc()).all()
    all_products = Product.query.all()
    return render_template('admin_new_arrivals.html', new_arrivals=new_arrivals, all_products=all_products)

@app.route('/category/<category_name>')
def category_products(category_name):
    products = Product.query.filter(Product.category.ilike(category_name)).all()
    return render_template('category_products.html', products=products, category_name=category_name)

@app.route('/product/<product_id>')
def product_detail(product_id):
    # Fetch product details based on product_id
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/products')
def products_list():
    """Route to display a list of products based on provided IDs."""
    product_ids_str = request.args.get('ids')
    products = []
    if product_ids_str:
        try:
            # Split the comma-separated string of IDs and convert to integers
            product_ids = [int(id) for id in product_ids_str.split(',')]
            # Fetch products from the database using the list of IDs
            products = Product.query.filter(Product.id.in_(product_ids)).all()
        except ValueError:
            # Handle cases where IDs are not valid integers
            flash('Invalid product IDs provided.', 'error')
            return redirect(url_for('index')) # Redirect to index or an error page

    # Render the products_list.html template, passing the fetched products
    return render_template('products_list.html', products=products)

@app.route('/new-arrivals')
def new_arrivals_page():
    """Route to display the 20 most recently added products."""
    # Fetch the latest 20 products ordered by ID (assuming higher ID is more recent)
    latest_products = Product.query.order_by(Product.id.desc()).limit(20).all()
    
    # Render the products_list.html template, passing the fetched products
    # We can reuse products_list.html as it's designed to display a list of products
    return render_template('products_list.html', products=latest_products)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    try:
        print(f"Add to cart request for product ID: {product_id}")
        print(f"Form data: {request.form}")
        
        action = request.form.get('action', 'add')
        quantity = int(request.form.get('quantity', 1))
        model = request.form.get('model', '')
        
        # Handle custom image upload
        custom_image = None
        if 'custom_image' in request.files:
            file = request.files['custom_image']
            if file and file.filename:
                # Create a unique filename
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                # Save the file
                file_path = os.path.join('static', 'custom_uploads', filename)
                file.save(file_path)
                custom_image = filename
        
        print(f"Action: {action}, Quantity: {quantity}, Model: {model}")
        
        # Get product
        product = Product.query.get_or_404(product_id)
        
        # Check if item is already in cart with the same model
        cart_item = CartItem.query.filter_by(
            user_id=current_user.id, 
            product_id=product_id,
            model=model
        ).first()
        
        # Add or update cart item
        if cart_item:
            cart_item.quantity += quantity
            if custom_image:  # Update custom image if provided
                cart_item.custom_image = custom_image
            print(f"Updated existing cart item, new quantity: {cart_item.quantity}")
        else:
            cart_item = CartItem(
                user_id=current_user.id, 
                product_id=product_id, 
                quantity=quantity,
                model=model,
                custom_image=custom_image
            )
            db.session.add(cart_item)
            print(f"Added new cart item with model: {model}")
        
        db.session.commit()
        print("Database committed successfully")
        
        # Update cart count
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        cart_count = sum(item.quantity for item in cart_items)
        
        flash(f'Added {product.name} to cart successfully!', 'success')
        return redirect(url_for('view_cart'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding to cart: {str(e)}")
        flash(f'Error adding to cart: {str(e)}', 'error')
        return redirect(url_for('product_detail', product_id=product_id))

@app.route('/cart')
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    try:
        data = request.get_json()
        if not data:
            data = request.form.to_dict()
        
        action = data.get('action')
        quantity = int(data.get('quantity', 1))
        model = data.get('model', '')
        
        cart_item = CartItem.query.filter_by(
            user_id=current_user.id, 
            product_id=product_id,
            model=model
        ).first()
        
        product = Product.query.get_or_404(product_id)

        if action == 'add':
            if not cart_item:
                cart_item = CartItem(
                    user_id=current_user.id, 
                    product_id=product_id, 
                    quantity=quantity,
                    model=model
                )
                db.session.add(cart_item)
            else:
                cart_item.quantity += quantity
            
            db.session.commit()
            cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
            total = sum(item.product.price * item.quantity for item in cart_items)
            cart_count = sum(item.quantity for item in cart_items)
            
            return jsonify({
                'success': True, 
                'message': 'Added to cart successfully',
                'cart_count': cart_count, 
                'total': total
            })
            
        elif action == 'update':
            if cart_item:
                cart_item.quantity = quantity
                db.session.commit()
                cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
                total = sum(item.product.price * item.quantity for item in cart_items)
                subtotal = cart_item.product.price * cart_item.quantity
                cart_count = sum(item.quantity for item in cart_items)
                return jsonify(success=True, total=total, subtotal=subtotal, cart_count=cart_count)
            else:
                return jsonify(success=False, message='Item not in cart')
                
        elif action == 'remove':
            if cart_item:
                db.session.delete(cart_item)
                db.session.commit()
                cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
                total = sum(item.product.price * item.quantity for item in cart_items)
                return jsonify(success=True, total=total)
            else:
                return jsonify(success=False, message='Item not in cart')
        else:
            return jsonify(success=False, message='Invalid action')
            
    except Exception as e:
        print(f"Error in update_cart: {str(e)}")
        db.session.rollback()
        return jsonify(success=False, message='Error updating cart. Please try again.')

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not current_user.is_authenticated:
        flash('Please log in to checkout', 'info')
        return redirect(url_for('login'))
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    if not cart_items:
        flash('Your cart is empty!')
        return redirect(url_for('cart'))
    if request.method == 'POST':
        # Save details to session (or DB in real app)
        session['checkout_details'] = {
            'name': request.form.get('name'),
            'address': request.form.get('address'),
            'pincode': request.form.get('pincode'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email')
        }
        return redirect(url_for('payment'))
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if not current_user.is_authenticated:
        flash('Please log in to continue', 'info')
        return redirect(url_for('login'))
    checkout_details = session.get('checkout_details')
    if not checkout_details:
        flash('Please fill in your details first')
        return redirect(url_for('checkout'))
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    if not cart_items:
        flash('Your cart is empty!')
        return redirect(url_for('cart'))
        
    # Convert total to paise (Razorpay requires amount in the smallest currency unit)
    amount_paise = int(total * 100)
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        
        if payment_method == 'COD':
            # Create a new Order in your database
            new_order = Order(
                user_id=current_user.id,
                order_date=datetime.utcnow(),
                status='pending',
                total_amount=total,
                customer_name=checkout_details.get('name'),
                email=checkout_details.get('email'),
                phone=checkout_details.get('phone'),
                address=checkout_details.get('address'),
                payment_method=payment_method
            )
            
            # For COD, create order items immediately
            for cart_item in cart_items:
                order_item = OrderItem(
                    order=new_order,
                    product_name=cart_item.product.name,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    model=cart_item.model,
                    custom_image=cart_item.custom_image
                )
                db.session.add(order_item)
            
            # Clear the cart
            CartItem.query.filter_by(user_id=current_user.id).delete()
            session.pop('checkout_details', None)
            
            try:
                db.session.add(new_order)
                db.session.commit()
                
                # Send confirmation email for COD order
                try:
                    msg = Message(
                        subject='Order Confirmation - Lush Lilac',
                        recipients=[checkout_details['email']],
                        html=f"""
                        <div style='font-family:Quicksand,sans-serif; background:#FFF9FD; padding:24px; color:#7D5E7A;'>
                            <div style='text-align:center; margin-bottom:24px;'>
                                <img src='http://127.0.0.1:5000/static/images/logo.png' alt='Lush Lilac Logo' style='height:60px;'>
                            </div>
                            <h2 style='text-align:center;'>Thank you for your order, {checkout_details['name']}!</h2>
                            <p>Your order has been confirmed. Here are your order details:</p>
                            <p><strong>Order ID:</strong> #{new_order.id}</p>
                            <p><strong>Payment Method:</strong> Cash on Delivery</p>
                            <ul>
                                {''.join([f'<li>{item.product_name} × {item.quantity}: ₹{item.price * item.quantity:.2f}</li>' for item in new_order.items])}
                            </ul>
                            <p><strong>Total:</strong> ₹{total:.2f}</p>
                            <h4>Shipping Address:</h4>
                            <p>
                                {checkout_details['address']}<br>
                                Phone: {checkout_details['phone']}<br>
                                Email: {checkout_details['email']}
                            </p>
                            <p style='margin-top:32px;'>With love,<br>Lush Lilac Team</p>
                        </div>
                        """
                    )
                    mail.send(msg)
                except Exception as e:
                    print(f"Error sending confirmation email for COD order: {str(e)}")
                
                flash('Order placed successfully! You will receive a confirmation email shortly.', 'success')
                return redirect(url_for('my_orders'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error processing order: {str(e)}', 'error')
                return redirect(url_for('checkout'))
        
        # For Razorpay payment (This part might not be strictly needed anymore as order is created on GET, but keeping for potential future use)
        # If you have other online payment methods, this is where you'd handle them.
        # The Razorpay initiation is now handled on the GET request.
        pass # The actual Razorpay payment happens client-side after GET render
    
    # GET request - Show payment options and prepare for Razorpay
    try:
        import razorpay
        client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))
        
        # Create a Razorpay Order on GET request
        razorpay_order = client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': f'order_rcpt_{datetime.utcnow().timestamp()}',
            'notes': {
                'user_id': current_user.id,
                'email': checkout_details.get('email'),
                'phone': checkout_details.get('phone')
            }
        })
        razorpay_order_id = razorpay_order['id']
        print(f"Razorpay Order Created on GET: {razorpay_order_id}") # Debug print

        # Create a new Order in your database and link it to the Razorpay order ID
        # Set status to 'pending' or 'initiated'
        new_order = Order(
            user_id=current_user.id,
            order_date=datetime.utcnow(),
            status='initiated', # Set status to initiated for online payments
            total_amount=total,
            customer_name=checkout_details.get('name'),
            email=checkout_details.get('email'),
            phone=checkout_details.get('phone'),
            address=checkout_details.get('address'),
            payment_method='Razorpay',
            razorpay_order_id=razorpay_order_id # Store the Razorpay order ID
        )
        db.session.add(new_order)
        db.session.commit()
        print(f"Local Order Initiated on GET with ID: {new_order.id} and Razorpay ID: {new_order.razorpay_order_id}") # Debug print

    except Exception as e:
        print(f"Error creating Razorpay Order or initiating local order on GET: {str(e)}") # Updated error message
        flash(f'Error preparing for payment: {str(e)}', 'error')
        return redirect(url_for('checkout'))
        
    # Pass necessary data to the payment template
    return render_template('payment.html', 
                           checkout_details=checkout_details, 
                           cart_items=cart_items, 
                           total=total,
                           razorpay_key_id=app.config['RAZORPAY_KEY_ID'],
                           razorpay_order_id=razorpay_order_id,
                           amount=amount_paise
                          )

@app.route('/admin/product/<int:product_id>')
@login_required
def get_product(product_id):
    if current_user.user_type != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock,
            'category': product.category,
            'image': product.image
        }
    })

@app.route('/admin/product/<int:product_id>/edit', methods=['POST'])
@login_required
def edit_product(product_id):
    if current_user.user_type != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    action = request.form.get('action')

    try:
        if action == 'toggle_bestseller':
            product.is_bestseller = not product.is_bestseller
            db.session.commit()
            print(f"Debug: Product {product.name} bestseller status toggled to {product.is_bestseller}") # Debug print
            status = "Bestseller" if product.is_bestseller else "not Bestseller"
            flash(f'Product "{product.name}" is now {status}!', 'success')
        elif action == 'toggle_new_arrival':
            product.is_new_arrival = not product.is_new_arrival
            db.session.commit()
            status = "New Arrival" if product.is_new_arrival else "not New Arrival"
            flash(f'Product "{product.name}" is now {status}!', 'success')
        else: # Default action is update
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price')
            stock = request.form.get('stock')
            category = request.form.get('category')
            image_file = request.files.get('image')

            if not name or not price or not stock or not category:
                flash('Please fill in all required fields', 'error')
                # Keep the user on the edit page if possible, maybe pass product_id back
                return redirect(url_for('admin_add_product')) # Redirecting to add page as a fallback

            # Update product fields
            product.name = name
            product.description = description
            product.price = float(price)
            product.stock = int(stock)
            product.category = category

            # Update image if provided
            if image_file and image_file.filename:
                image_filename = image_file.filename
                image_dir = os.path.join('static', 'images')
                os.makedirs(image_dir, exist_ok=True)
                image_path = os.path.join(image_dir, image_filename)
                image_file.save(image_path)
                product.image = image_filename

            db.session.commit()
            flash('Product updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error processing product update: {str(e)}', 'error')
    
    return redirect(url_for('admin_add_product')) # Redirect back to the product listing page

@app.route('/admin/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    if current_user.user_type != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    try:
        # Delete associated cart items first to avoid foreign key constraints
        CartItem.query.filter_by(product_id=product_id).delete()
        
        # Delete associated wishlist items
        Wishlist.query.filter_by(product_id=product_id).delete()
        
        # Delete the product
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')
    
    return redirect(url_for('admin_add_product'))

@app.route('/admin/product/<int:product_id>/toggle-stock', methods=['POST'])
@login_required
def toggle_product_stock(product_id):
    if current_user.user_type != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    product = Product.query.get_or_404(product_id)
    
    try:
        # If stock is 0, set it to 10, otherwise set it to 0
        if product.stock == 0:
            product.stock = 10
            message = f'Product "{product.name}" is now in stock'
        else:
            product.stock = 0
            message = f'Product "{product.name}" is now out of stock'
        
        db.session.commit()
        return jsonify({'success': True, 'message': message, 'stock': product.stock})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/shop')
def shop():
    # Fetch bestseller products
    bestsellers = Product.query.filter_by(is_bestseller=True).all()
    print(f"Debug: Bestsellers fetched: {[p.name for p in bestsellers]}") # Debug print product names
    
    # Fetch new arrival products
    new_arrivals = Product.query.filter_by(is_new_arrival=True).order_by(Product.id.desc()).limit(10).all() # Assuming higher ID means newer
    print(f"Debug: New Arrivals fetched: {[p.name for p in new_arrivals]}") # Debug print product names

    # Fetch all other products, excluding bestsellers and new arrivals
    bestseller_ids = [p.id for p in bestsellers]
    new_arrival_ids = [p.id for p in new_arrivals]
    excluded_ids = bestseller_ids + new_arrival_ids

    all_products = Product.query.filter(~Product.id.in_(excluded_ids)).all()
    print(f"Debug: Other Products fetched: {[p.name for p in all_products]}") # Debug print product names

    return render_template('shop.html', 
                           bestsellers=bestsellers,
                           new_arrivals=new_arrivals,
                           all_products=all_products)

@app.route('/razorpay_callback')
def razorpay_callback():
    if not current_user.is_authenticated:
        flash('Please log in to complete your order', 'info')
        return redirect(url_for('login'))

    razorpay_order_id = request.args.get('order_id')
    razorpay_payment_id = request.args.get('payment_id')
    razorpay_signature = request.args.get('signature')

    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        flash('Payment failed or cancelled.', 'error')
        # You might want to redirect to a specific order failure page
        return redirect(url_for('view_cart')) 

    try:
        import razorpay
        client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))

        # Verify the payment signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        client.utility.verify_payment_signature(params_dict)

        # If verification succeeds, find the order and update its status
        # We need to find the order based on the Razorpay order ID.
        # For now, let's assume we can find the corresponding Order based on something else, e.g., user and latest pending order.
        # A better approach would be to store razorpay_order_id in the Order model.
        # Let's quickly add razorpay_order_id to the Order model and update the checkout process.
        
        # **IMPORTANT:** The following lines to find and update the order are temporary.
        # We will refine this by adding razorpay_order_id to the Order model next.
        
        # Find the order using the razorpay_order_id received in the callback
        order = Order.query.filter_by(razorpay_order_id=razorpay_order_id).first()

        if order:
            # Update the order status to 'completed' or 'processing'
            order.status = 'processing' # Or 'completed' depending on your workflow
            # Store payment details (optional but recommended)
            # order.razorpay_payment_id = razorpay_payment_id # Requires adding this field to Order model
            # order.razorpay_order_id = razorpay_order_id # Requires adding this field to Order model
            db.session.commit() # Commit the order status update first
            
            # Now, create the OrderItems from the CartItems and clear the cart
            # This logic was previously in the POST of the /payment route
            cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
            for cart_item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_name=cart_item.product.name,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    model=cart_item.model,
                    custom_image=cart_item.custom_image
                )
                db.session.add(order_item)
                
            CartItem.query.filter_by(user_id=current_user.id).delete()
            session.pop('checkout_details', None) # Clear checkout details from session
            db.session.commit() # Commit order items creation and cart clearing
            
            # Send confirmation email (copying from previous payment route logic)
            try:
                checkout_details = {
                     'name': order.customer_name or current_user.username,
                     'email': order.email or current_user.email,
                     'phone': order.phone or '',
                     'address': order.address or '',
                     'pincode': '' # Pincode might be part of address string now
                 }
                # Re-fetch cart items for email content (they are deleted now, so this is problematic)
                # We should create OrderItems *before* clearing the cart or fetch details from the Order object
                # Let's use the order.items relationship which we populated above
                item_lines = '\n'.join([
                     f"- {item.product_name} × {item.quantity}: ₹{item.price * item.quantity:.2f}" for item in order.items # Use order.items
                 ])
                total = order.total_amount # Use total from order

                msg = Message(
                    subject='Order Confirmation - Lush Lilac',
                    recipients=[checkout_details['email']],
                    html=f"""
                    <div style='font-family:Quicksand,sans-serif; background:#FFF9FD; padding:24px; color:#7D5E7A;'>
                        <div style='text-align:center; margin-bottom:24px;'>
                            <img src='http://127.0.0.1:5000/static/images/logo.png' alt='Lush Lilac Logo' style='height:60px;'>
                        </div>
                        <h2 style='text-align:center;'>Thank you for your order, {checkout_details['name']}!</h2>
                        <p>Your order has been confirmed. Here are your order details:</p>
                        <p><strong>Order ID:</strong> #{order.id}</p>
                        <ul>
                            {''.join([f'<li>{item.product_name} × {item.quantity}: ₹{item.price * item.quantity:.2f}</li>' for item in order.items])} # Use order.items
                        </ul>
                        <p><strong>Total:</strong> ₹{total:.2f}</p>
                        <h4>Shipping Address:</h4>
                        <p>
                            {checkout_details['address']}<br>
                            Pincode: {checkout_details['pincode']}<br> # Pincode might need parsing from address
                            Phone: {checkout_details['phone']}<br>
                            Email: {checkout_details['email']}
                        </p>
                        <p style='margin-top:32px;'>With love,<br>Lush Lilac Team</p>
                    </div>
                    """
                )
                mail.send(msg)
            except Exception as e:
                print(f"Error sending confirmation email after Razorpay callback: {str(e)}")

            flash('Payment successful! Your order has been placed.', 'success')
            # Redirect to a thank you or order confirmation page
            return redirect(url_for('my_orders')) # Redirect to my_orders or a dedicated success page

        else:
            # Handle case where order is not found (shouldn't happen if flow is correct)
            print(f"Error: Order with Razorpay ID {razorpay_order_id} not found.") # Added debug print
            flash('Error: Corresponding order not found.', 'error')
            return redirect(url_for('view_cart'))

    except Exception as e:
        print(f"Razorpay signature verification failed: {str(e)}")
        flash('Payment verification failed. Please contact support.', 'error')
        # You might want to log this more securely and alert an admin
        return redirect(url_for('view_cart')) # Redirect to cart or an error page

@app.route('/collection/<product_ids_str>')
def featured_collection(product_ids_str):
    # Split the comma-separated string of IDs and convert to integers
    try:
        product_ids = [int(id_str) for id_str in product_ids_str.split(',')]
    except ValueError:
        flash('Invalid product IDs in URL', 'error')
        return redirect(url_for('index')) # Redirect to index if IDs are invalid

    # Fetch products with the given IDs
    products = Product.query.filter(Product.id.in_(product_ids)).all()

    # You can customize the title based on the collection, or pass it from the calling route if needed.
    # For now, let's use a generic title.
    page_title = "Featured Collection"

    return render_template('featured_collection.html', products=products, page_title=page_title)

if __name__ == '__main__':
    app.run(debug=True) 