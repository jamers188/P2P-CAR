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
import time
from dateutil.relativedelta import relativedelta

# Page config and custom CSS
st.set_page_config(
    page_title="Luxury Car Rentals",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        /* Root Variables for Theming */
        :root {
            --primary-color: #4B0082;
            --secondary-color: #6A0DAD;
            --background-color: #F4F4F8;
            --text-color: #333;
            --border-radius: 10px;
        }

        /* Global Styles */
        .stApp {
            background-color: var(--background-color);
            font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
            padding: 2rem;
        }

        /* Layout */
        .main-content {
            max-width: 1200px;
            margin: auto;
        }

        /* Button Styling */
        .stButton>button {
            width: 100%;
            border-radius: var(--border-radius);
            height: 3em;
            background-color: var(--primary-color);
            color: white;
            border: none;
            margin: 5px 0;
            transition: all 0.3s ease;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .stButton>button:hover {
            background-color: var(--secondary-color);
            transform: translateY(-3px);
            box-shadow: 0 6px 8px rgba(0,0,0,0.2);
        }
        
        /* Input Styling */
        input[type="text"], input[type="password"] {
            border-radius: var(--border-radius);
            padding: 10px 15px;
            border: 2px solid var(--primary-color);
            transition: all 0.3s ease;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: var(--secondary-color);
            box-shadow: 0 0 10px rgba(106,13,173,0.2);
        }
        
        /* Headings */
        h1, h2, h3 {
            color: var(--primary-color);
            text-align: center;
            padding: 1rem 0;
            font-weight: 700;
            letter-spacing: -1px;
        }
        
        /* Card Styling */
        .card {
            background-color: white;
            border-radius: var(--border-radius);
            padding: 1rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            margin: 1rem 0;
            transition: all 0.3s ease;
            border: 1px solid #e1e1e8;
        }
        
        .card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.15);
        }
        
        /* Image Gallery */
        .image-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .image-gallery img {
            width: 100%;
            border-radius: var(--border-radius);
            transition: transform 0.3s ease;
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }
        
        .image-gallery img:hover {
            transform: scale(1.05);
        }

        /* Profile Picture */
        .profile-picture {
            width: 100px;
            height: 100px;
            border-radius: var(--border-radius);
            object-fit: cover;
            border: 2px solid var(--primary-color);
            margin: auto;
        }
        
        /* Status Badges */
        .status-badge {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            color: white;
        }
        
        .status-badge.pending {
            background-color: #FFC107;
        }
        
        .status-badge.approved {
            background-color: #28a745;
        }
        
        .status-badge.rejected {
            background-color: #dc3545;
        }
        
        /* Subscription Cards */
        .subscription-card {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .subscription-card.premium {
            border-top: 5px solid #4B0082;
        }
        
        .subscription-card.elite {
            border-top: 5px solid #FFD700;
        }
        
        .subscription-price {
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary-color);
            margin: 15px 0;
        }
        
        /* Insurance Claim Cards */
        .insurance-claim-card {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
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
    try:
        db_exists = os.path.exists('car_rental.db')
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Create users table with profile picture field
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                profile_picture TEXT,
                subscription_type TEXT DEFAULT 'free_renter',
                subscription_expiry TEXT,
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

        # Create bookings table with all required columns
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
                insurance_price REAL DEFAULT 0,
                driver_price REAL DEFAULT 0,
                delivery_price REAL DEFAULT 0,
                vip_service_price REAL DEFAULT 0,
                FOREIGN KEY (user_email) REFERENCES users (email),
                FOREIGN KEY (car_id) REFERENCES car_listings (id)
            )
        ''')

        # Create insurance_claims table
        c.execute('''
            CREATE TABLE IF NOT EXISTS insurance_claims (
                id INTEGER PRIMARY KEY,
                booking_id INTEGER NOT NULL,
                user_email TEXT NOT NULL,
                claim_date TEXT NOT NULL,
                incident_date TEXT NOT NULL,
                description TEXT NOT NULL,
                damage_type TEXT NOT NULL,
                claim_amount REAL NOT NULL,
                evidence_images TEXT,
                claim_status TEXT DEFAULT 'pending',
                admin_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (booking_id) REFERENCES bookings (id),
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

        # Create subscriptions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS subscription_history (
                id INTEGER PRIMARY KEY,
                user_email TEXT NOT NULL,
                plan_type TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                amount_paid REAL NOT NULL,
                payment_method TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users (email)
            )
        ''')

        # Create indexes
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_listings_status ON car_listings(listing_status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_listings_category ON car_listings(category)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(booking_status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_email, read)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_claims_status ON insurance_claims(claim_status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscription_history(user_email)')

        # Create admin user only if database is new
        if not db_exists:
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

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(full_name, email, phone, password, profile_picture=None, role='user'):
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        if c.fetchone():
            return False
            
        c.execute(
            'INSERT INTO users (full_name, email, phone, password, profile_picture, role) VALUES (?, ?, ?, ?, ?, ?)',
            (full_name, email, phone, hash_password(password), profile_picture, role)
        )
        conn.commit()
        
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
    try:
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

def get_user_info(email):
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        result = c.fetchone()
        conn.close()
        return result
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def update_user_subscription(email, plan_type, months=1):
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        start_date = datetime.now().date()
        end_date = start_date + relativedelta(months=months)
        
        c.execute('''
            UPDATE users 
            SET subscription_type = ?, subscription_expiry = ?
            WHERE email = ?
        ''', (plan_type, end_date.isoformat(), email))
        
        amount = 0
        if plan_type == 'premium_renter':
            amount = 20 * months
        elif plan_type == 'elite_renter':
            amount = 50 * months
        elif plan_type == 'premium_host':
            amount = 50 * months
        elif plan_type == 'elite_host':
            amount = 100 * months
        
        c.execute('''
            INSERT INTO subscription_history
            (user_email, plan_type, start_date, end_date, amount_paid, payment_method, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            email, 
            plan_type, 
            start_date.isoformat(), 
            end_date.isoformat(), 
            amount,
            'Credit Card',
            'active'
        ))
        
        conn.commit()
        
        create_notification(
            email,
            f"Your subscription to {plan_type.replace('_', ' ').title()} has been activated until {end_date.strftime('%d %b %Y')}",
            "subscription_activated"
        )

        return True
    except sqlite3.Error as e:
        print(f"Subscription update error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def get_subscription_benefits(plan_type):
    benefits = {
        'free_renter': {
            'service_fees': 'Standard',
            'booking_priority': 'None',
            'discounts': 'None',
            'cancellations': 'Penalties apply',
            'roadside_assistance': 'Not included',
            'support': 'Standard',
            'vehicle_access': 'General listings only',
            'damage_waiver': 'None'
        },
        'premium_renter': {
            'service_fees': 'Reduced',
            'booking_priority': 'Medium priority',
            'discounts': 'Up to 10% on select cars',
            'cancellations': 'Limited free cancellations',
            'roadside_assistance': 'Included',
            'support': 'Fast response',
            'vehicle_access': 'Exclusive luxury vehicles',
            'damage_waiver': 'Partial protection'
        },
        'elite_renter': {
            'service_fees': 'Lowest',
            'booking_priority': 'Highest priority',
            'discounts': 'Up to 20% on rentals',
            'cancellations': 'Unlimited free cancellations',
            'roadside_assistance': 'Premium service',
            'support': '24/7 priority',
            'vehicle_access': 'All vehicles including exotic',
            'damage_waiver': 'Full protection',
            'upgrades': 'Free when available',
            'concierge': 'Personal booking assistant'
        },
        'free_host': {
            'visibility': 'Standard',
            'commission': '15% per booking',
            'pricing_tools': 'Basic',
            'damage_protection': 'Basic',
            'fraud_prevention': 'Basic',
            'payout_speed': 'Standard (3-5 days)',
            'support': 'Standard',
            'marketing': 'None'
        },
        'premium_host': {
            'visibility': 'Boosted',
            'commission': '10% per booking',
            'pricing_tools': 'Dynamic optimization',
            'damage_protection': 'Extra protection',
            'fraud_prevention': 'Enhanced verification',
            'payout_speed': 'Fast (1-2 days)',
            'support': 'Priority',
            'marketing': 'Eligible for promotions'
        },
        'elite_host': {
            'visibility': 'Top placement',
            'commission': '5% or zero up to limit',
            'pricing_tools': 'AI-driven optimization',
            'damage_protection': 'Full protection',
            'fraud_prevention': 'AI risk assessment',
            'payout_speed': 'Same-day',
            'support': 'Dedicated manager',
            'marketing': 'Featured in app promotions'
        }
    }
    
    return benefits.get(plan_type, benefits['free_renter'])

# Notification functions
def create_notification(user_email, message, type):
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

# Insurance claim functions
def create_insurance_claim(booking_id, user_email, incident_date, description, damage_type, claim_amount, evidence_images=None):
    """Create a new insurance claim"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Check if this booking exists and belongs to the user
        c.execute('SELECT * FROM bookings WHERE id = ? AND user_email = ?', (booking_id, user_email))
        booking = c.fetchone()
        
        if not booking:
            return False, "Booking not found or doesn't belong to you"
        
        # Check if insurance was included in the booking
        if not booking[7]:  # insurance column
            return False, "This booking doesn't include insurance coverage"
        
        # Insert claim
        c.execute('''
            INSERT INTO insurance_claims 
            (booking_id, user_email, claim_date, incident_date, description, 
            damage_type, claim_amount, evidence_images, claim_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            booking_id,
            user_email,
            datetime.now().date().isoformat(),
            incident_date,
            description,
            damage_type,
            claim_amount,
            evidence_images,
            'pending'
        ))
        
        conn.commit()
        
        # Create notification for user
        create_notification(
            user_email,
            f"Your insurance claim for booking #{booking_id} has been submitted for review.",
            "claim_submitted"
        )
        
        # Create notification for admin
        admin_email = "admin@luxuryrentals.com"
        create_notification(
            admin_email,
            f"New insurance claim submitted by {user_email} for booking #{booking_id}.",
            "admin_claim_submitted"
        )
        
        return True, "Claim submitted successfully"
    except sqlite3.Error as e:
        print(f"Error creating claim: {e}")
        return False, f"Database error: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()

def update_claim_status(claim_id, new_status, admin_notes=None):
    """Update insurance claim status"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Get claim details first
        c.execute('SELECT user_email, booking_id FROM insurance_claims WHERE id = ?', (claim_id,))
        claim = c.fetchone()
        
        if not claim:
            return False, "Claim not found"
        
        # Update claim status
        if admin_notes:
            c.execute(
                'UPDATE insurance_claims SET claim_status = ?, admin_notes = ? WHERE id = ?',
                (new_status, admin_notes, claim_id)
            )
        else:
            c.execute(
                'UPDATE insurance_claims SET claim_status = ? WHERE id = ?',
                (new_status, claim_id)
            )
            
        conn.commit()
        
        # Create notification for user
        user_email, booking_id = claim
        create_notification(
            user_email,
            f"Your insurance claim for booking #{booking_id} has been {new_status}. {admin_notes if admin_notes else ''}",
            f"claim_{new_status}"
        )
        
        return True, f"Claim successfully {new_status}"
    except sqlite3.Error as e:
        print(f"Error updating claim: {e}")
        return False, f"Database error: {str(e)}"
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

def get_damage_types():
    """Get list of damage types for insurance claims"""
    return [
        'Minor Scratch/Dent',
        'Major Body Damage',
        'Windshield/Glass Damage',
        'Interior Damage',
        'Mechanical Failure',
        'Tire/Wheel Damage',
        'Water/Flood Damage',
        'Fire Damage',
        'Theft/Stolen Vehicle',
        'Vandalism',
        'Collision',
        'Other'
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
    logo_url = "https://raw.githubusercontent.com/jamers188/P2P-CAR/main/kipride.png"
    st.markdown(f"""
        <div style='text-align: center;'>
            <img src="{logo_url}" alt="Luxury Car Rentals" style='max-width: 300px;'>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h2 style='color: #4B0082;'>Experience Luxury on Wheels</h2>
            <p style='font-size: 1.2rem; color: #666;'>Discover our exclusive collection of premium vehicles</p>
            <p style='font-size: 0.9rem; color: #28a745;'>Committed to SDGs 11, 12 & 13: Building sustainable mobility solutions</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([1,2,2,1])
    with col2:
        if st.button('Login', key='welcome_login'):
            st.session_state.current_page = 'login'
        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
        if st.button('Create Account', key='welcome_signup'):
            st.session_state.current_page = 'signup'
    
    with col3:
        if st.button('Browse Cars', key='welcome_browse'):
            st.session_state.current_page = 'browse_cars'
        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
        if st.button('About Us', key='welcome_about'):
            st.session_state.current_page = 'about_us'

def login_page():
    if st.button('← Back to Welcome', key='login_back'):
        st.session_state.current_page = 'welcome'
    
    st.markdown("<h1>Welcome Back</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email = st.text_input('Email')
        password = st.text_input('Password', type='password')
    
        if st.button('Login', key='login_submit'):
            # Special case for admin
            if email == "admin@luxuryrentals.com" and password == "admin123":
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.current_page = 'admin_panel'
                st.success('Admin login successful!')
                st.rerun()
            # Regular user authentication    
            elif verify_user(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                
                # Get user role
                role = get_user_role(email)
                
                if role == 'admin':
                    st.session_state.current_page = 'admin_panel'
                    st.success('Admin login successful!')
                else:
                    st.session_state.current_page = 'browse_cars'
                    st.success('Login successful!')
                
                st.rerun()
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
        
        # Profile picture upload (optional)
        st.markdown("### Profile Picture (Optional)")
        profile_pic = st.file_uploader("Upload a profile picture", type=["jpg", "jpeg", "png"])
        profile_pic_data = None
        
        if profile_pic:
            try:
                # Preview the image
                image = Image.open(profile_pic)
                col1, col2, col3 = st.columns([1,1,1])
                with col2:
                    st.image(image, width=150, caption="Profile Preview")
                profile_pic_data = save_uploaded_image(profile_pic)
            except Exception as e:
                st.error(f"Error processing image: {e}")
        
        if st.button('Create Account', key='signup_submit'):
            if password != confirm_password:
                st.error('Passwords do not match')
            elif not all([full_name, email, phone, password]):
                st.error('Please fill in all required fields')
            else:
                if create_user(full_name, email, phone, password, profile_pic_data):
                    st.success('Account created successfully!')
                    st.session_state.current_page = 'login'
                else:
                    st.error('Email already exists')

def browse_cars_page():
    col1, col2 = st.columns([9, 1])
    with col2:
        if st.session_state.logged_in:
            # Get user info for profile display
            user_info = get_user_info(st.session_state.user_email)
            if user_info:
                # Display profile picture if available, otherwise just name
                if user_info[6]:  # profile_picture field
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                            <img src="data:image/jpeg;base64,{user_info[6]}" class="profile-picture">
                        </div>
                        <div style="text-align: center; font-size: 0.8rem; margin-bottom: 5px;">
                            {user_info[1]}
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style="text-align: center; font-size: 0.8rem; margin-bottom: 5px;">
                            {user_info[1]}
                        </div>
                    """, unsafe_allow_html=True)
                
            # Notifications
            unread_count = get_unread_notifications_count(st.session_state.user_email)
            if unread_count > 0:
                if st.button(f'🔔 ({unread_count})', key='notifications'):
                    st.session_state.current_page = 'notifications'
            
            if st.button('Logout', key='logout'):
                st.session_state.logged_in = False
                st.session_state.user_email = None
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
            elif st.button('Subscription Plans', key='subscription_plans'):
                st.session_state.current_page = 'subscription_plans'
    
    # Display cars
    display_cars(search, luxury, suv, sports)

def display_cars(search="", luxury=False, suv=False, sports=False):
    # Hardcoded luxury cars data with multiple images
    luxury_cars = [
        {
            "id": 1,
            "model": "Rolls-Royce Phantom",
            "year": 2022,
            "price": 2500,
            "location": "Downtown Dubai",
            "description": "The epitome of luxury, the Phantom offers unparalleled comfort and craftsmanship.",
            "category": "Luxury",
            "specs": {
                "engine": "6.75L V12",
                "mileage": 5000,
                "transmission": "Automatic",
                "features": ["Handcrafted interior", "Starlight headliner", "Air suspension"]
            },
            "images": [
                "https://www.rolls-roycemotorcars.com/content/dam/rrmc/marketUK/rollsroycemotorcars_com/phantom-series-i/page-properties/Phantom-Series-II-Hero-Desktop.jpg",
                "https://www.rolls-roycemotorcars.com/content/dam/rrmc/marketUK/rollsroycemotorcars_com/phantom-series-i/gallery/exterior/Phantom-Ext-01.jpg",
                "https://www.rolls-roycemotorcars.com/content/dam/rrmc/marketUK/rollsroycemotorcars_com/phantom-series-i/gallery/interior/Phantom-Int-01.jpg"
            ]
        },
        {
            "id": 2,
            "model": "Bentley Continental GT",
            "year": 2023,
            "price": 1800,
            "location": "Palm Jumeirah",
            "description": "Grand tourer with exquisite craftsmanship and exhilarating performance.",
            "category": "Luxury",
            "specs": {
                "engine": "4.0L V8",
                "mileage": 3000,
                "transmission": "Automatic",
                "features": ["Hand-stitched leather", "Rotating display", "All-wheel drive"]
            },
            "images": [
                "https://www.bentleymotors.com/content/dam/bentley/Master/Models/continental-gt/continental-gt-models-overview/continental-gt-models-overview-1920x1080.jpg",
                "https://www.bentleymotors.com/content/dam/bentley/Master/Models/continental-gt/continental-gt-models-overview/continental-gt-models-overview-2-1920x1080.jpg",
                "https://www.bentleymotors.com/content/dam/bentley/Master/Models/continental-gt/continental-gt-models-overview/continental-gt-models-overview-3-1920x1080.jpg"
            ]
        },
        {
            "id": 3,
            "model": "Mercedes-Maybach S-Class",
            "year": 2023,
            "price": 1500,
            "location": "Business Bay",
            "description": "The ultimate in luxury and technology from Mercedes-Benz.",
            "category": "Luxury",
            "specs": {
                "engine": "4.0L V8 Biturbo",
                "mileage": 4500,
                "transmission": "Automatic",
                "features": ["Executive rear seats", "Burmester sound system", "Magic Body Control"]
            },
            "images": [
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/maybach-s-class/s-class-sedan/2023/overview/2023-MAYBACH-S-CLASS-SEDAN-OV-HERO-DESKTOP.jpg",
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/maybach-s-class/s-class-sedan/2023/gallery/exterior/2023-MAYBACH-S-CLASS-SEDAN-GAL-EXT-001-D.jpg",
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/maybach-s-class/s-class-sedan/2023/gallery/interior/2023-MAYBACH-S-CLASS-SEDAN-GAL-INT-001-D.jpg"
            ]
        },
        {
            "id": 4,
            "model": "Aston Martin DBS Superleggera",
            "year": 2022,
            "price": 2200,
            "location": "Dubai Marina",
            "description": "British grand tourer with breathtaking performance and style.",
            "category": "Luxury",
            "specs": {
                "engine": "5.2L V12 Twin-Turbo",
                "mileage": 3500,
                "transmission": "Automatic",
                "features": ["Carbon fiber body", "Bang & Olufsen sound", "Adaptive suspension"]
            },
            "images": [
                "https://www.astonmartin.com/-/media/images/models/dbs/dbs-superleggera/overview/dbs-superleggera-overview-01.jpg",
                "https://www.astonmartin.com/-/media/images/models/dbs/dbs-superleggera/gallery/dbs-superleggera-gallery-01.jpg",
                "https://www.astonmartin.com/-/media/images/models/dbs/dbs-superleggera/gallery/dbs-superleggera-gallery-02.jpg"
            ]
        },
        {
            "id": 5,
            "model": "Porsche Panamera Turbo S",
            "year": 2023,
            "price": 1900,
            "location": "JBR",
            "description": "Luxury sports sedan with exceptional performance.",
            "category": "Luxury",
            "specs": {
                "engine": "4.0L V8 Twin-Turbo",
                "mileage": 4000,
                "transmission": "Automatic",
                "features": ["Sport Chrono package", "Premium package", "Night vision assist"]
            },
            "images": [
                "https://www.porsche.com/international/models/panamera/panamera-models/panamera-turbo-s/panamera-turbo-s-models-series-ii/",
                "https://www.porsche.com/international/models/panamera/panamera-models/panamera-turbo-s/panamera-turbo-s-models-series-ii/gallery/",
                "https://www.porsche.com/international/models/panamera/panamera-models/panamera-turbo-s/panamera-turbo-s-models-series-ii/gallery/"
            ]
        }
    ]

    suv_cars = [
        {
            "id": 11,
            "model": "Range Rover Autobiography",
            "year": 2023,
            "price": 1200,
            "location": "Dubai Hills",
            "description": "The most luxurious Range Rover with exquisite interior and powerful performance.",
            "category": "SUV",
            "specs": {
                "engine": "4.4L V8",
                "mileage": 6000,
                "transmission": "Automatic",
                "features": ["Executive seating", "Meridian sound system", "Terrain Response 2"]
            },
            "images": [
                "https://www.landrover.com/content/dam/landrover/range-rover/range-rover/range-rover-l460/range-rover-l460-overview/range-rover-l460-overview-1920x1080.jpg",
                "https://www.landrover.com/content/dam/landrover/range-rover/range-rover/range-rover-l460/range-rover-l460-gallery/range-rover-l460-gallery-1-1920x1080.jpg",
                "https://www.landrover.com/content/dam/landrover/range-rover/range-rover/range-rover-l460/range-rover-l460-gallery/range-rover-l460-gallery-2-1920x1080.jpg"
            ]
        },
        {
            "id": 12,
            "model": "Bentley Bentayga",
            "year": 2023,
            "price": 1600,
            "location": "JBR",
            "description": "The world's most luxurious SUV with exceptional performance.",
            "category": "SUV",
            "specs": {
                "engine": "4.0L V8",
                "mileage": 4000,
                "transmission": "Automatic",
                "features": ["Mulliner driving specs", "All-terrain capability", "Handcrafted interior"]
            },
            "images": [
                "https://www.bentleymotors.com/content/dam/bentley/Master/Models/bentayga/bentayga-models-overview/bentayga-models-overview-1920x1080.jpg",
                "https://www.bentleymotors.com/content/dam/bentley/Master/Models/bentayga/bentayga-models-overview/bentayga-models-overview-2-1920x1080.jpg",
                "https://www.bentleymotors.com/content/dam/bentley/Master/Models/bentayga/bentayga-models-overview/bentayga-models-overview-3-1920x1080.jpg"
            ]
        },
        {
            "id": 13,
            "model": "Mercedes-Benz G-Class",
            "year": 2023,
            "price": 1400,
            "location": "Business Bay",
            "description": "Iconic luxury off-roader with unmatched presence.",
            "category": "SUV",
            "specs": {
                "engine": "4.0L V8 Biturbo",
                "mileage": 5000,
                "transmission": "Automatic",
                "features": ["Three differential locks", "AMG performance", "Handcrafted interior"]
            },
            "images": [
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/g-class/suv/2023/overview/2023-G-CLASS-SUV-OV-HERO-DESKTOP.jpg",
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/g-class/suv/2023/gallery/exterior/2023-G-CLASS-SUV-GAL-EXT-001-D.jpg",
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/g-class/suv/2023/gallery/interior/2023-G-CLASS-SUV-GAL-INT-001-D.jpg"
            ]
        },
        {
            "id": 14,
            "model": "Lamborghini Urus",
            "year": 2023,
            "price": 2000,
            "location": "Palm Jumeirah",
            "description": "Super SUV with Lamborghini performance and Italian design.",
            "category": "SUV",
            "specs": {
                "engine": "4.0L V8 Twin-Turbo",
                "mileage": 3000,
                "transmission": "Automatic",
                "features": ["Carbon ceramic brakes", "Adaptive air suspension", "Lamborghini DNA"]
            },
            "images": [
                "https://www.lamborghini.com/sites/it-en/files/DAM/lamborghini/facelift_2019/models-gw/urus/2023/03_29/gate_models_s_02_m.jpg",
                "https://www.lamborghini.com/sites/it-en/files/DAM/lamborghini/facelift_2019/models-gw/urus/2023/03_29/gate_models_s_03_m.jpg",
                "https://www.lamborghini.com/sites/it-en/files/DAM/lamborghini/facelift_2019/models-gw/urus/2023/03_29/gate_models_s_04_m.jpg"
            ]
        },
        {
            "id": 15,
            "model": "Porsche Cayenne Turbo GT",
            "year": 2023,
            "price": 1700,
            "location": "Downtown Dubai",
            "description": "The most powerful Cayenne ever with track-ready performance.",
            "category": "SUV",
            "specs": {
                "engine": "4.0L V8 Twin-Turbo",
                "mileage": 3500,
                "transmission": "Automatic",
                "features": ["Active aerodynamics", "Porsche Ceramic Composite Brakes", "Sport Chrono package"]
            },
            "images": [
                "https://www.porsche.com/international/models/cayenne/cayenne-models/cayenne-turbo-gt/",
                "https://www.porsche.com/international/models/cayenne/cayenne-models/cayenne-turbo-gt/gallery/",
                "https://www.porsche.com/international/models/cayenne/cayenne-models/cayenne-turbo-gt/gallery/"
            ]
        }
    ]

    sports_cars = [
        {
            "id": 21,
            "model": "Lamborghini Aventador",
            "year": 2022,
            "price": 3000,
            "location": "Dubai Marina",
            "description": "The ultimate Italian supercar with breathtaking performance.",
            "category": "Sports",
            "specs": {
                "engine": "6.5L V12",
                "mileage": 2500,
                "transmission": "Automatic",
                "features": ["Carbon fiber body", "ALA aerodynamics", "Lamborghini Dinamica Veicolo"]
            },
            "images": [
                "https://www.lamborghini.com/sites/it-en/files/DAM/lamborghini/facelift_2019/models_gw/images-s/2023/03_29/gate_family_s_03_m.jpg",
                "https://www.lamborghini.com/sites/it-en/files/DAM/lamborghini/facelift_2019/models_gw/images-s/2023/03_29/gate_family_s_02_m.jpg",
                "https://www.lamborghini.com/sites/it-en/files/DAM/lamborghini/facelift_2019/models_gw/images-s/2023/03_29/gate_family_s_04_m.jpg"
            ]
        },
        {
            "id": 22,
            "model": "Ferrari 488 GTB",
            "year": 2021,
            "price": 2800,
            "location": "Palm Jumeirah",
            "description": "Mid-engine masterpiece with Ferrari's legendary performance.",
            "category": "Sports",
            "specs": {
                "engine": "3.9L V8 Twin-Turbo",
                "mileage": 3500,
                "transmission": "Automatic",
                "features": ["Side Slip Control", "Aerodynamic design", "Handcrafted interior"]
            },
            "images": [
                "https://www.ferrari.com/en-EN/auto/488-gtb",
                "https://www.ferrari.com/en-EN/auto/488-gtb/gallery",
                "https://www.ferrari.com/en-EN/auto/488-gtb/interior"
            ]
        },
        {
            "id": 23,
            "model": "McLaren 720S",
            "year": 2023,
            "price": 2700,
            "location": "Business Bay",
            "description": "British supercar with aerospace-inspired design and performance.",
            "category": "Sports",
            "specs": {
                "engine": "4.0L V8 Twin-Turbo",
                "mileage": 2000,
                "transmission": "Automatic",
                "features": ["Monocage II carbon fiber chassis", "Active Dynamics Panel", "Variable drift control"]
            },
            "images": [
                "https://cars.mclaren.com/content/dam/mclaren-automotive/models/720s/720s-coupe/overview/720s-coupe-overview-01.jpg",
                "https://cars.mclaren.com/content/dam/mclaren-automotive/models/720s/720s-coupe/gallery/720s-coupe-gallery-01.jpg",
                "https://cars.mclaren.com/content/dam/mclaren-automotive/models/720s/720s-coupe/gallery/720s-coupe-gallery-02.jpg"
            ]
        },
        {
            "id": 24,
            "model": "Porsche 911 Turbo S",
            "year": 2023,
            "price": 2200,
            "location": "Downtown Dubai",
            "description": "Iconic sports car with everyday usability and blistering performance.",
            "category": "Sports",
            "specs": {
                "engine": "3.8L Flat-6 Twin-Turbo",
                "mileage": 3000,
                "transmission": "Automatic",
                "features": ["Porsche Active Suspension", "Ceramic Composite Brakes", "Sport Chrono package"]
            },
            "images": [
                "https://www.porsche.com/international/models/911/911-turbo-models/911-turbo-s/",
                "https://www.porsche.com/international/models/911/911-turbo-models/911-turbo-s/gallery/",
                "https://www.porsche.com/international/models/911/911-turbo-models/911-turbo-s/gallery/"
            ]
        },
        {
            "id": 25,
            "model": "Aston Martin Vantage",
            "year": 2023,
            "price": 2000,
            "location": "JBR",
            "description": "British sports car with aggressive styling and thrilling performance.",
            "category": "Sports",
            "specs": {
                "engine": "4.0L V8 Twin-Turbo",
                "mileage": 2500,
                "transmission": "Automatic",
                "features": ["Sport+ mode", "Dynamic Torque Vectoring", "Bond-inspired design"]
            },
            "images": [
                "https://www.astonmartin.com/-/media/images/models/vantage/vantage-coupe/overview/vantage-coupe-overview-01.jpg",
                "https://www.astonmartin.com/-/media/images/models/vantage/vantage-coupe/gallery/vantage-coupe-gallery-01.jpg",
                "https://www.astonmartin.com/-/media/images/models/vantage/vantage-coupe/gallery/vantage-coupe-gallery-02.jpg"
            ]
        }
    ]

    sedan_cars = [
        {
            "id": 31,
            "model": "Mercedes-Benz S-Class",
            "year": 2023,
            "price": 1200,
            "location": "Business Bay",
            "description": "The benchmark for luxury sedans with cutting-edge technology.",
            "category": "Sedan",
            "specs": {
                "engine": "3.0L I6 Turbo",
                "mileage": 5000,
                "transmission": "Automatic",
                "features": ["MBUX Hyperscreen", "E-Active Body Control", "Energizing Comfort"]
            },
            "images": [
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/s-class/s-class-sedan/2023/overview/2023-S-CLASS-SEDAN-OV-HERO-DESKTOP.jpg",
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/s-class/s-class-sedan/2023/gallery/exterior/2023-S-CLASS-SEDAN-GAL-EXT-001-D.jpg",
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/s-class/s-class-sedan/2023/gallery/interior/2023-S-CLASS-SEDAN-GAL-INT-001-D.jpg"
            ]
        },
        {
            "id": 32,
            "model": "BMW 7 Series",
            "year": 2023,
            "price": 1100,
            "location": "Downtown Dubai",
            "description": "Luxury sedan with innovative features and dynamic performance.",
            "category": "Sedan",
            "specs": {
                "engine": "3.0L I6 Turbo",
                "mileage": 4500,
                "transmission": "Automatic",
                "features": ["BMW Live Cockpit Professional", "Executive Lounge", "Sky Lounge roof"]
            },
            "images": [
                "https://www.bmw.com/en/models/7-series/sedan/2022/overview.html",
                "https://www.bmw.com/en/models/7-series/sedan/2022/gallery.html",
                "https://www.bmw.com/en/models/7-series/sedan/2022/gallery.html"
            ]
        },
        {
            "id": 33,
            "model": "Audi A8 L",
            "year": 2023,
            "price": 1000,
            "location": "Dubai Hills",
            "description": "Progressive luxury with advanced technology and comfort.",
            "category": "Sedan",
            "specs": {
                "engine": "3.0L V6 Turbo",
                "mileage": 4000,
                "transmission": "Automatic",
                "features": ["Audi virtual cockpit", "Bang & Olufsen 3D sound", "Adaptive air suspension"]
            },
            "images": [
                "https://www.audi.com/en/models/a8/a8-l.html",
                "https://www.audi.com/en/models/a8/a8-l/gallery.html",
                "https://www.audi.com/en/models/a8/a8-l/gallery.html"
            ]
        },
        {
            "id": 34,
            "model": "Lexus LS 500",
            "year": 2023,
            "price": 950,
            "location": "JBR",
            "description": "Japanese luxury with impeccable craftsmanship and reliability.",
            "category": "Sedan",
            "specs": {
                "engine": "3.5L V6 Twin-Turbo",
                "mileage": 3500,
                "transmission": "Automatic",
                "features": ["Mark Levinson sound system", "Executive seating", "Lexus Safety System+"]
            },
            "images": [
                "https://www.lexus.com/models/LS",
                "https://www.lexus.com/models/LS/gallery",
                "https://www.lexus.com/models/LS/gallery"
            ]
        },
        {
            "id": 35,
            "model": "Genesis G90",
            "year": 2023,
            "price": 900,
            "location": "Palm Jumeirah",
            "description": "Korean luxury sedan with exceptional value and features.",
            "category": "Sedan",
            "specs": {
                "engine": "3.5L V6 Twin-Turbo",
                "mileage": 3000,
                "transmission": "Automatic",
                "features": ["Lexicon sound system", "Rear seat entertainment", "Smart Posture Care System"]
            },
            "images": [
                "https://www.genesis.com/us/en/models/g90.html",
                "https://www.genesis.com/us/en/models/g90/gallery.html",
                "https://www.genesis.com/us/en/models/g90/gallery.html"
            ]
        }
    ]

    convertible_cars = [
        {
            "id": 41,
            "model": "Ferrari Portofino M",
            "year": 2023,
            "price": 2600,
            "location": "Palm Jumeirah",
            "description": "Grand touring convertible with Ferrari performance and style.",
            "category": "Convertible",
            "specs": {
                "engine": "3.9L V8 Twin-Turbo",
                "mileage": 2000,
                "transmission": "Automatic",
                "features": ["Retractable hardtop", "Manettino dial", "Ferrari Dynamic Enhancer"]
            },
            "images": [
                "https://www.ferrari.com/en-EN/auto/portofino-m",
                "https://www.ferrari.com/en-EN/auto/portofino-m/gallery",
                "https://www.ferrari.com/en-EN/auto/portofino-m/gallery"
            ]
        },
        {
            "id": 42,
            "model": "Aston Martin DB11 Volante",
            "year": 2023,
            "price": 2300,
            "location": "Dubai Marina",
            "description": "British grand tourer convertible with elegant design.",
            "category": "Convertible",
            "specs": {
                "engine": "4.0L V8 Twin-Turbo",
                "mileage": 2500,
                "transmission": "Automatic",
                "features": ["Fabric roof", "Bond-inspired design", "Adaptive damping"]
            },
            "images": [
                "https://www.astonmartin.com/-/media/images/models/db11/db11-volante/overview/db11-volante-overview-01.jpg",
                "https://www.astonmartin.com/-/media/images/models/db11/db11-volante/gallery/db11-volante-gallery-01.jpg",
                "https://www.astonmartin.com/-/media/images/models/db11/db11-volante/gallery/db11-volante-gallery-02.jpg"
            ]
        },
        {
            "id": 43,
            "model": "Bentley Continental GT Convertible",
            "year": 2023,
            "price": 2000,
            "location": "Business Bay",
            "description": "Luxury convertible with exquisite craftsmanship and performance.",
            "category": "Convertible",
            "specs": {
                "engine": "4.0L V8",
                "mileage": 3000,
                "transmission": "Automatic",
                "features": ["Fabric roof", "Rotating display", "All-wheel drive"]
            },
            "images": [
                "https://www.bentleymotors.com/content/dam/bentley/Master/Models/continental-gt/continental-gt-convertible/continental-gt-convertible-models-overview/continental-gt-convertible-models-overview-1920x1080.jpg",
                "https://www.bentleymotors.com/content/dam/bentley/Master/Models/continental-gt/continental-gt-convertible/continental-gt-convertible-models-overview/continental-gt-convertible-models-overview-2-1920x1080.jpg",
                "https://www.bentleymotors.com/content/dam/bentley/Master/Models/continental-gt/continental-gt-convertible/continental-gt-convertible-models-overview/continental-gt-convertible-models-overview-3-1920x1080.jpg"
            ]
        },
        {
            "id": 44,
            "model": "Mercedes-AMG SL 63",
            "year": 2023,
            "price": 1800,
            "location": "Downtown Dubai",
            "description": "Reborn roadster with AMG performance and luxury.",
            "category": "Convertible",
            "specs": {
                "engine": "4.0L V8 Biturbo",
                "mileage": 2500,
                "transmission": "Automatic",
                "features": ["Fabric roof", "AMG Performance 4MATIC+", "MBUX infotainment"]
            },
            "images": [
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/amg/sl/2023/overview/2023-AMG-SL-OV-HERO-DESKTOP.jpg",
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/amg/sl/2023/gallery/exterior/2023-AMG-SL-GAL-EXT-001-D.jpg",
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/amg/sl/2023/gallery/interior/2023-AMG-SL-GAL-INT-001-D.jpg"
            ]
        },
        {
            "id": 45,
            "model": "Porsche 911 Cabriolet",
            "year": 2023,
            "price": 1700,
            "location": "JBR",
            "description": "Iconic sports car with open-top driving pleasure.",
            "category": "Convertible",
            "specs": {
                "engine": "3.0L Flat-6 Twin-Turbo",
                "mileage": 3000,
                "transmission": "Automatic",
                "features": ["Fabric roof", "Sport Chrono package", "Porsche Active Suspension"]
            },
            "images": [
                "https://www.porsche.com/international/models/911/911-carrera-models/911-carrera-cabriolet/",
                "https://www.porsche.com/international/models/911/911-carrera-models/911-carrera-cabriolet/gallery/",
                "https://www.porsche.com/international/models/911/911-carrera-models/911-carrera-cabriolet/gallery/"
            ]
        }
    ]

    electric_cars = [
        {
            "id": 51,
            "model": "Tesla Model S Plaid",
            "year": 2023,
            "price": 1500,
            "location": "Dubai Hills",
            "description": "The fastest production car with blistering acceleration and long range.",
            "category": "Electric",
            "specs": {
                "engine": "Tri-motor electric",
                "mileage": 4000,
                "transmission": "Single-speed",
                "features": ["1020 hp", "390 miles range", "0-60 mph in 1.99s"]
            },
            "images": [
                "https://www.tesla.com/models",
                "https://www.tesla.com/models/design",
                "https://www.tesla.com/models/design"
            ]
        },
        {
            "id": 52,
            "model": "Porsche Taycan Turbo S",
            "year": 2023,
            "price": 1800,
            "location": "Business Bay",
            "description": "Electric sports sedan with Porsche performance and handling.",
            "category": "Electric",
            "specs": {
                "engine": "Dual-motor electric",
                "mileage": 3500,
                "transmission": "2-speed",
                "features": ["750 hp", "280 miles range", "0-60 mph in 2.6s"]
            },
            "images": [
                "https://www.porsche.com/international/models/taycan/taycan-models/taycan-turbo-s/",
                "https://www.porsche.com/international/models/taycan/taycan-models/taycan-turbo-s/gallery/",
                "https://www.porsche.com/international/models/taycan/taycan-models/taycan-turbo-s/gallery/"
            ]
        },
        {
            "id": 53,
            "model": "Audi e-tron GT",
            "year": 2023,
            "price": 1600,
            "location": "Downtown Dubai",
            "description": "Electric grand tourer with quattro all-wheel drive and premium luxury.",
            "category": "Electric",
            "specs": {
                "engine": "Dual-motor electric",
                "mileage": 3000,
                "transmission": "Single-speed",
                "features": ["637 hp", "238 miles range", "0-60 mph in 3.1s"]
            },
            "images": [
                "https://www.audi.com/en/models/e-tron-gt/e-tron-gt.html",
                "https://www.audi.com/en/models/e-tron-gt/e-tron-gt/gallery.html",
                "https://www.audi.com/en/models/e-tron-gt/e-tron-gt/gallery.html"
            ]
        },
        {
            "id": 54,
            "model": "Mercedes-Benz EQS",
            "year": 2023,
            "price": 1400,
            "location": "Palm Jumeirah",
            "description": "Electric luxury sedan with MBUX Hyperscreen and exceptional range.",
            "category": "Electric",
            "specs": {
                "engine": "Dual-motor electric",
                "mileage": 3500,
                "transmission": "Single-speed",
                "features": ["516 hp", "350 miles range", "56-inch Hyperscreen"]
            },
            "images": [
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/eqs/sedan/2022/overview/2022-EQS-SEDAN-OV-HERO-DESKTOP.jpg",
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/eqs/sedan/2022/gallery/exterior/2022-EQS-SEDAN-GAL-EXT-001-D.jpg",
                "https://www.mbusa.com/content/dam/mb-nafta/us/myco/eqs/sedan/2022/gallery/interior/2022-EQS-SEDAN-GAL-INT-001-D.jpg"
            ]
        },
        {
            "id": 55,
            "model": "Lucid Air Dream Edition",
            "year": 2023,
            "price": 1900,
            "location": "Dubai Marina",
            "description": "Ultra-luxury electric sedan with industry-leading range and performance.",
            "category": "Electric",
            "specs": {
                "engine": "Dual-motor electric",
                "mileage": 2500,
                "transmission": "Single-speed",
                "features": ["1111 hp", "520 miles range", "0-60 mph in 2.5s"]
            },
            "images": [
                "https://www.lucidmotors.com/air",
                "https://www.lucidmotors.com/air/gallery",
                "https://www.lucidmotors.com/air/gallery"
            ]
        }
    ]

    # Filter cars based on category filters
    filtered_cars = []
    if luxury:
        filtered_cars.extend(luxury_cars)
    if suv:
        filtered_cars.extend(suv_cars)
    if sports:
        filtered_cars.extend(sports_cars)
    
    # If no category filter is selected, show all cars
    if not any([luxury, suv, sports]):
        filtered_cars.extend(luxury_cars)
        filtered_cars.extend(suv_cars)
        filtered_cars.extend(sports_cars)
        filtered_cars.extend(sedan_cars)
        filtered_cars.extend(convertible_cars)
        filtered_cars.extend(electric_cars)
    
    # Apply search filter if provided
    if search:
        search = search.lower()
        filtered_cars = [
            car for car in filtered_cars 
            if search in car['model'].lower() or search in car['description'].lower()
        ]
    
    if not filtered_cars:
        st.info("No cars found matching your criteria.")
        return
    
    # Group cars by category
    categorized_cars = {}
    for car in filtered_cars:
        category = car['category']
        if category not in categorized_cars:
            categorized_cars[category] = []
        categorized_cars[category].append(car)
    
    # Display cars by category
    for category, cars in categorized_cars.items():
        st.markdown(f"<h2 style='color: #4B0082; margin-top: 2rem;'>{category}</h2>", unsafe_allow_html=True)
        
        cols = st.columns(3)
        for idx, car in enumerate(cars):
            with cols[idx % 3]:
                # Display the first image as the main image
                st.image(
                    car['images'][0],
                    use_column_width=True,
                    caption=f"{car['model']} ({car['year']})"
                )
                
                st.markdown(f"""
                    <div style='margin-top: 10px;'>
                        <h3 style='color: #4B0082; margin: 0;'>{car['model']} ({car['year']})</h3>
                        <p style='color: #666; margin: 5px 0;'>{format_currency(car['price'])}/day</p>
                        <p style='color: #666; margin: 5px 0;'>{car['location']}</p>
                        <div style='color: #666; font-size: 0.9rem; margin: 5px 0;'>
                            <p>🏎 {car['specs']['engine']}</p>
                            <p>📊 {car['specs']['mileage']}km</p>
                            <p>⚙️ {car['specs']['transmission']}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button('View Details', key=f"details_{car['id']}"):
                    st.session_state.selected_car = car
                    st.session_state.current_page = 'car_details'
                    st.rerun()

def show_car_details(car):
    # Add a Go Back button
    col1, col2 = st.columns([1,7])
    with col1:
        if st.button('← Back'):
            st.session_state.current_page = 'browse_cars'
            st.session_state.selected_car = None
            st.rerun()
    
    st.markdown(f"<h1>{car['model']} ({car['year']})</h1>", unsafe_allow_html=True)
    
    # Image gallery with multiple images
    st.markdown("<div class='image-gallery'>", unsafe_allow_html=True)
    cols = st.columns(len(car['images']))
    for idx, img_url in enumerate(car['images']):
        with cols[idx]:
            st.image(
                img_url,
                caption=f"Image {idx+1}",
                use_container_width=True
            )
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Car details
    st.markdown(f"""
        <div style='background-color: white; padding: 1rem; border-radius: 10px; margin-top: 20px;'>
            <h3>Car Details</h3>
            <p><strong>Price:</strong> {format_currency(car['price'])}/day</p>
            <p><strong>Location:</strong> {car['location']}</p>
            <p><strong>Category:</strong> {car['category']}</p>
            <p><strong>Description:</strong> {car['description']}</p>
            
            <h4 style='margin-top: 20px;'>Specifications</h4>
            <p><strong>Engine:</strong> {car['specs']['engine']}</p>
            <p><strong>Mileage:</strong> {car['specs']['mileage']} km</p>
            <p><strong>Transmission:</strong> {car['specs']['transmission']}</p>
            
            <h4 style='margin-top: 20px;'>Features</h4>
            <ul>
                {''.join([f'<li>{feature}</li>' for feature in car['specs'].get('features', [])])}
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    # Booking button (only show if logged in)
    if st.session_state.logged_in:
        if st.button('Book Now', key=f"book_{car['id']}"):
            st.session_state.current_page = 'book_car'
            st.rerun()
    else:
        st.warning("Please login to book this car")
        if st.button('Login', key=f"login_from_{car['id']}"):
            st.session_state.current_page = 'login'
            st.rerun()

# ... (rest of your existing functions remain the same)

def main():
    # Create necessary folders
    create_folder_structure()
    
    # Setup or update database
    if not os.path.exists('car_rental.db'):
        setup_database()
    else:
        update_bookings_table()
    
    # Persistent login state initialization
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'welcome'
    
    # Verify login persistence
    if st.session_state.logged_in:
        try:
            conn = sqlite3.connect('car_rental.db')
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE email = ?', (st.session_state.user_email,))
            user = c.fetchone()
            conn.close()
            
            # If no user found, force logout
            if not user:
                st.session_state.logged_in = False
                st.session_state.user_email = None
                st.session_state.current_page = 'welcome'
        except Exception as e:
            print(f"Login verification error: {e}")
    
    # Sidebar for logged-in users
    if st.session_state.logged_in:
        with st.sidebar:
            # Get user info
            user_info = get_user_info(st.session_state.user_email)
            
            # Display profile section
            if user_info:
                if user_info[6]:  # profile picture
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 15px;">
                            <img src="data:image/jpeg;base64,{user_info[6]}" 
                                style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #4B0082;">
                        </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown(f"""
                    <div style="text-align: center; margin-bottom: 20px;">
                        <h3 style="margin: 5px 0;">{user_info[1]}</h3>
                        <p style="color: #666; margin: 0;">{user_info[7].replace('_', ' ').title()}</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style="text-align: center; margin-bottom: 20px;">
                        <h3 style="margin: 5px 0;">Welcome</h3>
                        <p style="color: #666; margin: 0;">{st.session_state.user_email}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("### My Account")
            
            # Get user role
            role = get_user_role(st.session_state.user_email)
            
            # Admin panel for admin users
            if role == 'admin':
                st.markdown("### Admin Functions")
                if st.button("🔧 Admin Panel"):
                    st.session_state.current_page = 'admin_panel'
                st.markdown("---")
            
            # Navigation buttons
            nav_items = [
                ("🚗 Browse Cars", 'browse_cars'),
                ("📝 My Listings", 'my_listings'),
                ("➕ List Your Car", 'list_your_car'),
                ("🚗 My Bookings", 'my_bookings'),
                ("📋 Bookings for My Cars", 'owner_bookings'),
                ("💰 Subscription Plans", 'subscription_plans'),
                ("🛡️ Insurance Claims", 'insurance_claims'),
                ("ℹ️ About Us", 'about_us')
            ]
            
            for label, page in nav_items:
                if st.button(label):
                    st.session_state.current_page = page
            
            # Notifications
            unread_count = get_unread_notifications_count(st.session_state.user_email)
            notification_label = f"🔔 Notifications ({unread_count})" if unread_count > 0 else "🔔 Notifications"
            if st.button(notification_label):
                st.session_state.current_page = 'notifications'
            
            st.markdown("---")
            
            # Logout button
            if st.button("👋 Logout"):
                st.session_state.logged_in = False
                st.session_state.user_email = None
                if 'persisted' in st.session_state:
                    del st.session_state.persisted
                if 'last_email' in st.session_state:
                    del st.session_state.last_email
                st.session_state.current_page = 'welcome'
                st.rerun()
    
    # Page routing
    if not st.session_state.logged_in and st.session_state.current_page not in ['welcome', 'login', 'signup', 'browse_cars', 'about_us']:
        st.session_state.current_page = 'welcome'
    
    # Page rendering
    page_handlers = {
        'welcome': welcome_page,
        'login': login_page,
        'signup': signup_page,
        'browse_cars': browse_cars_page,
        'admin_panel': admin_panel,
        'list_your_car': list_your_car_page,
        'my_listings': my_listings_page,
        'notifications': notifications_page,
        'my_bookings': my_bookings_page,
        'owner_bookings': owner_bookings_page,
        'car_details': lambda: show_car_details(st.session_state.selected_car) if hasattr(st.session_state, 'selected_car') and st.session_state.selected_car else browse_cars_page,
        'book_car': book_car_page,
        'subscription_plans': subscription_plans_page,
        'insurance_claims': insurance_claims_page,
        'about_us': about_us_page
    }
    
    # Authentication check for protected pages
    protected_pages = [
        'list_your_car', 'my_listings', 'notifications', 
        'my_bookings', 'owner_bookings', 'book_car', 'admin_panel',
        'subscription_plans', 'insurance_claims'
    ]
    
    # Render the current page
    current_page = st.session_state.current_page
    
    if current_page in protected_pages:
        if st.session_state.logged_in:
            # Special handling for admin panel
            if current_page == 'admin_panel' and get_user_role(st.session_state.user_email) != 'admin':
                st.error("Access denied. Admin privileges required.")
                st.session_state.current_page = 'browse_cars'
                browse_cars_page()
            else:
                page_handlers.get(current_page, welcome_page)()
        else:
            st.warning("Please log in to access this page")
            st.session_state.current_page = 'login'
            login_page()
    else:
        page_handlers.get(current_page, welcome_page)()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        print(f"Error details: {str(e)}")
