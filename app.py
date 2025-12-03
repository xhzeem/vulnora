#!/usr/bin/env python3
"""
VulnerableShop - Deliberately Vulnerable E-commerce Application
EDUCATIONAL PURPOSES ONLY - DO NOT DEPLOY TO PRODUCTION

This application contains INTENTIONAL security vulnerabilities for CTF/training purposes.
"""

from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify, make_response, render_template_string
import psycopg2
import psycopg2.extras
import bcrypt
import os
import time
import hashlib
import subprocess
import urllib.request
from datetime import datetime, timedelta
from functools import wraps
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# INSECURE: Disable auto-escaping for certain templates (XSS vulnerability)
app.jinja_env.autoescape = False

def auto_linkify(text):
    """
    VULNERABLE: Automatically convert URLs in text to clickable links
    WITHOUT proper sanitization or escaping!
    
    This allows XSS via malicious URLs like:
    http://google.com/'onmouseover='alert()
    
    Which becomes:
    <a href='http://google.com/'onmouseover='alert()'>link</a>
    Breaking out of the href attribute to inject event handlers!
    """
    import re
    
    # Find URLs (http://, https://, www.)
    url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
    
    def replace_url(match):
        url = match.group(0)
        # INSECURE: No sanitization! Direct insertion into href attribute
        # This allows breaking out with quotes and injecting JavaScript
        return f"<a href=\"{url}\">{url}</a>"
    
    # Replace all URLs with links
    return re.sub(url_pattern, replace_url, text)

def get_db():
    """Get database connection"""
    return psycopg2.connect(Config.DATABASE_URI, cursor_factory=psycopg2.extras.RealDictCursor)

def login_required(f):
    """Decorator for routes that require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator for admin-only routes - VULNERABLE to IDOR"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Admin access required', 'danger')
            return redirect(url_for('login'))
        # INSECURE: Only check if logged in, not if actually admin
        # Can be bypassed by manipulating session or user data
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# PUBLIC PAGES
# ============================================================================

@app.route('/')
def home():
    """Homepage with featured products"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get featured products (first 8)
    cursor.execute("SELECT * FROM products WHERE is_active = TRUE LIMIT 8")
    featured_products = cursor.fetchall()
    
    # Get categories
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('home.html', products=featured_products, categories=categories)

