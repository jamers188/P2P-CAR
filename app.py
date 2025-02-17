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

st.markdown("""
    <style>
        /* Root Variables for Theming */
        :root {
            --primary-color: #4B0082;
            --secondary-color: #6A0DAD;
            --background-color: #F4F4F8;
            --text-color: #333;
            --success-color: #28a745;
            --error-color: #dc3545;
            --warning-color: #FFC107;
        }

        /* Global Styles */
        .stApp {
            background-color: var(--background-color);
            font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
        }

        /* Layout Containers */
        .css-1d391kg {
            padding: 32px 16px;
        }

        /* Headings */
        h1 {
            color: var(--primary-color);
            text-align: center;
            padding: 16px 0;
            font-weight: 700;
            letter-spacing: -1px;
            font-size: 32px;
            margin-bottom: 24px;
        }

        h2 {
            color: var(--primary-color);
            font-size: 24px;
            margin: 16px 0;
        }

        h3 {
            color: var(--primary-color);
            font-size: 20px;
            margin: 12px 0;
        }

        /* Button Styling */
        .stButton>button {
            width: 100%;
            border-radius: 20px;
            height: 48px;
            background-color: var(--primary-color);
            color: white;
            border: none;
            margin: 5px 0;
            transition: all 0.3s ease;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 0 16px;
            cursor: pointer;
        }
        
        .stButton>button:hover {
            background-color: var(--secondary-color);
            transform: translateY(-3px);
            box-shadow: 0 6px 8px rgba(0,0,0,0.2);
        }

        /* Back Button Specific Styling */
        button[data-testid="stBaseButton-secondary"] {
            display: inline-flex;
            align-items: center;
            padding: 8px 16px;
            font-size: 14px;
            width: auto !important;
            height: 36px !important;
            background-color: transparent;
            color: var(--primary-color);
            border: 1px solid var(--primary-color);
        }

        button[data-testid="stBaseButton-secondary"]:hover {
            background-color: var(--primary-color);
            color: white;
        }

        /* SVG Icon Fixes */
        button svg {
            width: 16px !important;
            height: 16px !important;
        }

        /* Input Fields */
        input[type="text"], 
        input[type="password"],
        input[type="email"],
        input[type="number"],
        .stTextInput>div>div>input {
            border-radius: 20px;
            padding: 12px 16px;
            border: 2px solid var(--primary-color);
            transition: all 0.3s ease;
            width: 100%;
            font-size: 16px;
            background-color: white;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: var(--secondary-color);
            box-shadow: 0 0 10px rgba(106,13,173,0.2);
            outline: none;
        }

        /* Card Styling */
        .car-card {
            background-color: white;
            border-radius: 15px;
            padding: 24px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            margin: 16px 0;
            transition: all 0.3s ease;
            border: 1px solid #e1e1e8;
        }
        
        .car-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.15);
        }

        /* Status Badges */
        .status-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: inline-block;
        }
        
        .status-badge.pending {
            background-color: var(--warning-color);
            color: #333;
        }
        
        .status-badge.approved {
            background-color: var(--success-color);
            color: white;
        }
        
        .status-badge.rejected {
            background-color: var(--error-color);
            color: white;
        }

        /* Message Styling */
        .success-message {
            background-color: #E8F5E9;
            color: var(--success-color);
            padding: 16px;
            border-radius: 10px;
            margin: 16px 0;
            border-left: 4px solid var(--success-color);
        }
        
        .error-message {
            background-color: #FFEBEE;
            color: var(--error-color);
            padding: 16px;
            border-radius: 10px;
            margin: 16px 0;
            border-left: 4px solid var(--error-color);
        }

        /* Admin Review Card */
        .admin-review-card {
            background-color: white;
            border-radius: 15px;
            padding: 24px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            margin: 24px 0;
            border: 1px solid #e1e1e8;
        }

        /* Image Gallery */
        .image-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 16px 0;
        }
        
        .image-gallery img {
            width: 100%;
            border-radius: 10px;
            transition: transform 0.3s ease;
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }
        
        .image-gallery img:hover {
            transform: scale(1.05);
        }

        /* Form Elements */
        .stSelectbox {
            margin: 8px 0;
        }

        .stSelectbox>div>div {
            border-radius: 20px;
        }

        .stTextArea textarea {
            border-radius: 15px;
            padding: 12px;
            border: 2px solid var(--primary-color);
        }

        /* Checkbox Styling */
        .stCheckbox {
            margin: 8px 0;
        }

        .stCheckbox>div>div>label {
            color: var(--text-color);
            font-weight: 500;
        }

        /* Date Input Styling */
        .stDateInput>div>div {
            border-radius: 20px;
        }

        /* Sidebar Styling */
        .css-1d391kg .sidebar .sidebar-content {
            background-color: white;
            padding: 16px;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .stButton>button {
                height: 40px;
                font-size: 14px;
            }

            .car-card {
                padding: 16px;
            }

            .image-gallery {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }
        }

        /* Tooltip Styling */
        .tooltip {
            position: relative;
            display: inline-block;
        }

        .tooltip .tooltiptext {
            visibility: hidden;
            background-color: #555;
            color: white;
            text-align: center;
            border-radius: 6px;
            padding: 8px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            opacity: 0;
            transition: opacity 0.3s;
        }

        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
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
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Bookings table
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
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')
    
    # Car listings table
    c.execute('''
        CREATE TABLE IF NOT EXISTS car_listings (
            id INTEGER PRIMARY KEY,
            owner_email TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            price REAL NOT NULL,
            location TEXT NOT NULL,
            description TEXT,
            image_data TEXT,
            category TEXT NOT NULL,
            specs TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_email) REFERENCES users (email)
        )
    ''')
    
    # Notifications table
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
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

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
        },
        {
            'id': 2,
            'model': 'Rolls-Royce Ghost',
            'price': 3000,
            'location': 'Palm Jumeirah',
            'image': 'https://example.com/ghost.jpg',
            'specs': {
                'engine': '6.75L V12',
                'power': '563 hp',
                'acceleration': '0-60 mph in 4.8s'
            },
            'available': True
        }
    ],
    'SUV': [
        {
            'id': 3,
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
    ],
    'Sports': [
        {
            'id': 4,
            'model': 'Ferrari F8 Tributo',
            'price': 3500,
            'location': 'Downtown Dubai',
            'image': 'https://example.com/f8.jpg',
            'specs': {
                'engine': '3.9L V8 Twin-Turbo',
                'power': '710 hp',
                'acceleration': '0-60 mph in 2.9s'
            },
            'available': True
        }
    ]
}

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(full_name, email, phone, password):
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    try:
        c.execute(
            'INSERT INTO users (full_name, email, phone, password) VALUES (?, ?, ?, ?)',
            (full_name, email, phone, hash_password(password))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(email, password):
    try:
        # Special case for admin
        if email == "admin@luxuryrentals.com" and password == "admin123":
            return True
            
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Check credentials
        c.execute('SELECT password FROM users WHERE email = ?', (email,))
        result = c.fetchone()
        
        if result and result[0] == hashed_password:
            return True
        return False
    except sqlite3.Error as e:
        print(f"Database error during verification: {e}")
        return False
    finally:
        if 'conn' in locals():
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
        st.rerun()
    
    st.markdown("<h1>Login</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email = st.text_input('Email', key='login_email')
        password = st.text_input('Password', type='password', key='login_password')
        
        if st.button('Login', key='login_submit'):
            try:
                if verify_user(email, password):
                    # Set session state
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    
                    # Get user role
                    role = get_user_role(email)
                    
                    # Save session
                    save_session(email, 'browse_cars' if role != 'admin' else 'admin_panel')
                    
                    # Show success message
                    st.success('Login successful!')
                    
                    # Set next page based on role
                    st.session_state.current_page = 'admin_panel' if role == 'admin' else 'browse_cars'
                    
                    # Rerun to update the page
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error('Invalid email or password')
            except Exception as e:
                st.error(f'Login error: {str(e)}')
                print(f'Login error details: {str(e)}')


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

def reset_password_page():
    if st.button('← Back to Login', key='reset_back'):
        st.session_state.current_page = 'login'
    
    st.markdown("<h1>Reset Password</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email = st.text_input('Enter your email to reset password')
        
        if st.button('Send Reset Link', key='reset_submit'):
            st.success('Check your email for password reset instructions')

def browse_cars_page():
    # Navigation header
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
    
    st.markdown("<h3 style='color: #4B0082; margin-top: 1rem;'>Categories</h3>", unsafe_allow_html=True)
    cat_col1, cat_col2, cat_col3, cat_col4 = st.columns(4)
    
    with cat_col1:
        luxury = st.button('🎯 Luxury', key='luxury_filter')
    with cat_col2:
        suv = st.button('🚙 SUV', key='suv_filter')
    with cat_col3:
        sports = st.button('🏎 Sports', key='sports_filter')
    with cat_col4:
        if st.button('List Your Car', key='list_car'):
            st.session_state.current_page = 'list_your_car'
            st.rerun()
    
    # Display cars
    for category, cars in cars_data.items():
        if (luxury and category == 'Luxury') or \
           (suv and category == 'SUV') or \
           (sports and category == 'Sports') or \
           (not any([luxury, suv, sports])):
            
            st.markdown(f"<h2 style='color: #4B0082; margin-top: 2rem;'>{category}</h2>", unsafe_allow_html=True)
            
            cols = st.columns(3)
            for idx, car in enumerate(cars):
                if search.lower() in car['model'].lower() or not search:
                    with cols[idx % 3]:
                        st.markdown(f"""
                            <div class='car-card'>
                                <img src='{car['image']}' style='width: 100%; border-radius: 10px;'>
                                <h3 style='color: #4B0082; margin: 1rem 0;'>{car['model']}</h3>
                                <p style='color: #666;'>AED {car['price']}/day</p>
                                <p style='color: #666;'>{car['location']}</p>
                                <div style='color: #666; font-size: 0.9rem;'>
                                    <p>🏎 {car['specs']['engine']}</p>
                                    <p>⚡ {car['specs']['power']}</p>
                                    <p>🚀 {car['specs']['acceleration']}</p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button('Book Now', key=f"book_{car['id']}"):
                            st.session_state.selected_car = car
                            st.session_state.current_page = 'book_car'
                            st.rerun()

def list_your_car_page():
    st.markdown("<h1>List Your Car</h1>", unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        st.warning("Please log in to list your car")
        if st.button("Go to Login"):
            st.session_state.current_page = 'login'
        return
    
    # Back button
    if st.button('← Back to Browse', key='list_back'):
        st.session_state.current_page = 'browse_cars'
        st.rerun()
    
    # Create form for car listing
    with st.form("car_listing_form"):
        st.markdown("<h3 style='color: #4B0082;'>Car Details</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            model = st.text_input("Car Model*")
            year = st.number_input("Year*", min_value=1990, max_value=datetime.now().year)
            price = st.number_input("Daily Rate (AED)*", min_value=0)
            category = st.selectbox("Category*", ["Luxury", "SUV", "Sports", "Sedan"])
        
        with col2:
            location = st.text_input("Location*")
            engine = st.text_input("Engine Specifications*")
            mileage = st.number_input("Mileage (km)*", min_value=0)
            transmission = st.selectbox("Transmission*", ["Automatic", "Manual"])
        
        description = st.text_area("Description", help="Provide detailed information about your car")
        
        # Image upload
        uploaded_file = st.file_uploader("Upload Car Images*", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
        
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
        
        submit_button = st.form_submit_button("Submit Listing")
        
        if submit_button:
            if not all([model, year, price, location, engine, mileage, uploaded_file, agree]):
                st.error("Please fill in all required fields and accept terms and conditions")
            else:
                # Process image
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=image.format)
                img_byte_arr = img_byte_arr.getvalue()
                img_base64 = base64.b64encode(img_byte_arr).decode()
                
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
                
                # Save to database
                conn = sqlite3.connect('car_rental.db')
                c = conn.cursor()
                try:
                    c.execute('''
                        INSERT INTO car_listings 
                        (owner_email, model, year, price, location, description, 
                        image_data, category, specs, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        st.session_state.user_email, model, year, price, 
                        location, description, img_base64, category, 
                        json.dumps(specs), 'pending'
                    ))
                    conn.commit()
                    
                    # Create notification
                    create_notification(
                        st.session_state.user_email,
                        f"Your listing for {model} has been submitted for review",
                        'listing_submitted'
                    )
                    
                    st.success("Your car has been listed successfully! Our team will review it shortly.")
                    
                except Exception as e:
                    st.error(f"An error occurred while listing your car. Please try again.")
                finally:
                    conn.close()

def notifications_page():
    st.markdown("<h1>Notifications</h1>", unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        st.warning("Please log in to view notifications")
        if st.button("Go to Login"):
            st.session_state.current_page = 'login'
        return
    
    if st.button('← Back to Browse', key='notifications_back'):
        st.session_state.current_page = 'browse_cars'
        st.rerun()
    
    # Fetch notifications
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
                <div style='background-color: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <p style='margin: 0;'>{notif[2]}</p>
                    <small style='color: #666;'>{notif[5]}</small>
                </div>
            """, unsafe_allow_html=True)

def main():
    # Sidebar navigation for logged-in users
    if st.session_state.logged_in:
        with st.sidebar:
            st.markdown("### My Account")
            st.write(f"Welcome, {st.session_state.user_email}")
            
            unread_count = get_unread_notifications_count(st.session_state.user_email)
            if unread_count > 0:
                st.markdown(f"🔔 **{unread_count}** new notifications")
            
            st.markdown("---")
            
            if st.button("Browse Cars"):
                st.session_state.current_page = 'browse_cars'
            if st.button("My Listings"):
                st.session_state.current_page = 'my_listings'
            if st.button("List Your Car"):
                st.session_state.current_page = 'list_your_car'
            if st.button("Notifications"):
                st.session_state.current_page = 'notifications'
            
            st.markdown("---")
            if st.button("Logout"):
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
    elif st.session_state.current_page == 'reset_password':
        reset_password_page()
    elif st.session_state.current_page == 'browse_cars':
        browse_cars_page()
    elif st.session_state.current_page == 'list_your_car':
        list_your_car_page()
    elif st.session_state.current_page == 'notifications':
        notifications_page()

if __name__ == '__main__':
    main()
