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
def setup_database():
    """Initialize all database tables and admin user"""
    try:
        # Remove existing database to start fresh
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
        # In setup_database() function, modify the bookings table creation
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
                insurance_cost REAL DEFAULT 0,
                driver_cost REAL DEFAULT 0,
                delivery_cost REAL DEFAULT 0,
                vip_service_cost REAL DEFAULT 0,
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

        # Create indexes
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_listings_status ON car_listings(listing_status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_listings_category ON car_listings(category)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(booking_status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_email, read)')

        # Create admin user
        admin_password = hash_password('admin123')
        c.execute('''
            INSERT INTO users (full_name, email, phone, password, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            'Admin User',
            'admin@luxuryrentals.com',
            '+971500000000',
            admin_password,
            'admin'
        ))

        conn.commit()
        print("Database initialized successfully")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

# Sample car data
cars_data = {
    'Luxury': [
        {
            'id': 1,
            'model': 'Lamborghini Urus',
            'price': 2500,
            'location': 'Dubai Marina',
            'image': 'https://example.com/urus.jpg',
            'specs': {
                'engine': '4.0L V8 Twin-Turbo',
                'power': '641 hp',
                'acceleration': '0-60 mph in 3.5s'
            },
            'available': True
        }
    ],
    'SUV': [
        {
            'id': 2,
            'model': 'Range Rover Autobiography',
            'price': 1500,
            'location': 'Dubai Marina',
            'image': 'https://example.com/range_rover.jpg',
            'specs': {
                'engine': '5.0L V8',
                'power': '518 hp',
                'acceleration': '0-60 mph in 5.2s'
            },
            'available': True
        }
    ]
}

# Authentication functions
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(full_name, email, phone, password, role='user'):
    """Create a new user account"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Check if user already exists
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        if c.fetchone():
            return False
            
        # Create new user
        c.execute(
            'INSERT INTO users (full_name, email, phone, password, role) VALUES (?, ?, ?, ?, ?)',
            (full_name, email, phone, hash_password(password), role)
        )
        conn.commit()
        
        # Create welcome notification
        create_notification(
            email,
            "Welcome to Luxury Car Rentals! Start exploring our premium collection.",
            "welcome"
        )
        
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def verify_user(email, password):
    """Verify user credentials"""
    try:
        # Special case for admin
        if email == "admin@luxuryrentals.com" and password == "admin123":
            return True
            
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        c.execute('SELECT password FROM users WHERE email = ?', (email,))
        result = c.fetchone()
        
        if result and result[0] == hash_password(password):
            return True
        return False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def get_user_role(email):
    """Get user's role from database"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        c.execute('SELECT role FROM users WHERE email = ?', (email,))
        result = c.fetchone()
        return result[0] if result else 'user'
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 'user'
    finally:
        if 'conn' in locals():
            conn.close()

# Notification functions
def create_notification(user_email, message, type):
    """Create a new notification"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        c.execute(
            'INSERT INTO notifications (user_email, message, type) VALUES (?, ?, ?)',
            (user_email, message, type)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating notification: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def get_unread_notifications_count(user_email):
    """Get count of unread notifications"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        c.execute(
            'SELECT COUNT(*) FROM notifications WHERE user_email = ? AND read = FALSE',
            (user_email,)
        )
        return c.fetchone()[0]
    except sqlite3.Error as e:
        print(f"Error counting notifications: {e}")
        return 0
    finally:
        if 'conn' in locals():
            conn.close()

def mark_notifications_as_read(user_email):
    """Mark all notifications as read for a user"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        c.execute(
            'UPDATE notifications SET read = TRUE WHERE user_email = ?',
            (user_email,)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating notifications: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

# Utility functions
def create_folder_structure():
    """Create necessary folders for the application"""
    folders = ['images', 'temp', 'uploads']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

def format_currency(amount):
    """Format amount as AED currency"""
    return f"AED {amount:,.2f}"

def get_location_options():
    """Get list of available locations"""
    return [
        'Dubai Marina',
        'Palm Jumeirah',
        'Downtown Dubai',
        'Dubai Hills',
        'Business Bay',
        'JBR'
    ]

def get_car_categories():
    """Get list of car categories"""
    return [
        'Luxury',
        'SUV',
        'Sports',
        'Sedan',
        'Convertible',
        'Electric'
    ]

# Image handling functions
def save_uploaded_image(uploaded_file):
    """Save uploaded image and return base64 string"""
    try:
        image = Image.open(uploaded_file)
        # Resize image if too large
        max_size = (1200, 1200)
        image.thumbnail(max_size, Image.LANCZOS)
        
        # Convert to JPEG format
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
            
        # Save to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr = img_byte_arr.getvalue()
        
        # Convert to base64
        return base64.b64encode(img_byte_arr).decode()
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def validate_image(uploaded_file):
    """Validate uploaded image"""
    try:
        # Check file size (max 5MB)
        if uploaded_file.size > 5 * 1024 * 1024:
            return False, "Image size should be less than 5MB"
            
        # Check file type
        image = Image.open(uploaded_file)
        if image.format not in ['JPEG', 'PNG']:
            return False, "Only JPEG and PNG images are allowed"
            
        return True, "Image is valid"
    except Exception as e:
        return False, f"Invalid image: {str(e)}"

def resize_image_if_needed(image, max_size=(800, 800)):
    """Resize image if larger than max_size"""
    if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
        image.thumbnail(max_size, Image.LANCZOS)
    return image


# Page Components
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
        email = st.text_input('Email')
        password = st.text_input('Password', type='password')
        
        if st.button('Login', key='login_submit'):
            if verify_user(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                
                # Get user role
                role = get_user_role(email)
                
                if role == 'admin':
                    st.session_state.current_page = 'admin_panel'
                else:
                    st.session_state.current_page = 'browse_cars'
                st.success('Login successful!')
            else:
                st.error('Invalid credentials')
        
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        if st.button('Forgot Password?', key='forgot_password'):
            st.session_state.current_page = 'reset_password'

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
                    st.session_state.current_page = 'login'
                else:
                    st.error('Email already exists')

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
    
    # Category filters
    st.markdown("<h3 style='color: #4B0082; margin-top: 1rem;'>Categories</h3>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        luxury = st.button('🎯 Luxury', key='luxury_filter')
    with col2:
        suv = st.button('🚙 SUV', key='suv_filter')
    with col3:
        sports = st.button('🏎 Sports', key='sports_filter')
    with col4:
        if st.session_state.logged_in:
            if st.button('List Your Car', key='list_car'):
                st.session_state.current_page = 'list_your_car'
    
    # Display cars
    display_cars(search, luxury, suv, sports)

def display_cars(search="", luxury=False, suv=False, sports=False):
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Get approved listings with primary images
    query = '''
        SELECT cl.*, li.image_data
        FROM car_listings cl
        LEFT JOIN listing_images li ON cl.id = li.listing_id AND li.is_primary = TRUE
        WHERE cl.listing_status = 'approved'
    '''
    
    # Add category filters
    if any([luxury, suv, sports]):
        categories = []
        if luxury:
            categories.append('Luxury')
        if suv:
            categories.append('SUV')
        if sports:
            categories.append('Sports')
        query += f" AND cl.category IN ({','.join(['?']*len(categories))})"
        params = categories
    else:
        params = []
    
    # Add search filter
    if search:
        query += " AND (cl.model LIKE ? OR cl.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    query += " ORDER BY cl.created_at DESC"
    
    c.execute(query, params)
    listings = c.fetchall()
    
    if not listings:
        st.info("No cars found matching your criteria.")
        return
    
    # Group listings by category
    categorized_listings = {}
    for listing in listings:
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
                        <img src='data:image/jpeg;base64,{car[11]}' style='width: 100%; height: 250px; object-fit: cover; border-radius: 10px;'>
                        <h3 style='color: #4B0082; margin: 1rem 0;'>{car[2]} ({car[3]})</h3>
                        <p style='color: #666;'>{format_currency(car[4])}/day</p>
                        <p style='color: #666;'>{car[5]}</p>
                        <div style='color: #666; font-size: 0.9rem;'>
                            <p>🏎 {specs['engine']}</p>
                            <p>📊 {specs.get('mileage', '')}km</p>
                            <p>⚙️ {specs.get('transmission', '')}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button('View Details', key=f"details_{car[0]}"):
                    st.session_state.selected_car = {
                        'id': car[0],
                        'model': car[2],
                        'year': car[3],
                        'price': car[4],
                        'location': car[5],
                        'specs': car[8],  # Keep it as is, let show_car_details handle parsing
                        'image': car[11],
                        'owner_email': car[1]
                    }
                    st.session_state.current_page = 'car_details'
                    st.rerun()
                 
    
    conn.close()


def list_your_car_page():
    st.markdown("<h1>List Your Car</h1>", unsafe_allow_html=True)
    
    if st.button('← Back to Browse', key='list_back'):
        st.session_state.current_page = 'browse_cars'
    
    with st.form("car_listing_form"):
        st.markdown("<h3 style='color: #4B0082;'>Car Details</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            model = st.text_input("Car Model*")
            year = st.number_input("Year*", min_value=1990, max_value=datetime.now().year)
            price = st.number_input("Daily Rate (AED)*", min_value=0)
            category = st.selectbox("Category*", get_car_categories())
        
        with col2:
            location = st.selectbox("Location*", get_location_options())
            engine = st.text_input("Engine Specifications*")
            mileage = st.number_input("Mileage (km)*", min_value=0)
            transmission = st.selectbox("Transmission*", ["Automatic", "Manual"])
        
        description = st.text_area("Description", help="Provide detailed information about your car")
        
        # Image upload
        uploaded_files = st.file_uploader(
            "Upload Car Images* (Select multiple files)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.markdown("<div class='image-gallery'>", unsafe_allow_html=True)
            cols = st.columns(len(uploaded_files))
            for idx, uploaded_file in enumerate(uploaded_files):
                with cols[idx]:
                    # Validate image
                    is_valid, message = validate_image(uploaded_file)
                    if is_valid:
                        image = Image.open(uploaded_file)
                        st.image(image, caption=f"Image {idx+1}", use_column_width=True)
                    else:
                        st.error(message)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Additional features
        st.markdown("<h3 style='color: #4B0082;'>Additional Features</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            leather_seats = st.checkbox("Leather Seats")
            bluetooth = st.checkbox("Bluetooth")
        with col2:
            parking_sensors = st.checkbox("Parking Sensors")
            cruise_control = st.checkbox("Cruise Control")
        with col3:
            sunroof = st.checkbox("Sunroof")
            navigation = st.checkbox("Navigation")
        
        # Terms and conditions
        st.markdown("---")
        agree = st.checkbox("I agree to the terms and conditions")
        
        submit = st.form_submit_button("Submit Listing")
        
        if submit:
            if not all([model, year, price, location, engine, mileage, uploaded_files, agree]):
                st.error("Please fill in all required fields and accept terms and conditions")
            else:
                try:
                    conn = sqlite3.connect('car_rental.db')
                    c = conn.cursor()
                    
                    # Create specs dictionary
                    specs = {
                        "engine": engine,
                        "mileage": mileage,
                        "transmission": transmission,
                        "features": {
                            "leather_seats": leather_seats,
                            "bluetooth": bluetooth,
                            "parking_sensors": parking_sensors,
                            "cruise_control": cruise_control,
                            "sunroof": sunroof,
                            "navigation": navigation
                        }
                    }
                    
                    # Insert listing
                    c.execute('''
                        INSERT INTO car_listings 
                        (owner_email, model, year, price, location, description, 
                        category, specs, listing_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        st.session_state.user_email, model, year, price, 
                        location, description, category, 
                        json.dumps(specs), 'pending'
                    ))
                    
                    listing_id = c.lastrowid
                    
                    # Save images
                    # Modify this part of the image saving logic
                    for idx, file in enumerate(uploaded_files):
                        image_data = save_uploaded_image(file)
                        if image_data:
                            c.execute('''
                                INSERT INTO listing_images 
                                (listing_id, image_data, is_primary)
                                VALUES (?, ?, ?)
                            ''', (listing_id, image_data, idx == 0))  # Only the first image is primary
                    
                    conn.commit()
                    
                    # Create notification
                    create_notification(
                        st.session_state.user_email,
                        f"Your listing for {model} has been submitted for review",
                        'listing_submitted'
                    )
                    
                    st.success("Your car has been listed successfully! Our team will review it shortly.")
                    time.sleep(2)  # Give user time to read the message
                    st.session_state.current_page = 'my_listings'
                    
                except Exception as e:
                    st.error(f"An error occurred while listing your car: {str(e)}")
                finally:
                    conn.close()

def my_listings_page():
    st.markdown("<h1>My Listings</h1>", unsafe_allow_html=True)
    
    if st.button('← Back to Browse', key='my_listings_back'):
        st.session_state.current_page = 'browse_cars'
    
    col1, col2, col3 = st.columns([1,6,1])
    with col1:
        if st.button("+ List a New Car"):
            st.session_state.current_page = 'list_your_car'
    
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Get user's listings with their images
    c.execute('''
        SELECT cl.*, GROUP_CONCAT(li.image_data) as images
        FROM car_listings cl
        LEFT JOIN listing_images li ON cl.id = li.listing_id
        WHERE cl.owner_email = ?
        GROUP BY cl.id
        ORDER BY cl.created_at DESC
    ''', (st.session_state.user_email,))
    
    listings = c.fetchall()
    
    if not listings:
        st.info("You haven't listed any cars yet.")
    else:
        for listing in listings:
            with st.container():
                st.markdown(f"""
                    <div class='car-card'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <h3 style='color: #4B0082;'>{listing[2]} ({listing[3]})</h3>
                            <span class='status-badge {listing[9].lower()}'>
                                {listing[9].upper()}
                            </span>
                        </div>
                        <p><strong>Price:</strong> {format_currency(listing[4])}/day</p>
                        <p><strong>Location:</strong> {listing[5]}</p>
                        <p><strong>Category:</strong> {listing[7]}</p>
                        <p>{listing[6]}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                if listing[-1]:  # If there are images
                    images = listing[-1].split(',')
                    st.markdown("<div class='image-gallery'>", unsafe_allow_html=True)
                    cols = st.columns(len(images))
                    for idx, img_data in enumerate(images):
                        with cols[idx]:
                            st.image(
                                f"data:image/jpeg;base64,{img_data}",
                                caption=f"Image {idx+1}",
                                use_column_width=True
                            )
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Get review if exists
                c.execute('''
                    SELECT comment, review_status, created_at
                    FROM admin_reviews
                    WHERE listing_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (listing[0],))
                
                review = c.fetchone()
                if review:
                    st.markdown(f"""
                        <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 10px; margin-top: 1rem;'>
                            <p><strong>Admin Review:</strong> {review[0]}</p>
                            <small style='color: #666;'>Reviewed on {review[2]}</small>
                        </div>
                    """, unsafe_allow_html=True)
    
    conn.close()

def notifications_page():
    st.markdown("<h1>Notifications</h1>", unsafe_allow_html=True)
    
    if st.button('← Back to Browse', key='notifications_back'):
        st.session_state.current_page = 'browse_cars'
    
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Mark notifications as read
    c.execute('''
        UPDATE notifications 
        SET read = TRUE 
        WHERE user_email = ? AND read = FALSE
    ''', (st.session_state.user_email,))
    
    # Get all notifications
    c.execute('''
        SELECT * FROM notifications 
        WHERE user_email = ? 
        ORDER BY created_at DESC
    ''', (st.session_state.user_email,))
    
    notifications = c.fetchall()
    conn.commit()
    conn.close()
    
    if not notifications:
        st.info("No notifications")
    else:
        for notif in notifications:
            st.markdown(f"""
                <div style='background-color: white; padding: 1rem; border-radius: 10px; 
                     margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <p style='margin: 0;'>{notif[2]}</p>
                    <small style='color: #666;'>{notif[5]}</small>
                </div>
            """, unsafe_allow_html=True)

def admin_panel():
    st.markdown("<h1>Admin Panel</h1>", unsafe_allow_html=True)
    
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
    
    # Get pending listings
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
                        <p><strong>Price:</strong> {format_currency(listing[4])}/day</p>
                        <p><strong>Location:</strong> {listing[5]}</p>
                        <p><strong>Description:</strong> {listing[6]}</p>
                        <p><strong>Category:</strong> {listing[7]}</p>
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
                        approve = st.form_submit_button("✅ Approve")
                    with col2:
                        reject = st.form_submit_button("❌ Reject")
                    
                    if approve or reject:
                        status = 'approved' if approve else 'rejected'
                        
                        # Update listing status
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

def show_listings_by_status(status):
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
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
                        <p><strong>Price:</strong> {format_currency(listing[4])}/day</p>
                        <p><strong>Location:</strong> {listing[5]}</p>
                        <p><strong>Review Comment:</strong> {listing[12] or 'No comment'}</p>
                        <p><strong>Review Date:</strong> {listing[13]}</p>
                    </div>
                """, unsafe_allow_html=True)
                
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
def show_car_details(car):
    # Add a Go Back button
    col1, col2 = st.columns([1,7])
    with col1:
        if st.button('← Back'):
            st.session_state.current_page = 'browse_cars'
            st.session_state.selected_car = None
            st.rerun()
    
    st.markdown(f"<h1>{car['model']} ({car['year']})</h1>", unsafe_allow_html=True)
    
    # Fetch all images for this car
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    c.execute('SELECT image_data FROM listing_images WHERE listing_id = ?', (car['id'],))
    images = c.fetchall()
    conn.close()
    
    # Image gallery
    if images:
        st.markdown("<div class='image-gallery'>", unsafe_allow_html=True)
        cols = st.columns(len(images))
        for idx, (img_data,) in enumerate(images):
            with cols[idx]:
                st.image(
                    f"data:image/jpeg;base64,{img_data}", 
                    caption=f"Image {idx+1}",
                    use_container_width=True  # Updated from use_column_width
                )
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Car details
    # Use json.loads with error handling
    try:
        specs = json.loads(car['specs']) if isinstance(car['specs'], str) else car['specs']
    except json.JSONDecodeError:
        specs = {}
    
    st.markdown(f"""
        <div style='background-color: white; padding: 1rem; border-radius: 10px;'>
            <h3>Car Details</h3>
            <p><strong>Price:</strong> {format_currency(car['price'])}/day</p>
            <p><strong>Location:</strong> {car['location']}</p>
            <p><strong>Engine:</strong> {specs.get('engine', 'N/A')}</p>
            <p><strong>Mileage:</strong> {specs.get('mileage', 'N/A')} km</p>
            <p><strong>Transmission:</strong> {specs.get('transmission', 'N/A')}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Booking button
    if st.button('Book Now'):
        st.session_state.current_page = 'book_car'
        st.rerun()

def book_car_page():
    if st.button('← Back to Car Details'):
        st.session_state.current_page = 'car_details'
        st.rerun()
    
    # Check if a car is selected
    if not st.session_state.selected_car:
        st.error("No car selected")
        st.session_state.current_page = 'browse_cars'
        st.rerun()
        return
    
    car = st.session_state.selected_car
    
    st.markdown(f"<h1>Book {car['model']} ({car['year']})</h1>", unsafe_allow_html=True)
    
    # Define service prices
    service_prices = {
        'insurance': 50,  # per day
        'driver': 100,    # per day
        'delivery': 200,  # flat rate
        'vip_service': 300  # flat rate
    }
    
    # Booking form
    with st.form("booking_form"):
        st.markdown("### Booking Details")
        
        # Date selection
        col1, col2 = st.columns(2)
        with col1:
            pickup_date = st.date_input("Pickup Date", min_value=datetime.now().date())
        with col2:
            return_date = st.date_input("Return Date", min_value=pickup_date)
        
        # Location
        location = st.selectbox("Pickup Location", get_location_options())
        
        # Additional Services
        st.markdown("### Additional Services")
        col1, col2, col3 = st.columns(3)
        with col1:
            insurance = st.checkbox(f"Insurance (AED {service_prices['insurance']}/day)")
        with col2:
            driver = st.checkbox(f"Driver (AED {service_prices['driver']}/day)")
        with col3:
            delivery = st.checkbox(f"Delivery (Flat AED {service_prices['delivery']})")
        
        vip_service = st.checkbox(f"VIP Service (Flat AED {service_prices['vip_service']})")
        
        # Calculate total price
        rental_days = (return_date - pickup_date).days + 1
        base_price = car['price'] * rental_days
        
        # Additional service costs
        insurance_cost = service_prices['insurance'] * rental_days if insurance else 0
        driver_cost = service_prices['driver'] * rental_days if driver else 0
        delivery_cost = service_prices['delivery'] if delivery else 0
        vip_cost = service_prices['vip_service'] if vip_service else 0
        
        total_price = base_price + insurance_cost + driver_cost + delivery_cost + vip_cost
        
        # Display price breakdown
        st.markdown("### Price Breakdown")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Base Rental ({rental_days} days): {format_currency(base_price)}")
            if insurance:
                st.write(f"Insurance: {format_currency(insurance_cost)}")
            if driver:
                st.write(f"Driver: {format_currency(driver_cost)}")
        with col2:
            if delivery:
                st.write(f"Delivery: {format_currency(delivery_cost)}")
            if vip_service:
                st.write(f"VIP Service: {format_currency(vip_cost)}")
        
        st.markdown(f"### Total Cost: {format_currency(total_price)}")
        
        # Submit booking
        submit = st.form_submit_button("Confirm Booking")
        
        if submit:
            try:
                conn = sqlite3.connect('car_rental.db')
                c = conn.cursor()
                
                # Insert booking
                c.execute('''
                    INSERT INTO bookings 
                    (user_email, car_id, pickup_date, return_date, location, 
                    total_price, insurance, driver, delivery, vip_service,
                    insurance_cost, driver_cost, delivery_cost, vip_service_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    st.session_state.user_email, 
                    car['id'], 
                    pickup_date.strftime('%Y-%m-%d'), 
                    return_date.strftime('%Y-%m-%d'), 
                    location, 
                    total_price, 
                    insurance, 
                    driver, 
                    delivery, 
                    vip_service,
                    insurance_cost,
                    driver_cost,
                    delivery_cost,
                    vip_cost
                ))
                
                conn.commit()
                
                # Create notification
                create_notification(
                    st.session_state.user_email,
                    f"Booking confirmed for {car['model']} from {pickup_date} to {return_date}",
                    'booking_confirmed'
                )
                
                st.success("Booking confirmed successfully!")
                
                # Reset selected car and move to browse cars
                st.session_state.selected_car = None
                st.session_state.current_page = 'browse_cars'
                st.rerun()
                
            except Exception as e:
                st.error(f"An error occurred while booking: {str(e)}")
            finally:
                if 'conn' in locals():
                    conn.close()

def my_bookings_page():
    st.markdown("<h1>My Bookings</h1>", unsafe_allow_html=True)
    
    if st.button('← Back to Browse', key='bookings_back'):
        st.session_state.current_page = 'browse_cars'
    
    # Connect to database
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Fetch user's bookings with car details and owner information
    c.execute('''
        SELECT b.*, cl.model, cl.year, cl.owner_email, li.image_data
        FROM bookings b
        JOIN car_listings cl ON b.car_id = cl.id
        LEFT JOIN listing_images li ON cl.id = li.listing_id AND li.is_primary = TRUE
        WHERE b.user_email = ?
        ORDER BY b.created_at DESC
    ''', (st.session_state.user_email,))
    
    bookings = c.fetchall()
    conn.close()
    
    if not bookings:
        st.info("You haven't made any bookings yet.")
        return
    
    for booking in bookings:
        # Unpack booking details
        (booking_id, user_email, car_id, pickup_date, return_date, location, 
         total_price, insurance, driver, delivery, vip_service, 
         booking_status, created_at, owner_email, model, year, image_data,
         insurance_cost, driver_cost, delivery_cost, vip_service_cost) = booking
        
        # Create a card-like container
        with st.container():
            # Display car image if available
            if image_data:
                st.image(f"data:image/jpeg;base64,{image_data}", use_container_width=True)
            
            # Car details
            st.subheader(f"{model} ({year})")
            
            # Status display
            st.markdown(f"### Booking Status: {booking_status.upper()}")
            
            # Booking details
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Pickup Date:** {pickup_date}")
                st.write(f"**Location:** {location}")
                st.write(f"**Owner Email:** {owner_email}")
            
            with col2:
                st.write(f"**Return Date:** {return_date}")
                st.write(f"**Total Price:** {format_currency(total_price)}")
            
            # Price Breakdown
            st.subheader("Price Breakdown")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Base Rental: {format_currency(total_price - insurance_cost - driver_cost - delivery_cost - vip_service_cost)}")
                if insurance:
                    st.write(f"Insurance: {format_currency(insurance_cost)}")
                if driver:
                    st.write(f"Driver: {format_currency(driver_cost)}")
            with col2:
                if delivery:
                    st.write(f"Delivery: {format_currency(delivery_cost)}")
                if vip_service:
                    st.write(f"VIP Service: {format_currency(vip_service_cost)}")
            
            # Additional Services
            st.subheader("Additional Services")
            services = []
            if insurance:
                services.append(("Insurance", insurance_cost))
            if driver:
                services.append(("Driver", driver_cost))
            if delivery:
                services.append(("Delivery", delivery_cost))
            if vip_service:
                services.append(("VIP Service", vip_service_cost))
            
            if services:
                for service, cost in services:
                    st.info(f"{service}: {format_currency(cost)}")
            else:
                st.info("No additional services selected")
            
            st.markdown("---")
            
def owner_bookings_page():
    st.markdown("<h1>Bookings for My Cars</h1>", unsafe_allow_html=True)
    
    if st.button('← Back to Browse', key='owner_bookings_back'):
        st.session_state.current_page = 'browse_cars'
    
    # Connect to database
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Fetch bookings for cars owned by the current user
    c.execute('''
        SELECT b.*, cl.model, cl.year, b.user_email as renter_email, li.image_data
        FROM bookings b
        JOIN car_listings cl ON b.car_id = cl.id
        LEFT JOIN listing_images li ON cl.id = li.listing_id AND li.is_primary = TRUE
        WHERE cl.owner_email = ?
        ORDER BY b.created_at DESC
    ''', (st.session_state.user_email,))
    
    bookings = c.fetchall()
    conn.close()
    
    if not bookings:
        st.info("No bookings for your cars.")
        return
    
    for booking in bookings:
        # Unpack booking details
        (booking_id, renter_email, car_id, pickup_date, return_date, location, 
         total_price, insurance, driver, delivery, vip_service, 
         booking_status, created_at, model, year, booking_renter_email, image_data) = booking
        
        # Create a container for each booking
        with st.container():
            # Display car image if available
            if image_data:
                st.image(f"data:image/jpeg;base64,{image_data}", use_container_width=True)
            
            # Car and Booking Details
            st.subheader(f"{model} ({year})")
            
            # Status display
            status_colors = {
                'pending': 'yellow',
                'confirmed': 'green',
                'rejected': 'red'
            }
            st.markdown(f"### Booking Status: {booking_status.upper()}")
            
            # Booking details
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Renter:** {renter_email}")
                st.write(f"**Pickup Date:** {pickup_date}")
                st.write(f"**Location:** {location}")
            
            with col2:
                st.write(f"**Return Date:** {return_date}")
                st.write(f"**Total Price:** {format_currency(total_price)}")
            
            # Additional Services
            st.subheader("Additional Services")
            services = []
            if insurance:
                services.append("Insurance")
            if driver:
                services.append("Driver")
            if delivery:
                services.append("Delivery")
            if vip_service:
                services.append("VIP Service")
            
            if services:
                for service in services:
                    st.info(service)
            else:
                st.info("No additional services selected")
            
            # Approval buttons
            col1, col2 = st.columns(2)
            with col1:
                approve = st.button("Approve Booking", key=f"approve_{booking_id}")
            with col2:
                reject = st.button("Reject Booking", key=f"reject_{booking_id}")
            
            if approve or reject:
                new_status = 'confirmed' if approve else 'rejected'
                
                # Update booking status
                conn = sqlite3.connect('car_rental.db')
                c = conn.cursor()
                c.execute('''
                    UPDATE bookings 
                    SET booking_status = ? 
                    WHERE id = ?
                ''', (new_status, booking_id))
                
                # Create notification for renter
                create_notification(
                    renter_email,
                    f"Your booking for {model} has been {new_status}.",
                    f'booking_{new_status}'
                )
                
                conn.commit()
                conn.close()
                
                st.success(f"Booking {new_status}")
                st.experimental_rerun()
            
            st.markdown("---")

def show_approved_listings():
    st.subheader("Approved Listings")
    show_listings_by_status('approved')

def show_rejected_listings():
    st.subheader("Rejected Listings")
    show_listings_by_status('rejected')

def main():
    # Create necessary folders
    create_folder_structure()
    
    # Setup database if not exists
    if not os.path.exists('car_rental.db'):
        setup_database()
    
    # Sidebar navigation for logged-in users
    if st.session_state.logged_in:
        with st.sidebar:
            st.markdown("### My Account")
            st.write(f"Welcome, {st.session_state.user_email}")
            
            # Get user role
            role = get_user_role(st.session_state.user_email)
            
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


            # In the sidebar navigation section
            if st.button("🚗 My Bookings"):
                st.session_state.current_page = 'my_bookings'

            if st.button("📋 Bookings for My Cars"):
                st.session_state.current_page = 'owner_bookings'
            
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
        if st.session_state.logged_in and get_user_role(st.session_state.user_email) == 'admin':
            admin_panel()
        else:
            st.error("Access denied. Admin privileges required.")
            st.session_state.current_page = 'browse_cars'
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

    elif st.session_state.current_page == 'car_details':
        if st.session_state.selected_car:
            show_car_details(st.session_state.selected_car)
        else:
            st.error("No car selected")
            st.session_state.current_page = 'browse_cars'

    elif st.session_state.current_page == 'book_car':
        if st.session_state.logged_in:
            book_car_page()
        else:
            st.warning("Please log in to book a car")
            st.session_state.current_page = 'login'

    elif st.session_state.current_page == 'my_bookings':
        if st.session_state.logged_in:
            my_bookings_page()
        else:
            st.warning("Please log in to view your bookings")
            st.session_state.current_page = 'login'
    
    elif st.session_state.current_page == 'owner_bookings':
        if st.session_state.logged_in:
            owner_bookings_page()
        else:
            st.warning("Please log in to view bookings")
            st.session_state.current_page = 'login'
    
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        print(f"Error details: {str(e)}")