@app.route('/about')
def about():
    """About us page"""
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form - VULNERABLE to XSS"""
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        message = request.form.get('message', '')
        
        # INSECURE: Reflect user input without sanitization
        flash(f'Thank you {name}! We received your message.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/terms')
def terms():
    """Terms and conditions"""
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    """Privacy policy"""
    return render_template('privacy.html')

# ============================================================================
# AUTHENTICATION - MULTIPLE VULNERABILITIES
# ============================================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration - VULNERABLE to SQL Injection and Username Enumeration"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        display_name = request.form.get('display_name', username)
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # INSECURE: SQL Injection vulnerability in registration
            # Attacker can manipulate the query to create admin accounts
            query = f"SELECT * FROM users WHERE username = '{username}' OR email = '{email}'"
            cursor.execute(query)
            existing_user = cursor.fetchone()
            
            if existing_user:
                # INSECURE: Username enumeration - different messages
                if existing_user['username'] == username:
                    flash('Username already taken', 'danger')
                else:
                    flash('Email already registered', 'danger')
                return redirect(url_for('register'))
            
            # Hash password (at least this part is somewhat secure)
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # INSECURE: SQL Injection in INSERT
            insert_query = f"""
                INSERT INTO users (username, email, password_hash, display_name) 
                VALUES ('{username}', '{email}', '{password_hash}', '{display_name}')
            """
            cursor.execute(insert_query)
            conn.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            # INSECURE: Verbose error messages leak information
            flash(f'Registration error: {str(e)}', 'danger')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login - VULNERABLE to SQL Injection, XSS, No Rate Limiting"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # INSECURE: Error-based SQL Injection - username concatenated directly
            query = f"SELECT * FROM users WHERE username = '{username}'"
            cursor.execute(query)
            user = cursor.fetchone()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                # Successful login
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = user['is_admin']
                
                # Update last login
                cursor.execute(f"UPDATE users SET last_login = NOW() WHERE id = {user['id']}")
                conn.commit()
                
                flash(f'Welcome back, {user["display_name"]}!', 'success')
                
                # Redirect to next page or home
                next_page = request.args.get('next')
                if next_page:
                    # INSECURE: Open redirect vulnerability
                    return redirect(next_page)
                return redirect(url_for('home'))
            else:
                # INSECURE: Reflected XSS - username reflected without sanitization
                error_message = f'Invalid login credentials for user: {username}'
                return render_template('auth/login.html', error=error_message, username=username)
                
        except psycopg2.Error as e:
            # INSECURE: Verbose SQL error messages
            error_message = f'Database error: {str(e)}'
            return render_template('auth/login.html', error=error_message, sql_error=True)
        finally:
            cursor.close()
            conn.close()
    
    return render_template('auth/login.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    """Password reset - VULNERABLE to Logic Flaw (predictable tokens)"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        new_password = request.form.get('new_password', '')
        token = request.form.get('token', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            if not token:
                # Generate reset token - INSECURE: timestamp-based, predictable
                reset_token = hashlib.md5(f"{username}{int(time.time())}".encode()).hexdigest()
                expiry = datetime.now() + timedelta(hours=24)
                
                cursor.execute(
                    f"UPDATE users SET reset_token = '{reset_token}', reset_token_expiry = '{expiry}' WHERE username = '{username}'"
                )
                conn.commit()
                
                flash(f'Password reset token generated: {reset_token}', 'info')
                return render_template('auth/reset_password.html', username=username, show_token=True)
            else:
                # Reset password with token
                # INSECURE: Logic flaw - can bypass if you know the token format
                cursor.execute(
                    f"SELECT * FROM users WHERE username = '{username}' AND reset_token = '{token}'"
                )
                user = cursor.fetchone()
                
                if user:
                    if datetime.now() < user['reset_token_expiry']:
                        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        cursor.execute(
                            f"UPDATE users SET password_hash = '{password_hash}', reset_token = NULL WHERE username = '{username}'"
                        )
                        conn.commit()
                        flash('Password reset successful! Please login.', 'success')
                        return redirect(url_for('login'))
                    else:
                        flash('Reset token expired', 'danger')
                else:
                    flash('Invalid reset token', 'danger')
                    
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('auth/reset_password.html')

@app.route('/logout')
def logout():
    """Logout user"""
    username = session.get('username', 'User')
    session.clear()
    
    # INSECURE: Open redirect via next parameter
    next_page = request.args.get('next', url_for('home'))
    flash(f'Goodbye {username}!', 'info')
    return redirect(next_page)

# ============================================================================
# PRODUCT CATALOG - SQL Injection, XSS, SSTI
# ============================================================================

@app.route('/products')
def products():
    """Product catalog with search - VULNERABLE to SQL Injection"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get search and filter parameters
    search = request.args.get('search', '')
    category_id = request.args.get('category', '')
    sort_by = request.args.get('sort', 'name')
    page = int(request.args.get('page', 1))
    per_page = Config.PRODUCTS_PER_PAGE
    offset = (page - 1) * per_page
    
    # Build query - INSECURE: SQL Injection in search and filters
    query = "SELECT * FROM products WHERE is_active = TRUE"
    
    if search:
        # INSECURE: Direct concatenation allows SQL injection
        query += f" AND (name LIKE '%{search}%' OR description LIKE '%{search}%')"
    
    if category_id:
        query += f" AND category_id = {category_id}"
    
    # INSECURE: SQL Injection in ORDER BY
    query += f" ORDER BY {sort_by} LIMIT {per_page} OFFSET {offset}"
    
    try:
        cursor.execute(query)
        products_list = cursor.fetchall()
    except psycopg2.Error as e:
        # Show SQL error
        flash(f'Search error: {str(e)}', 'danger')
        products_list = []
    
    # Get categories for filter
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    
    # Get total count for pagination
    count_query = "SELECT COUNT(*) as total FROM products WHERE is_active = TRUE"
    if search:
        count_query += f" AND (name LIKE '%{search}%' OR description LIKE '%{search}%')"
    if category_id:
        count_query += f" AND category_id = {category_id}"
    
    cursor.execute(count_query)
    total_products = cursor.fetchone()['total']
    total_pages = (total_products + per_page - 1) // per_page
    
    cursor.close()
    conn.close()
    
    return render_template('products/catalog.html', 
                         products=products_list, 
                         categories=categories,
                         current_page=page,
                         total_pages=total_pages,
                         search=search)

@app.route('/product/<product_id>')
def product_detail(product_id):
    """Product detail page - VULNERABLE to Blind SQL Injection"""
    conn = get_db()
    cursor = conn.cursor()
    
    # INSECURE: Blind SQL Injection - different responses based on query result
    query = f"SELECT * FROM products WHERE id = {product_id} AND is_active = TRUE"
    
    try:
        cursor.execute(query)
        product = cursor.fetchone()
        
        if not product:
            flash('Product not found', 'warning')
            return redirect(url_for('products'))
        
        # Get reviews for this product
        cursor.execute(f"SELECT r.*, u.username FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.product_id = {product_id} ORDER BY r.created_at DESC")
        reviews = cursor.fetchall()
        
        # Get category
        if product['category_id']:
            cursor.execute(f"SELECT * FROM categories WHERE id = {product['category_id']}")
            category = cursor.fetchone()
        else:
            category = None
        
        cursor.close()
        conn.close()
        
        return render_template('products/detail.html', product=product, reviews=reviews, category=category)
        
    except psycopg2.Error as e:
        # INSECURE: Error message reveals SQL injection
        cursor.close()
        conn.close()
        flash(f'Error loading product: {str(e)}', 'danger')
        return redirect(url_for('products'))

@app.route('/product/<product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    """Add product review - VULNERABLE to Stored XSS and Unrestricted File Upload"""
    rating = request.form.get('rating', 5)
    comment = request.form.get('comment', '')
    
    # VULNERABLE: Auto-linkify URLs without sanitization
    # This creates XSS when URLs contain: http://example.com/'onmouseover='alert()
    comment_with_links = auto_linkify(comment)
    
    conn = get_db()
    cursor = conn.cursor()
    
    file_path = None
    
    # INSECURE: Unrestricted file upload - accepts SVG, HTML, any file type!
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            # VULNERABLE: No file type validation
            # VULNERABLE: No file size validation
            # VULNERABLE: No malware scanning
            # Allows SVG with embedded JavaScript
            # Allows HTML files with XSS
            
            import os
            from werkzeug.utils import secure_filename
            
            # Even secure_filename won't help with malicious content inside files
            filename = secure_filename(file.filename)
            upload_folder = os.path.join('static', 'uploads', 'reviews')
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, f"{session['user_id']}_{int(time.time())}_{filename}")
            file.save(file_path)
            
            # Store relative path for web access
            file_path = '/' + file_path
    
    # INSECURE: Stored XSS - comment with auto-linkified URLs not sanitized
    # SQL Injection in comment field
    query = f"""
        INSERT INTO reviews (product_id, user_id, rating, comment, file_attachment) 
        VALUES ({product_id}, {session['user_id']}, {rating}, '{comment_with_links}', '{file_path}')
    """
    
    try:
        cursor.execute(query)
        conn.commit()
        flash('Review posted successfully!', 'success')
    except Exception as e:
        flash(f'Error posting review: {str(e)}', 'danger')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/check_stock')
def check_stock():
    """Check product stock - VULNERABLE to SSTI"""
    product_name = request.args.get('product_name', '')
    product = None
    rendered_name = None
    
    if product_name:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get product stock
        # INSECURE: SQL injection via string formatting
        cursor.execute(f"SELECT * FROM products WHERE name LIKE '%{product_name}%' LIMIT 1")
        product = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # INSECURE: Server-Side Template Injection
        # User input is rendered through render_template_string
        from flask import render_template_string
        try:
            rendered_name = render_template_string(product_name)
        except:
            rendered_name = product_name
    
    # Pass product data to template
    return render_template('products/check_stock.html', product=product, rendered_name=rendered_name)

# ============================================================================
# SHOPPING CART & CHECKOUT
# ============================================================================

@app.route('/cart')
@login_required
def view_cart():
    """View shopping cart"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, p.name, p.description, p.price, p.image_url, (c.quantity * p.price) as subtotal
        FROM cart_items c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (session['user_id'],))
    
    cart_items = cursor.fetchall()
    
    # Calculate total
    total = sum(item['subtotal'] for item in cart_items)
    
    cursor.close()
    conn.close()
    
    return render_template('cart/cart.html', cart_items=cart_items, total=total)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add item to cart"""
    quantity = int(request.form.get('quantity', 1))
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if item already in cart
        cursor.execute("""
            SELECT * FROM cart_items WHERE user_id = %s AND product_id = %s
        """, (session['user_id'], product_id))
        
        existing_item = cursor.fetchone()
        
        if existing_item:
            # Update quantity
            new_quantity = existing_item['quantity'] + quantity
            cursor.execute("""
                UPDATE cart_items SET quantity = %s WHERE user_id = %s AND product_id = %s
            """, (new_quantity, session['user_id'], product_id))
        else:
            # Insert new item
            cursor.execute("""
                INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)
            """, (session['user_id'], product_id, quantity))
        
        conn.commit()
        flash('Item added to cart!', 'success')
    except Exception as e:
        flash(f'Error adding to cart: {str(e)}', 'danger')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(request.referrer or url_for('products'))

@app.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    """Update cart quantities - VULNERABLE to negative quantity exploit"""
    cart_id = request.form.get('cart_id')
    quantity = int(request.form.get('quantity', 1))
    
    # INSECURE: No validation on quantity - can be negative!
    # This allows users to get "refunds" by setting negative quantities
    
    conn = get_db()
    cursor = conn.cursor()
    
    if quantity <= 0:
        cursor.execute("DELETE FROM cart_items WHERE id = %s AND user_id = %s", (cart_id, session['user_id']))
    else:
        cursor.execute("UPDATE cart_items SET quantity = %s WHERE id = %s AND user_id = %s", 
                      (quantity, cart_id, session['user_id']))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Cart updated', 'success')
    return redirect(url_for('view_cart'))

@app.route('/cart/remove/<int:cart_id>')
@login_required
def remove_from_cart(cart_id):
    """Remove item from cart"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM cart_items WHERE id = %s AND user_id = %s", (cart_id, session['user_id']))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    flash('Item removed from cart', 'info')
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout - VULNERABLE to Price Manipulation and CSRF"""
    if request.method == 'POST':
        # INSECURE: Total price comes from client (hidden form field)
        # User can manipulate this to pay any amount!
        total_amount = float(request.form.get('total_amount', 0))
        
        # INSECURE: No CSRF protection on checkout
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # Get cart items
            cursor.execute("""
                SELECT c.*, p.name, p.price
                FROM cart_items c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = %s
            """, (session['user_id'],))
            
            cart_items = cursor.fetchall()
            
            if not cart_items:
                flash('Your cart is empty', 'warning')
                return redirect(url_for('view_cart'))
            
            # Create order
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{int(time.time())}"
            
            cursor.execute("""
                INSERT INTO orders (user_id, order_number, total_amount, status)
                VALUES (%s, %s, %s, 'pending') RETURNING id
            """, (session['user_id'], order_number, total_amount))
            
            order_id = cursor.fetchone()['id']
            
            # Add order items
            for item in cart_items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, product_name, quantity, price, subtotal)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (order_id, item['product_id'], item['name'], item['quantity'], 
                      item['price'], item['quantity'] * item['price']))
            
            # Clear cart
            cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (session['user_id'],))
            
            conn.commit()
            
            flash(f'Order {order_number} placed successfully!', 'success')
            return redirect(url_for('order_confirmation', order_id=order_id))
            
        except Exception as e:
            flash(f'Checkout error: {str(e)}', 'danger')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    # GET request - show checkout form
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, p.name, p.price, p.image_url, (c.quantity * p.price) as subtotal
        FROM cart_items c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (session['user_id'],))
    
    cart_items = cursor.fetchall()
    total = sum(item['subtotal'] for item in cart_items)
    
    cursor.close()
    conn.close()
    
    return render_template('cart/checkout.html', cart_items=cart_items, total=total)

@app.route('/order/<int:order_id>/confirmation')
@login_required
def order_confirmation(order_id):
    """Order confirmation page"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT o.*, 
               (SELECT json_agg(row_to_json(oi.*)) FROM order_items oi WHERE oi.order_id = o.id) as order_items
        FROM orders o
        WHERE o.id = %s AND o.user_id = %s
    """, (order_id, session['user_id']))
    
    order = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('home'))
    
    return render_template('cart/confirmation.html', order=order)

@app.route('/apply_coupon', methods=['POST'])
@login_required
def apply_coupon():
    """Apply coupon code - VULNERABLE to Race Condition"""
    coupon_code = request.form.get('coupon_code', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM coupons 
            WHERE code = %s AND is_active = TRUE
            AND (expires_at IS NULL OR expires_at > NOW())
        """, (coupon_code,))
        
        coupon = cursor.fetchone()
        
        if coupon:
            # INSECURE: Race condition - can apply same coupon multiple times
            # No transaction locking, times_used not checked atomically
            if coupon['max_uses'] and coupon['times_used'] >= coupon['max_uses']:
                flash('Coupon usage limit reached', 'warning')
                return redirect(url_for('checkout'))
            
            # Increment usage count
            cursor.execute("UPDATE coupons SET times_used = times_used + 1 WHERE id = %s", (coupon['id'],))
            conn.commit()
            
            # Store in session
            session['coupon'] = {
                'code': coupon['code'],
                'type': coupon['discount_type'],
                'value': float(coupon['discount_value'])
            }
            
            flash(f'Coupon "{coupon_code}" applied!', 'success')
        else:
            flash('Invalid or expired coupon', 'danger')
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('checkout'))

