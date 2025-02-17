import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import sqlite3
import os
from PIL import Image
import io
import base64
import json

# Page config and custom CSS
st.set_page_config(page_title="Luxury Car Rentals", layout="wide")

# Custom CSS
st.markdown("""
    <style>
        .stButton>button {
            width: 100%;
            border-radius: 20px;
            height: 3em;
            background-color: #4B0082;
            color: white;
            border: none;
            margin: 5px 0;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background-color: #6A0DAD;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .css-1d391kg {
            padding: 2rem 1rem;
        }
        
        input[type="text"], input[type="password"] {
            border-radius: 20px;
            padding: 10px 15px;
            border: 2px solid #4B0082;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: #6A0DAD;
            box-shadow: 0 0 5px rgba(106,13,173,0.5);
        }
        
        h1 {
            color: #4B0082;
            text-align: center;
            padding: 1rem 0;
        }
        
        .car-card {
            background-color: white;
            border-radius: 15px;
            padding: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        
        .car-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        }
        
        .success-message {
            background-color: #E8F5E9;
            color: #2E7D32;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        
        .error-message {
            background-color: #FFEBEE;
            color: #C62828;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        
        .status-badge {
            padding: 0.25rem 0.5rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .status-badge.pending {
            background-color: #FFF3CD;
            color: #856404;
        }
        
        .status-badge.approved {
            background-color: #D4EDDA;
            color: #155724;
        }
        
        .status-badge.rejected {
            background-color: #F8D7DA;
            color: #721C24;
        }
        
        .admin-review-card {
            background-color: white;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 1.5rem 0;
        }
        
        .image-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .image-gallery img {
            width: 100%;
            border-radius: 10px;
            transition: transform 0.3s ease;
        }
        
        .image-gallery img:hover {
            transform: scale(1.05);
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'welcome'
if 'selected_car' not in st.session_state:
    st.session_state.selected_car = None

# Database setup

def init_db():
    """Initialize database and create tables"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()

        # Create Bookings Table (if not exists)
        c.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY,
                user_email TEXT NOT NULL,
                car_id INTEGER NOT NULL,
                pickup_date TEXT NOT NULL,
                return_date TEXT NOT NULL,
                location TEXT NOT NULL,
                total_price REAL NOT NULL,
                insurance BOOLEAN,
                driver BOOLEAN,
                delivery BOOLEAN,
                vip_service BOOLEAN,
                booking_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users (email)
            )
        ''')

        # Ensure Column Exists Before Indexing
        c.execute("PRAGMA table_info(bookings)")
        columns = [row[1] for row in c.fetchall()]
        if 'booking_status' in columns:
            c.execute('CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(booking_status)')

        conn.commit()
        print("Database initialized successfully")

    except sqlite3.Error as e:
        print(f"Database Error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def setup_database():
    """Initialize all database tables and admin user"""
    try:
        # First drop the existing database file to start fresh
        if os.path.exists('car_rental.db'):
            os.remove('car_rental.db')
            
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()

        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create car_listings table
        c.execute('''
            CREATE TABLE IF NOT EXISTS car_listings (
                id INTEGER PRIMARY KEY,
                owner_email TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                price REAL NOT NULL,
                location TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                specs TEXT NOT NULL,
                listing_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_email) REFERENCES users (email)
            )
        ''')

        # Create listing_images table
        c.execute('''
            CREATE TABLE IF NOT EXISTS listing_images (
                id INTEGER PRIMARY KEY,
                listing_id INTEGER NOT NULL,
                image_data TEXT NOT NULL,
                is_primary BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES car_listings (id)
            )
        ''')

        # Create bookings table
        c.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY,
                user_email TEXT NOT NULL,
                car_id INTEGER NOT NULL,
                pickup_date TEXT NOT NULL,
                return_date TEXT NOT NULL,
                location TEXT NOT NULL,
                total_price REAL NOT NULL,
                insurance BOOLEAN,
                driver BOOLEAN,
                delivery BOOLEAN,
                vip_service BOOLEAN,
                booking_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users (email)
            )
        ''')

        # Create notifications table
        c.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY,
                user_email TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT NOT NULL,
                read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users (email)
            )
        ''')

        # Create admin_reviews table
        c.execute('''
            CREATE TABLE IF NOT EXISTS admin_reviews (
                id INTEGER PRIMARY KEY,
                listing_id INTEGER NOT NULL,
                admin_email TEXT NOT NULL,
                comment TEXT,
                review_status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES car_listings (id),
                FOREIGN KEY (admin_email) REFERENCES users (email)
            )
        ''')

        # Create indexes with consistent column names
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_listings_status ON car_listings(listing_status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_listings_category ON car_listings(category)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(booking_status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_email, read)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_reviews_status ON admin_reviews(review_status)')

        # Create admin user
        c.execute('SELECT * FROM users WHERE email = ?', ('admin@luxuryrentals.com',))
        admin_exists = c.fetchone()
        
        if not admin_exists:
            c.execute('''
                INSERT INTO users (full_name, email, phone, password, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                'Admin User',
                'admin@luxuryrentals.com',
                '+971500000000',
                hash_password('admin123'),
                'admin'
            ))

        conn.commit()
        print("Database initialized successfully")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        st.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()