# ============================================================================
# USER PROFILE & ORDERS - IDOR, CSTI, CSRF
# ============================================================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile - VULNERABLE to CSTI (Client-Side Template Injection)"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        display_name = request.form.get('display_name', '')
        email = request.form.get('email', '')
        
        # Update profile
        cursor.execute("""
            UPDATE users SET display_name = %s, email = %s WHERE id = %s
        """, (display_name, email, session['user_id']))
        
        conn.commit()
        flash('Profile updated!', 'success')
    
    # Get user data
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    # INSECURE: Display name will be rendered in AngularJS template (CSTI vulnerability)
    return render_template('user/profile.html', user=user)

@app.route('/profile/change_email', methods=['POST'])
@login_required
def change_email():
    """Change email - VULNERABLE to CSRF (No CSRF token)"""
    new_email = request.form.get('email', '')
    
    # INSECURE: No CSRF protection
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE users SET email = %s WHERE id = %s", (new_email, session['user_id']))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    flash('Email updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/orders')
@login_required
def order_history():
    """User order history"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC
    """, (session['user_id'],))
    
    orders = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('user/orders.html', orders=orders)

@app.route('/order/<int:order_id>')
@login_required
def view_order(order_id):
    """View order details - VULNERABLE to IDOR"""
    conn = get_db()
    cursor = conn.cursor()
    
    # INSECURE: Only checks if user is logged in, not if they own the order
    # Can view ANY order by changing the ID
    cursor.execute("""
        SELECT o.*, 
               u.username, u.email,
               (SELECT json_agg(row_to_json(oi.*)) FROM order_items oi WHERE oi.order_id = o.id) as order_items
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.id = %s
    """, (order_id,))
    
    order = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not order:
        flash('Order not found', 'warning')
        return redirect(url_for('order_history'))
    
    return render_template('user/order_detail.html', order=order)