def hash_password(password):
    """Consistent password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()
    
def create_user(full_name, email, phone, password, role='user'):
    """Create a new user with proper password hashing"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Hash password consistently
        hashed_password = hash_password(password)
        
        # Print for debugging (remove in production)
        print(f"Creating user: {email}")
        
        c.execute(
            'INSERT INTO users (full_name, email, phone, password, role) VALUES (?, ?, ?, ?, ?)',
            (full_name, email, phone, hashed_password, role)
        )
        conn.commit()
        
        # Verify the user was created
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        print(f"User created: {user is not None}")
        
        return True
    except sqlite3.IntegrityError as e:
        print(f"Error creating user: {e}")
        return False
    finally:
        conn.close()

# Create admin user if not exists
def create_admin():
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()

    admin_email = "admin@luxuryrentals.com"
    admin_password = "admin123"  # Change in production
    hashed_password = hash_password(admin_password)

    try:
        c.execute('''
            INSERT INTO users (full_name, email, phone, password, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Admin User', admin_email, '+971500000000', hashed_password, 'admin'))

        conn.commit()
        st.success("✅ Admin user created successfully!")
    except sqlite3.IntegrityError:
        st.warning("⚠️ Admin user already exists.")
    
    conn.close()

def verify_user(email, password):
    """Verify user credentials with better error handling"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Print for debugging (remove in production)
        print(f"Verifying user: {email}")
        
        c.execute('SELECT password FROM users WHERE email = ?', (email,))
        result = c.fetchone()
        
        if result:
            stored_password = result[0]
            hashed_input = hash_password(password)
            
            # Print for debugging (remove in production)
            print(f"Password match: {stored_password == hashed_input}")
            
            return stored_password == hashed_input
        return False
        
    except sqlite3.Error as e:
        print(f"Database error during verification: {e}")
        return False
    finally:
        conn.close()


# Notification functions
def create_notification(user_email, message, type):
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    try:
        c.execute(
            'INSERT INTO notifications (user_email, message, type) VALUES (?, ?, ?)',
            (user_email, message, type)
        )
        conn.commit()
    finally:
        conn.close()

def get_unread_notifications_count(user_email):
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    c.execute(
        'SELECT COUNT(*) FROM notifications WHERE user_email = ? AND read = FALSE',
        (user_email,)
    )
    count = c.fetchone()[0]
    conn.close()
    return count

# Page components
def welcome_page():
    st.markdown("<h1>🚗 Luxury Car Rentals</h1>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h2 style='color: #4B0082;'>Experience Luxury on Wheels</h2>
            <p style='font-size: 1.2rem; color: #666;'>Discover our exclusive collection of premium vehicles</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button('Login', key='welcome_login'):
            st.session_state.current_page = 'login'
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        if st.button('Create Account', key='welcome_signup'):
            st.session_state.current_page = 'signup'
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        if st.button('Browse Cars', key='welcome_browse'):
            st.session_state.current_page = 'browse_cars'

def login_page():
    if st.button('← Back to Welcome', key='login_back'):
        st.session_state.current_page = 'welcome'
    
    st.markdown("<h1>Welcome Back</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email = st.text_input('Email/Phone')
        password = st.text_input('Password', type='password')
        
        if st.button('Login', key='login_submit'):
            # Add debug information
            st.info(f"Attempting login for: {email}")
            
            if verify_user(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.success('Login successful!')
                
                # Get user role
                conn = sqlite3.connect('car_rental.db')
                c = conn.cursor()
                c.execute('SELECT role FROM users WHERE email = ?', (email,))
                role = c.fetchone()[0] if c.fetchone() else 'user'
                conn.close()
                
                if role == 'admin':
                    st.session_state.current_page = 'admin_panel'
                else:
                    st.session_state.current_page = 'browse_cars'
            else:
                st.error('Invalid credentials. Please check your email and password.')
                # Add debug information
                conn = sqlite3.connect('car_rental.db')
                c = conn.cursor()
                c.execute('SELECT COUNT(*) FROM users WHERE email = ?', (email,))
                user_exists = c.fetchone()[0] > 0
                conn.close()
                if user_exists:
                    st.error("User exists but password doesn't match")
                else:
                    st.error("User not found in database")
                    
def signup_page():
    if st.button('← Back to Welcome', key='signup_back'):
        st.session_state.current_page = 'welcome'
    
    st.markdown("<h1>Create Account</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        full_name = st.text_input('Full Name')
        email = st.text_input('Email')
        phone = st.text_input('Phone Number')
        password = st.text_input('Password', type='password')
        confirm_password = st.text_input('Confirm Password', type='password')
        
        if st.button('Create Account', key='signup_submit'):
            if password != confirm_password:
                st.error('Passwords do not match')
            elif not all([full_name, email, phone, password]):
                st.error('Please fill in all fields')
            else:
                if create_user(full_name, email, phone, password):
                    st.success('Account created successfully!')
                    create_notification(email, "Welcome to Luxury Car Rentals!", "welcome")
                    st.session_state.current_page = 'login'
                else:
                    st.error('Email already exists')

def admin_panel():
    st.markdown("<h1>Admin Panel</h1>", unsafe_allow_html=True)
    
    # Back button
    if st.button('← Back to Browse', key='admin_back'):
        st.session_state.current_page = 'browse_cars'
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["Pending Listings", "Approved Listings", "Rejected Listings"])
    
    with tab1:
        show_pending_listings()
    
    with tab2:
        show_approved_listings()
    
    with tab3:
        show_rejected_listings()

def show_pending_listings():
    st.subheader("Pending Listings")
    
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Updated query to use listing_status
    c.execute('''
        SELECT cl.*, u.full_name, u.email, u.phone
        FROM car_listings cl
        JOIN users u ON cl.owner_email = u.email
        WHERE cl.listing_status = 'pending'
        ORDER BY cl.created_at DESC
    ''')
    
    pending_listings = c.fetchall()
    
    if not pending_listings:
        st.info("No pending listings to review")
    else:
        for listing in pending_listings:
            with st.container():
                # Get images for this listing
                c.execute('SELECT * FROM listing_images WHERE listing_id = ?', (listing[0],))
                images = c.fetchall()
                
                st.markdown(f"""
                    <div class='admin-review-card'>
                        <h3>{listing[2]} ({listing[3]})</h3>
                        <p><strong>Owner:</strong> {listing[11]} ({listing[12]})</p>
                        <p><strong>Phone:</strong> {listing[13]}</p>
                        <p><strong>Price:</strong> AED {listing[4]}/day</p>
                        <p><strong>Location:</strong> {listing[5]}</p>
                        <p><strong>Description:</strong> {listing[6]}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Display images
                if images:
                    st.markdown("<div class='image-gallery'>", unsafe_allow_html=True)
                    cols = st.columns(len(images))
                    for idx, img in enumerate(images):
                        with cols[idx]:
                            st.image(
                                f"data:image/jpeg;base64,{img[2]}", 
                                caption=f"Image {idx+1}",
                                use_column_width=True
                            )
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Review form
                with st.form(key=f"review_form_{listing[0]}"):
                    comment = st.text_area("Review Comment")
                    col1, col2 = st.columns(2)
                    with col1:
                        approve = st.form_submit_button("Approve")
                    with col2:
                        reject = st.form_submit_button("Reject")
                    
                    if approve or reject:
                        status = 'approved' if approve else 'rejected'
                        
                        # Update listing status - using listing_status
                        c.execute('''
                            UPDATE car_listings 
                            SET listing_status = ? 
                            WHERE id = ?
                        ''', (status, listing[0]))
                        
                        # Add admin review
                        c.execute('''
                            INSERT INTO admin_reviews 
                            (listing_id, admin_email, comment, review_status)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            listing[0],
                            st.session_state.user_email,
                            comment,
                            status
                        ))
                        
                        # Create notification for owner
                        create_notification(
                            listing[12],
                            f"Your listing for {listing[2]} has been {status}. {comment if comment else ''}",
                            f'listing_{status}'
                        )
                        
                        conn.commit()
                        st.success(f"Listing has been {status}")
                        st.rerun()
    
    conn.close()