@app.route('/invoice/<int:order_id>')
@login_required
def download_invoice(order_id):
    """Download invoice - VULNERABLE to IDOR"""
    # INSECURE: Can download any invoice by changing order_id
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    
    if not order:
        cursor.close()
        conn.close()
        flash('Invoice not found', 'danger')
        return redirect(url_for('order_history'))
    
    # Get order items
    cursor.execute("""
        SELECT * FROM order_items WHERE order_id = %s
    """, (order_id,))
    order_items = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Use template instead of raw HTML
    return render_template('invoice/invoice.html', order=order, order_items=order_items)

@app.route('/wishlist')
@login_required
def wishlist():
    """View wishlist"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT w.*, p.name, p.description, p.price, p.image_url
        FROM wishlist w
        JOIN products p ON w.product_id = p.id
        WHERE w.user_id = %s
    """, (session['user_id'],))
    
    wishlist_items = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('user/wishlist.html', wishlist=wishlist_items)

@app.route('/wishlist/add/<int:product_id>')
@login_required
def add_to_wishlist(product_id):
    """Add to wishlist"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO wishlist (user_id, product_id) VALUES (%s, %s)
            ON CONFLICT (user_id, product_id) DO NOTHING
        """, (session['user_id'], product_id))
        conn.commit()
        flash('Added to wishlist!', 'success')
    except:
        flash('Error adding to wishlist', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(request.referrer or url_for('products'))

# ============================================================================
# ADMIN PANEL - Multiple Vulnerabilities
# ============================================================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) as total FROM users")
    total_users = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM products")
    total_products = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM orders")
    total_orders = cursor.fetchone()['total']
    
    cursor.execute("SELECT SUM(total_amount) as revenue FROM orders WHERE status IN ('delivered', 'shipped')")
    total_revenue = cursor.fetchone()['revenue'] or 0
    
    # Recent orders
    cursor.execute("SELECT o.*, u.username FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC LIMIT 10")
    recent_orders = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders)

@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin user management"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    """Edit user - VULNERABLE to IDOR and Mass Assignment"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # INSECURE: Mass assignment - can modify any field including is_admin!
        username = request.form.get('username')
        email = request.form.get('email')
        display_name = request.form.get('display_name')
        is_admin = request.form.get('is_admin') == 'on'
        is_active = request.form.get('is_active') == 'on'
        balance = request.form.get('balance', 0)
        
        cursor.execute("""
            UPDATE users 
            SET username = %s, email = %s, display_name = %s, is_admin = %s, is_active = %s, balance = %s
            WHERE id = %s
        """, (username, email, display_name, is_admin, is_active, balance, user_id))
        
        conn.commit()
        flash('User updated!', 'success')
        return redirect(url_for('admin_users'))
    
    # INSECURE: Can edit ANY user, even other admins
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not user:
        flash('User not found', 'warning')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/products')
@admin_required
def admin_products():
    """Admin product management"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id ORDER BY p.created_at DESC")
    products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/products.html', products=products)

@app.route('/admin/health_check', methods=['GET', 'POST'])
@admin_required
def admin_health_check():
    """System health check - VULNERABLE to SSRF"""
    if request.method == 'POST':
        url = request.form.get('url', '')
        
        # INSECURE: Server-Side Request Forgery (SSRF)
        # No URL validation - can access internal services!
        try:
            response = urllib.request.urlopen(url, timeout=5)
            content = response.read().decode('utf-8')
            
            return render_template('admin/health_check.html', 
                                 result=content, 
                                 url=url,
                                 success=True)
        except Exception as e:
            return render_template('admin/health_check.html', 
                                 result=f"Error: {str(e)}", 
                                 url=url,
                                 success=False)
    
    return render_template('admin/health_check.html')

@app.route('/admin/backup', methods=['GET', 'POST'])
@admin_required
def admin_backup():
    """Database backup - VULNERABLE to Command Injection"""
    if request.method == 'POST':
        filename = request.form.get('filename', 'backup.sql')
        
        # INSECURE: Command Injection - filename passed directly to shell
        # Can execute arbitrary commands!
        backup_command = f"pg_dump {Config.DATABASE_NAME} > /tmp/{filename}"
        
        try:
            # EXTREMELY INSECURE: Direct execution of user input
            result = subprocess.run(backup_command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                flash(f'Backup created: /tmp/{filename}', 'success')
                return render_template('admin/backup.html', success=True, filename=filename, output=result.stdout)
            else:
                flash(f'Backup failed: {result.stderr}', 'danger')
                return render_template('admin/backup.html', success=False, error=result.stderr)
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return render_template('admin/backup.html', success=False, error=str(e))
    
    return render_template('admin/backup.html')

@app.route('/download')
def download_file():
    """
    Download files - VULNERABLE to Directory Traversal!
    Allows reading ANY file on the system via path traversal
    """
    filename = request.args.get('file', '')
    
    # INSECURE: No path validation or sanitization!
    # Allows directory traversal attacks like: ../../../etc/passwd
    # No restriction on file types or locations
    
    try:
        # CRITICAL VULNERABILITY: Direct file path construction
        # User can access ANY file on the system
        file_path = os.path.join('static/uploads', filename)
        
        # INSECURE: os.path.join doesn't prevent traversal with ../
        # Example exploits:
        # ?file=../../../etc/passwd
        # ?file=../../app.py
        # ?file=../../../root/.ssh/id_rsa
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            # Even the error message leaks information!
            flash(f'File not found: {file_path}', 'danger')
            return redirect(url_for('home'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('home'))

@app.route('/api/logs')
def view_logs():
    """
    View application logs - VULNERABLE to Arbitrary File Read!
    Allows reading ANY file on the system
    """
    log_file = request.args.get('file', 'app.log')
    
    # CRITICAL VULNERABILITY: Arbitrary File Read
    # No path validation or sanitization
    # User can read ANY file on the system
    
    try:
        # INSECURE: Direct file read without validation
        # Examples:
        # ?file=/etc/passwd
        # ?file=/app/config.py
        # ?file=/app/.env
        # ?file=/root/.ssh/id_rsa
        
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Return file content as plain text
        return Response(content, mimetype='text/plain')
    
    except FileNotFoundError:
        return Response(f"Log file not found: {log_file}", status=404, mimetype='text/plain')
    except PermissionError:
        return Response(f"Permission denied: {log_file}", status=403, mimetype='text/plain')
    except Exception as e:
        return Response(f"Error reading file: {str(e)}", status=500, mimetype='text/plain')

# Internal endpoint for SSRF target
@app.route('/admin/internal_secrets')
def internal_secrets():
    """Internal secrets endpoint - only accessible via SSRF"""
    # Check if request is from localhost
    # INSECURE: Can be bypassed via SSRF
    if request.remote_addr in ['127.0.0.1', 'localhost', '::1']:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM flags WHERE flag_name = 'flag_ssrf'")
        flag = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        secret_data = {
            'internal_api_key': Config.INTERNAL_API_KEY,
            'database_password': Config.DATABASE_PASSWORD,
            'flag': flag['flag_value'] if flag else 'FLAG{ss4f_1nt3rn4l_4cc3ss}',
            'admin_secret': 'ADMIN-SECRET-KEY-12345'
        }
        
        return jsonify(secret_data)
    else:
        return "Access Denied - Internal Use Only", 403

# ============================================================================
# API ENDPOINTS - Information Disclosure
# ============================================================================

@app.route('/api/products')
def api_products():
    """API endpoint for products - VULNERABLE to Information Disclosure"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products WHERE is_active = TRUE")
    products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # INSECURE: Leaks internal cost information
    # Converts to list of dicts for JSON serialization
    products_list = []
    for product in products:
        products_list.append(dict(product))
    
    return jsonify(products_list)