def show_approved_listings():
    st.subheader("Approved Listings")
    show_listings_by_status('approved')

def show_rejected_listings():
    st.subheader("Rejected Listings")
    show_listings_by_status('rejected')

def show_listings_by_status(status):
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Updated query to use listing_status
    c.execute('''
        SELECT cl.*, u.full_name, ar.comment, ar.created_at
        FROM car_listings cl
        JOIN users u ON cl.owner_email = u.email
        LEFT JOIN admin_reviews ar ON cl.id = ar.listing_id
        WHERE cl.listing_status = ?
        ORDER BY cl.created_at DESC
    ''', (status,))
    
    listings = c.fetchall()
    
    if not listings:
        st.info(f"No {status} listings")
    else:
        for listing in listings:
            with st.container():
                # Get images
                c.execute('SELECT * FROM listing_images WHERE listing_id = ?', (listing[0],))
                images = c.fetchall()
                
                st.markdown(f"""
                    <div class='admin-review-card'>
                        <h3>{listing[2]} ({listing[3]})</h3>
                        <p><strong>Owner:</strong> {listing[11]}</p>
                        <p><strong>Review Comment:</strong> {listing[12] or 'No comment'}</p>
                        <p><strong>Review Date:</strong> {listing[13]}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Display images
                if images:
                    st.markdown("<div class='image-gallery'>", unsafe_allow_html=True)
                    cols = st.columns(len(images))
                    for idx, img in enumerate(images):
                        with cols[idx]:
                            st.image(
                                f"data:image/jpeg;base64,{img[2]}", 
                                caption=f"Image {idx+1}",
                                use_column_width=True
                            )
                    st.markdown("</div>", unsafe_allow_html=True)
    
    conn.close()

def browse_cars_page():
    col1, col2, col3 = st.columns([1,8,1])
    with col1:
        if st.button('← Back', key='browse_back'):
            st.session_state.current_page = 'welcome'
    with col3:
        if st.session_state.logged_in:
            unread_count = get_unread_notifications_count(st.session_state.user_email)
            if unread_count > 0:
                if st.button(f'🔔 ({unread_count})', key='notifications'):
                    st.session_state.current_page = 'notifications'
            if st.button('Logout', key='logout'):
                st.session_state.logged_in = False
                st.session_state.current_page = 'welcome'
    
    st.markdown("<h1>Explore Our Fleet</h1>", unsafe_allow_html=True)
    
    # Search and filters
    search = st.text_input('Search for your dream car', placeholder='e.g., "Lamborghini"')
    
    # Display cars
    display_cars(search)

def display_cars(search=""):
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    c.execute('''
        SELECT cl.*, li.image_data
        FROM car_listings cl
        LEFT JOIN listing_images li ON cl.id = li.listing_id AND li.is_primary = TRUE
        WHERE cl.listing_status = 'approved'
        ORDER BY cl.created_at DESC
    ''')
    
    listings = c.fetchall()
    
    # Group listings by category
    categorized_listings = {}
    for listing in listings:
        if search.lower() in listing[2].lower():  # Check if search matches model name
            category = listing[7]  # Category field
            if category not in categorized_listings:
                categorized_listings[category] = []
            categorized_listings[category].append(listing)
    
    # Display listings by category
    for category, cars in categorized_listings.items():
        st.markdown(f"<h2 style='color: #4B0082; margin-top: 2rem;'>{category}</h2>", unsafe_allow_html=True)
        
        cols = st.columns(3)
        for idx, car in enumerate(cars):
            with cols[idx % 3]:
                specs = json.loads(car[8])  # Parse specs JSON
                st.markdown(f"""
                    <div class='car-card'>
                        <img src='data:image/jpeg;base64,{car[11]}' style='width: 100%; border-radius: 10px;'>
                        <h3 style='color: #4B0082; margin: 1rem 0;'>{car[2]} ({car[3]})</h3>
                        <p style='color: #666;'>AED {car[4]}/day</p>
                        <p style='color: #666;'>{car[5]}</p>
                        <div style='color: #666; font-size: 0.9rem;'>
                            <p>🏎 {specs['engine']}</p>
                            <p>📊 {specs['mileage']}km</p>
                            <p>⚙️ {specs['transmission']}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button('Book Now', key=f"book_{car[0]}"):
                    st.session_state.selected_car = {
                        'id': car[0],
                        'model': car[2],
                        'year': car[3],
                        'price': car[4],
                        'location': car[5],
                        'specs': specs,
                        'image': car[11],
                        'owner_email': car[1]
                    }
                    st.session_state.current_page = 'book_car'
                    st.rerun()
    
    conn.close()

def main():
        
    # Sidebar navigation for logged-in users
    if st.session_state.logged_in:
        with st.sidebar:
            st.markdown("### My Account")
            st.write(f"Welcome, {st.session_state.user_email}")
            
            # Get user role
            conn = sqlite3.connect('car_rental.db')
            c = conn.cursor()
            c.execute('SELECT role FROM users WHERE email = ?', (st.session_state.user_email,))
            role = c.fetchone()[0]
            conn.close()
            
            # Show admin panel button for admin users
            if role == 'admin':
                st.markdown("### Admin Functions")
                if st.button("🔧 Admin Panel"):
                    st.session_state.current_page = 'admin_panel'
                st.markdown("---")
            
            # Regular navigation
            if st.button("🚗 Browse Cars"):
                st.session_state.current_page = 'browse_cars'
            
            if st.button("📝 My Listings"):
                st.session_state.current_page = 'my_listings'
            
            if st.button("➕ List Your Car"):
                st.session_state.current_page = 'list_your_car'
            
            # Show notifications with count
            unread_count = get_unread_notifications_count(st.session_state.user_email)
            if unread_count > 0:
                if st.button(f"🔔 Notifications ({unread_count})"):
                    st.session_state.current_page = 'notifications'
            else:
                if st.button("🔔 Notifications"):
                    st.session_state.current_page = 'notifications'
            
            st.markdown("---")
            if st.button("👋 Logout"):
                st.session_state.logged_in = False
                st.session_state.user_email = None
                st.session_state.current_page = 'welcome'
                st.rerun()
    
    # Main content based on current page
    if st.session_state.current_page == 'welcome':
        welcome_page()
    
    elif st.session_state.current_page == 'login':
        login_page()
    
    elif st.session_state.current_page == 'signup':
        signup_page()
    
    elif st.session_state.current_page == 'admin_panel':
        if st.session_state.logged_in:
            # Verify admin role
            conn = sqlite3.connect('car_rental.db')
            c = conn.cursor()
            c.execute('SELECT role FROM users WHERE email = ?', (st.session_state.user_email,))
            role = c.fetchone()[0]
            conn.close()
            
            if role == 'admin':
                admin_panel()
            else:
                st.error("Access denied. Admin privileges required.")
                st.session_state.current_page = 'browse_cars'
        else:
            st.warning("Please log in first")
            st.session_state.current_page = 'login'
    
    elif st.session_state.current_page == 'browse_cars':
        browse_cars_page()
    
    elif st.session_state.current_page == 'list_your_car':
        if st.session_state.logged_in:
            list_your_car_page()
        else:
            st.warning("Please log in to list your car")
            st.session_state.current_page = 'login'
    
    elif st.session_state.current_page == 'my_listings':
        if st.session_state.logged_in:
            my_listings_page()
        else:
            st.warning("Please log in to view your listings")
            st.session_state.current_page = 'login'
    
    elif st.session_state.current_page == 'notifications':
        if st.session_state.logged_in:
            notifications_page()
        else:
            st.warning("Please log in to view notifications")
            st.session_state.current_page = 'login'
    
    elif st.session_state.current_page == 'book_car':
        if st.session_state.logged_in:
            if st.session_state.selected_car:
                book_car_page()
            else:
                st.error("No car selected")
                st.session_state.current_page = 'browse_cars'
        else:
            st.warning("Please log in to book a car")
            st.session_state.current_page = 'login'

def create_folder_structure():
    """Create necessary folders for the application"""
    folders = ['images', 'temp', 'uploads']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

if __name__ == '__main__':
    try:
        # Ensure the database file exists and is properly initialized
        if not os.path.exists('car_rental.db'):
            setup_database()
            st.success("Database initialized successfully")
        
        # Create necessary folders
        create_folder_structure()
        
        # Run the main application
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