@app.route('/api/profile', methods=['GET', 'POST'])
@login_required
def api_profile():
    """API endpoint for profile - VULNERABLE to Mass Assignment"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # INSECURE: Mass assignment vulnerability
        # User can modify any field by sending JSON data
        data = request.get_json()
        
        # Build UPDATE query from all provided fields
        fields = []
        values = []
        for key, value in data.items():
            fields.append(f"{key} = %s")
            values.append(value)
        
        if fields:
            query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
            values.append(session['user_id'])
            
            try:
                cursor.execute(query, values)
                conn.commit()
                
                # Update session if is_admin was changed
                cursor.execute("SELECT is_admin FROM users WHERE id = %s", (session['user_id'],))
                user = cursor.fetchone()
                session['is_admin'] = user['is_admin']
                
                return jsonify({'success': True, 'message': 'Profile updated'})
            except Exception as e:
                conn.rollback()
                return jsonify({'success': False, 'error': str(e)}), 400
        
    # GET request
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return jsonify(dict(user))

# ============================================================================
# FILE UPLOAD - Unrestricted Upload
# ============================================================================

@app.route('/admin/upload', methods=['GET', 'POST'])
@admin_required
def file_upload():
    """File upload - VULNERABLE to Unrestricted File Upload"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'warning')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected', 'warning')
            return redirect(request.url)
        
        # INSECURE: No file type validation!
        # Can upload anything including executable files
        upload_folder = os.path.join(app.static_folder, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, file.filename)
        file.save(filepath)
        
        flash(f'File uploaded: {file.filename}', 'success')
        return redirect(url_for('file_upload'))
    
    return render_template('admin/upload.html')

# ============================================================================
# FAVORITES SYSTEM - IDOR Vulnerabilities
# ============================================================================

@app.route('/favorites')
@login_required
def view_favorites():
    """View user's favorite products"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT f.*, p.name, p.description, p.price, p.image_url
        FROM favorites f
        JOIN products p ON f.product_id = p.id
        WHERE f.user_id = %s
    """, (session['user_id'],))
    
    favorites = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('user/favorites.html', favorites=favorites)

@app.route('/favorites/add/<int:product_id>')
@login_required
def add_to_favorites(product_id):
    """Add product to favorites"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO favorites (user_id, product_id) VALUES (%s, %s)
            ON CONFLICT (user_id, product_id) DO NOTHING
        """, (session['user_id'], product_id))
        conn.commit()
        flash('Added to favorites!', 'success')
    except:
        flash('Error adding to favorites', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(request.referrer or url_for('products'))

@app.route('/favorites/share/<int:user_id>')
def share_favorites(user_id):
    """Share favorites list - VULNERABLE to IDOR"""
    # INSECURE: Can view anyone's favorites by changing user_id
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT f.*, p.name, p.description, p.price, p.image_url, u.username
        FROM favorites f
        JOIN products p ON f.product_id = p.id
        JOIN users u ON f.user_id = u.id
        WHERE f.user_id = %s
    """, (user_id,))
    
    favorites = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('user/shared_favorites.html', favorites=favorites, user_id=user_id)

# ============================================================================
# PRODUCT Q&A - Stored XSS
# ============================================================================

@app.route('/product/<int:product_id>/questions')
def product_questions(product_id):
    """View product Q&A"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    
    cursor.execute("""
        SELECT q.*, u.username as asker_username, u2.username as answerer_username
        FROM product_questions q
        JOIN users u ON q.user_id = u.id
        LEFT JOIN users u2 ON q.answered_by = u2.id
        WHERE q.product_id = %s
        ORDER BY q.created_at DESC
    """, (product_id,))
    
    questions = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('products/questions.html', product=product, questions=questions)

@app.route('/product/<int:product_id>/ask', methods=['POST'])
@login_required
def ask_question(product_id):
    """Ask a question about product - VULNERABLE to Stored XSS"""
    question_text = request.form.get('question', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # INSECURE: Stored XSS - question not sanitized
    cursor.execute("""
        INSERT INTO product_questions (product_id, user_id, question)
        VALUES (%s, %s, %s)
    """, (product_id, session['user_id'], question_text))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Question posted!', 'success')
    return redirect(url_for('product_questions', product_id=product_id))

@app.route('/question/<int:question_id>/answer', methods=['POST'])
@login_required
def answer_question(question_id):
    """Answer a product question - VULNERABLE to Stored XSS"""
    answer_text = request.form.get('answer', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # INSECURE: Stored XSS - answer not sanitized
    cursor.execute("""
        UPDATE product_questions 
        SET answer = %s, answered_by = %s, answered_at = NOW()
        WHERE id = %s
    """, (answer_text, session['user_id'], question_id))
    
    conn.commit()
    
    cursor.execute("SELECT product_id FROM product_questions WHERE id = %s", (question_id,))
    product_id = cursor.fetchone()['product_id']
    
    cursor.close()
    conn.close()
    
    flash('Answer posted!', 'success')
    return redirect(url_for('product_questions', product_id=product_id))

# ============================================================================
# USER MESSAGING - IDOR, Stored XSS
# ============================================================================

@app.route('/messages')
@login_required
def view_messages():
    """View user messages"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.*, 
               u1.username as sender_username,
               u2.username as recipient_username
        FROM messages m
        JOIN users u1 ON m.sender_id = u1.id
        JOIN users u2 ON m.recipient_id = u2.id
        WHERE m.recipient_id = %s OR m.sender_id = %s
        ORDER BY m.created_at DESC
    """, (session['user_id'], session['user_id']))
    
    messages = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('user/messages.html', messages=messages)

@app.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    """Send message - VULNERABLE to Stored XSS"""
    recipient_username = request.form.get('recipient', '')
    subject = request.form.get('subject', '')
    message_text = request.form.get('message', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get recipient ID
    cursor.execute("SELECT id FROM users WHERE username = %s", (recipient_username,))
    recipient = cursor.fetchone()
    
    if not recipient:
        flash('User not found', 'danger')
        return redirect(url_for('view_messages'))
    
    # INSECURE: Stored XSS - message not sanitized
    cursor.execute("""
        INSERT INTO messages (sender_id, recipient_id, subject, message)
        VALUES (%s, %s, %s, %s)
    """, (session['user_id'], recipient['id'], subject, message_text))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Message sent!', 'success')
    return redirect(url_for('view_messages'))

@app.route('/message/<int:message_id>')
@login_required
def view_message(message_id):
    """View message - VULNERABLE to IDOR"""
    conn = get_db()
    cursor = conn.cursor()
    
    # INSECURE: Can read anyone's messages by changing ID
    cursor.execute("""
        SELECT m.*, 
               u1.username as sender_username,
               u2.username as recipient_username
        FROM messages m
        JOIN users u1 ON m.sender_id = u1.id
        JOIN users u2 ON m.recipient_id = u2.id
        WHERE m.id = %s
    """, (message_id,))
    
    message = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not message:
        flash('Message not found', 'danger')
        return redirect(url_for('view_messages'))
    
    return render_template('user/message_detail.html', message=message)

# ============================================================================
# XXE (XML External Entity) INJECTION
# ============================================================================

@app.route('/admin/import_xml', methods=['GET', 'POST'])
@admin_required
def import_xml():
    """Import products from XML - VULNERABLE to XXE"""
    if request.method == 'POST':
        xml_data = request.form.get('xml_data', '')
        
        try:
            import lxml.etree as ET
            
            # INSECURE: XXE vulnerability - allows external entities
            parser = ET.XMLParser(no_network=False, resolve_entities=True, load_dtd=True)
            root = ET.fromstring(xml_data.encode(), parser)
            
            # Process XML
            products_imported = 0
            for product in root.findall('.//product'):
                name = product.find('name').text if product.find('name') is not None else 'Unknown'
                price = product.find('price').text if product.find('price') is not None else '0'
                products_imported += 1
            
            flash(f'Imported {products_imported} products', 'success')
            
            # Also return parsed XML for display
            return render_template('admin/import_xml.html', 
                                 result=ET.tostring(root, pretty_print=True).decode(),
                                 success=True)
            
        except Exception as e:
            flash(f'XML parsing error: {str(e)}', 'danger')
            return render_template('admin/import_xml.html', error=str(e))
    
    return render_template('admin/import_xml.html')

# ============================================================================
# GRAPHQL ENDPOINT - Injection Vulnerabilities
# ============================================================================

@app.route('/graphql', methods=['GET', 'POST'])
def graphql_endpoint():
    """GraphQL endpoint - VULNERABLE to injection"""
    if request.method == 'POST':
        query = request.get_json().get('query', '') if request.is_json else request.form.get('query', '')
        
        # INSECURE: Direct string interpolation in GraphQL query
        # Vulnerable to injection attacks
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # Parse simple GraphQL-like queries
            if 'user(' in query:
                # Extract user ID from query - VULNERABLE
                import re
                match = re.search(r'user\(id:\s*(\d+)\)', query)
                if match:
                    user_id = match.group(1)
                    # INSECURE: SQL Injection via GraphQL
                    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
                    user = cursor.fetchone()
                    
                    cursor.close()
                    conn.close()
                    
                    return jsonify({
                        'data': {
                            'user': dict(user) if user else None
                        }
                    })
            
            elif 'products' in query:
                cursor.execute("SELECT * FROM products LIMIT 10")
                products = cursor.fetchall()
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'data': {
                        'products': [dict(p) for p in products]
                    }
                })
            
            return jsonify({'error': 'Invalid query'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    return render_template('api/graphql.html')

# ============================================================================
# REDOS (Regular Expression Denial of Service)
# ============================================================================

@app.route('/search_advanced', methods=['GET', 'POST'])
def search_advanced():
    """Advanced search - VULNERABLE to ReDoS"""
    if request.method == 'POST':
        search_pattern = request.form.get('pattern', '')
        
        import re
        import time
        
        start_time = time.time()
        
        try:
            # INSECURE: ReDoS vulnerability - catastrophic backtracking
            # Pattern like (a+)+ causes exponential time complexity
            regex = re.compile(search_pattern)
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT name, description FROM products LIMIT 100")
            products = cursor.fetchall()
            cursor.close()
            conn.close()
            
            matches = []
            for product in products:
                if regex.search(product['name']) or regex.search(product['description'] or ''):
                    matches.append(product)
            
            elapsed = time.time() - start_time
            
            return render_template('search_advanced.html', 
                                 matches=matches, 
                                 elapsed=elapsed,
                                 pattern=search_pattern)
            
        except Exception as e:
            return render_template('search_advanced.html', error=str(e))
    
    return render_template('search_advanced.html')

# ============================================================================
# HTTP HEADER INJECTION
# ============================================================================

@app.route('/api/export')
@login_required
def export_data():
    """Export user data - VULNERABLE to HTTP Header Injection"""
    filename = request.args.get('filename', 'export.csv')
    
    # INSECURE: HTTP Header Injection via filename
    # Attacker can inject headers by including newlines in filename
    
    response = make_response('user_id,username,email\n1,admin,admin@local')
    
    # VULNERABLE: Unsanitized filename in header
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'text/csv'
    
    return response

# ============================================================================
# SESSION FIXATION & INSECURE DESERIALIZATION
# ============================================================================

@app.route('/debug/session')
def debug_session():
    """Debug session - Exposes session data"""
    # INSECURE: Session information disclosure
    return jsonify({
        'session_data': dict(session),
        'session_id': request.cookies.get('session'),
        'warning': 'This endpoint leaks session information!'
    })

# ============================================================================
# DIRECTORY LISTING (Exposed via static files)
# ============================================================================

# Note: Flask's static file serving already allows directory listing
# if index.html doesn't exist. We ensure /static/uploads/ is browsable

# ============================================================================
# LDAP INJECTION (if LDAP is enabled)
# ============================================================================

@app.route('/admin/ldap_search', methods=['GET', 'POST'])
@admin_required
def ldap_search():
    """LDAP user search - VULNERABLE to LDAP Injection"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        
        # INSECURE: LDAP Injection
        # In a real scenario, this would connect to LDAP
        # Here we simulate the vulnerability
        
        ldap_filter = f"(uid={username})"
        
        # Attacker can inject: *)(uid=*
        # Resulting in: (uid=*)(uid=*)
        
        results = {
            'filter': ldap_filter,
            'warning': 'LDAP Injection possible!',
            'example_injection': '*)(uid=*',
            'simulated_results': [
                {'uid': 'admin', 'cn': 'Administrator'},
                {'uid': 'user1', 'cn': 'User One'}
            ]
        }
        
        return render_template('admin/ldap_search.html', results=results)
    
    return render_template('admin/ldap_search.html')

# ============================================================================
# HOST HEADER INJECTION / PASSWORD RESET POISONING
# ============================================================================

# Already vulnerable in /reset_password route via Host header manipulation

# ============================================================================
# CORS MISCONFIGURATION
# ============================================================================

@app.route('/api/sensitive_data')
@login_required
def api_sensitive_data():
    """API endpoint - VULNERABLE to CORS misconfiguration"""
    response = jsonify({
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'is_admin': session.get('is_admin'),
        'session_token': request.cookies.get('session')
    })
    
    # INSECURE: Overly permissive CORS
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    return response

# ============================================================================
# HTML INJECTION (in profile bio)
# ============================================================================

@app.route('/profile/bio', methods=['POST'])
@login_required
def update_bio():
    """Update profile bio - VULNERABLE to HTML Injection"""
    bio = request.form.get('bio', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # INSECURE: HTML Injection - bio rendered as raw HTML
    cursor.execute("UPDATE users SET bio = %s WHERE id = %s", (bio, session['user_id']))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    flash('Bio updated!', 'success')
    return redirect(url_for('profile'))

# ============================================================================
# PRICE = 0 ORDER VULNERABILITY
# ============================================================================

@app.route('/checkout/free', methods=['POST'])
@login_required
def checkout_free():
    """Checkout with $0 - VULNERABLE: allows free orders"""
    # INSECURE: Allows orders with total = $0.00
    # No validation that total must be > 0
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT c.*, p.name, p.price
            FROM cart_items c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = %s
        """, (session['user_id'],))
        
        cart_items = cursor.fetchall()
        
        if not cart_items:
            flash('Cart is empty', 'warning')
            return redirect(url_for('view_cart'))
        
        # Create order with $0.00 total
        order_number = f"ORD-FREE-{datetime.now().strftime('%Y%m%d')}-{int(time.time())}"
        
        cursor.execute("""
            INSERT INTO orders (user_id, order_number, total_amount, status)
            VALUES (%s, %s, %s, 'completed') RETURNING id
        """, (session['user_id'], order_number, 0.00))
        
        order_id = cursor.fetchone()['id']
        
        # Add order items
        for item in cart_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, quantity, price, subtotal)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (order_id, item['product_id'], item['name'], item['quantity'], 0.00, 0.00))
        
        # Clear cart
        cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (session['user_id'],))
        
        conn.commit()
        
        flash(f'🎉 Free order {order_number} completed! FLAG{{fr33_pr0duct5_vuln}}', 'success')
        return redirect(url_for('order_confirmation', order_id=order_id))
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('view_cart'))

# ============================================================================
# PRODUCT COMPARISON - XSS
# ============================================================================

@app.route('/compare')
def compare_products():
    """Compare products - VULNERABLE to XSS in notes"""
    product_ids = request.args.getlist('products')
    notes = request.args.get('notes', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    products = []
    for pid in product_ids[:4]:  # Max 4 products
        cursor.execute("SELECT * FROM products WHERE id = %s", (pid,))
        product = cursor.fetchone()
        if product:
            products.append(product)
    
    cursor.close()
    conn.close()
    
    # INSECURE: XSS in comparison notes
    return render_template('products/compare.html', products=products, notes=notes)

# ============================================================================
# RATE LIMIT BYPASS via X-Forwarded-For
# ============================================================================

# Note: Already vulnerable - no rate limiting implemented
# Attackers can rotate X-Forwarded-For header to bypass IP-based limits

# ============================================================================
# CLICKJACKING (No X-Frame-Options)
# ============================================================================

# Note: Already vulnerable - no X-Frame-Options header set globally

# ============================================================================
# BACKUP FILE EXPOSURE
# ============================================================================

@app.route('/.git/config')
def git_config():
    """Exposed .git/config - shows sensitive data"""
    try:
        with open('.git/config', 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/plain'}
    except:
        return "Not found", 404

@app.route('/.env')
def dotenv_file():
    """Exposed .env file"""
    try:
        with open('.env', 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/plain'}
    except:
        return "Not found", 404

@app.route('/backups/<path:filename>')
def backup_files(filename):
    """Exposed backup files"""
    try:
        with open(f'backups/{filename}', 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/plain'}
    except:
        return "Not found", 404

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    # INSECURE: Verbose error page in production
    return render_template('errors/500.html', error=str(error)), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("VulnerableShop - Deliberately Vulnerable E-commerce Application")
    print("=" * 70)
    print()
    print("⚠️  WARNING: This application is INTENTIONALLY INSECURE")
    print("    It contains multiple security vulnerabilities for educational purposes.")
    print("    DO NOT deploy to production or expose to the internet!")
    print()
    print("Starting server on http://localhost:5555")
    print()
    print("Default Credentials:")
    print("  Admin: admin / admin")
    print("  User:  alice / password")
    print()
    print("=" * 70)
    
    # Run in debug mode (insecure!)
    app.run(host='0.0.0.0', port=5555, debug=False)
