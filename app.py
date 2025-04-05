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
st.set_page_config(page_title="Luxury Car Rentals", layout="wide")

st.markdown("""
    <style>
        /* Root Variables for Theming */
        :root {
            --primary-color: #4B0082;
            --secondary-color: #6A0DAD;
            --background-color: #F4F4F8;
            --text-color: #333;
        }

        /* Global Styles */
        .stApp {
            background-color: var(--background-color);
            font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
        }

        /* Button Styling */
        .stButton>button {
            width: 100%;
            border-radius: 20px;
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
        
        /* Layout */
        .css-1d391kg {
            padding: 2rem 1rem;
        }
        
        /* Input Styling */
        input[type="text"], input[type="password"] {
            border-radius: 20px;
            padding: 10px 15px;
            border: 2px solid var(--primary-color);
            transition: all 0.3s ease;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: var(--secondary-color);
            box-shadow: 0 0 10px rgba(106,13,173,0.2);
        }
        
        /* Headings */
        h1 {
            color: var(--primary-color);
            text-align: center;
            padding: 1rem 0;
            font-weight: 700;
            letter-spacing: -1px;
        }
        
        /* Card Styling */
        .car-card {
            background-color: white;
            border-radius: 15px;
            padding: 1rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            margin: 1rem 0;
            transition: all 0.3s ease;
            border: 1px solid #e1e1e8;
        }
        
        .car-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.15);
        }
        
        /* Message Styling */
        .success-message {
            background-color: #E8F5E9;
            color: #2E7D32;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            border-left: 4px solid #2E7D32;
        }
        
        .error-message {
            background-color: #FFEBEE;
            color: #C62828;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            border-left: 4px solid #C62828;
        }
        
        /* Status Badge */
        .status-badge {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: inline-block;
        }
        
        .status-badge.pending {
            background-color: #FFC107;
            color: #333;
        }
        
        .status-badge.approved {
            background-color: #28a745;
            color: white;
        }
        
        .status-badge.rejected {
            background-color: #dc3545;
            color: white;
        }
        
        /* Admin Review Card */
        .admin-review-card {
            background-color: white;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            margin: 1.5rem 0;
            border: 1px solid #e1e1e8;
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
            border-radius: 10px;
            transition: transform 0.3s ease;
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }
        
        .image-gallery img:hover {
            transform: scale(1.05);
        }
        
        /* Profile Picture */
        .profile-picture {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid var(--primary-color);
        }
        
        /* Subscription Cards */
        .subscription-card {
            background-color: white;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            margin: 1rem 0;
            height: 100%;
            display: flex;
            flex-direction: column;
            transition: all 0.3s ease;
        }
        
        .subscription-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.2);
        }
        
        .subscription-card.premium {
            border-top: 5px solid #4B0082;
        }
        
        .subscription-card.elite {
            border-top: 5px solid #FFD700;
        }
        
        .subscription-card h3 {
            text-align: center;
            margin-bottom: 1rem;
            color: var(--primary-color);
        }
        
        .subscription-price {
            font-size: 1.8rem;
            text-align: center;
            margin: 1rem 0;
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .subscription-features {
            flex-grow: 1;
        }
        
        .subscription-features ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .subscription-features li {
            padding: 0.5rem 0;
            border-bottom: 1px solid #eee;
        }
        
        .subscription-features li:before {
            content: "✓";
            margin-right: 0.5rem;
            color: #28a745;
        }
        
        .insurance-claim-card {
            background-color: white;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            margin: 1.5rem 0;
            border: 1px solid #e1e1e8;
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

# Database setup - Modified for persistent storage
def setup_database():
    try:
        # Check if database exists first, don't remove it
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
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(full_name, email, phone, password, profile_picture=None, role='user'):
    """Create a new user account with optional profile picture"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Check if user already exists
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        if c.fetchone():
            return False
            
        # Create new user
        c.execute(
            'INSERT INTO users (full_name, email, phone, password, profile_picture, role) VALUES (?, ?, ?, ?, ?, ?)',
            (full_name, email, phone, hash_password(password), profile_picture, role)
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

def get_user_info(email):
    """Get user's full information"""
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
    """Update user's subscription"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Get current date and calculate expiry
        start_date = datetime.now().date()
        end_date = start_date + relativedelta(months=months)
        
        # Update user subscription
        c.execute('''
            UPDATE users 
            SET subscription_type = ?, subscription_expiry = ?
            WHERE email = ?
        ''', (plan_type, end_date.isoformat(), email))
        
        # Calculate amount based on plan and duration
        amount = 0
        if plan_type == 'premium_renter':
            amount = 20 * months
        elif plan_type == 'elite_renter':
            amount = 50 * months
        elif plan_type == 'premium_host':
            amount = 50 * months
        elif plan_type == 'elite_host':
            amount = 100 * months
        
        # Add to subscription history
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
        
        # Create notification
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
    """Get subscription benefits based on plan type"""
    benefits = {
        # Renter plans
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
        
        # Host plans
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
    logo_url = "https://raw.githubusercontent.com/jamers188/P2P-CAR/main/kipride.png"  # Update with the raw URL
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
                st.rerun()  # Use rerun() instead of experimental_rerun()
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
                
                st.rerun()  # Use rerun() instead of experimental_rerun()
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


def subscription_plans_page():
    st.markdown("<h1>Subscription Plans</h1>", unsafe_allow_html=True)
    
    if st.button('← Back to Browse', key='subscription_back'):
        st.session_state.current_page = 'browse_cars'
    
    # Get user info
    user_info = get_user_info(st.session_state.user_email)
    current_plan = user_info[7] if user_info else 'free_renter'
    
    # Check if user is primarily a renter or host based on history
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Count bookings vs listings
    c.execute('SELECT COUNT(*) FROM bookings WHERE user_email = ?', (st.session_state.user_email,))
    booking_count = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM car_listings WHERE owner_email = ?', (st.session_state.user_email,))
    listing_count = c.fetchone()[0]
    
    conn.close()
    
    # Determine if user is primarily a renter or host
    user_type = 'renter' if booking_count >= listing_count else 'host'
    
    # Subscription plan tabs
    if user_type == 'renter':
        st.markdown("<h2>Plans for Renters</h2>", unsafe_allow_html=True)
        renter_tab1, renter_tab2, renter_tab3 = st.tabs(["Free Plan", "Premium Plan ($20/month)", "Elite VIP Plan ($50/month)"])
        
        with renter_tab1:
            st.markdown("""
                <div class="subscription-card">
                    <h3>Free Plan</h3>
                    <div class="subscription-price">$0</div>
                    <div class="subscription-features">
                        <ul>
                            <li>Standard service fees apply</li>
                            <li>No booking priority</li>
                            <li>No special discounts on rentals</li>
                            <li>Cancellations may have penalties</li>
                            <li>No roadside assistance</li>
                            <li>Standard customer support response time</li>
                            <li>Access to general vehicle listings only</li>
                            <li>No damage waiver protection</li>
                        </ul>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if current_plan != 'free_renter':
                if st.button("Downgrade to Free", key="downgrade_free_renter"):
                    if update_user_subscription(st.session_state.user_email, 'free_renter'):
                        st.success("Successfully downgraded to Free plan!")
                        st.rerun()
        
        with renter_tab2:
            st.markdown("""
                <div class="subscription-card premium">
                    <h3>Premium Plan</h3>
                    <div class="subscription-price">$20/month</div>
                    <div class="subscription-features">
                        <ul>
                            <li>Reduced service fees</li>
                            <li>Priority booking access before free users</li>
                            <li>Discounts of up to 10% on select cars</li>
                            <li>Limited free cancellations</li>
                            <li>Roadside assistance included</li>
                            <li>Faster customer support response</li>
                            <li>Access to exclusive luxury vehicles</li>
                            <li>Partial damage waiver protection</li>
                        </ul>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if current_plan != 'premium_renter':
                duration = st.selectbox("Subscription Duration", [1, 3, 6, 12], key="premium_renter_duration")
                if st.button(f"Subscribe for {duration} {'month' if duration == 1 else 'months'}", key="subscribe_premium_renter"):
                    if update_user_subscription(st.session_state.user_email, 'premium_renter', duration):
                        st.success(f"Successfully subscribed to Premium plan for {duration} {'month' if duration == 1 else 'months'}!")
                        st.rerun()
        
        with renter_tab3:
            st.markdown("""
                <div class="subscription-card elite">
                    <h3>Elite VIP Plan</h3>
                    <div class="subscription-price">$50/month</div>
                    <div class="subscription-features">
                        <ul>
                            <li>Lowest service fees on rentals</li>
                            <li>First priority booking access</li>
                            <li>Up to 20% discount on rentals</li>
                            <li>Unlimited free cancellations</li>
                            <li>Premium roadside assistance</li>
                            <li>24/7 priority customer support</li>
                            <li>Access to luxury, exotic, and chauffeur-driven cars</li>
                            <li>Full damage waiver protection</li>
                            <li>Free vehicle upgrades (if available)</li>
                            <li>VIP concierge service with a personal booking assistant</li>
                        </ul>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if current_plan != 'elite_renter':
                duration = st.selectbox("Subscription Duration", [1, 3, 6, 12], key="elite_renter_duration")
                if st.button(f"Subscribe for {duration} {'month' if duration == 1 else 'months'}", key="subscribe_elite_renter"):
                    if update_user_subscription(st.session_state.user_email, 'elite_renter', duration):
                        st.success(f"Successfully subscribed to Elite VIP plan for {duration} {'month' if duration == 1 else 'months'}!")
                        st.rerun()
    else:
        st.markdown("<h2>Plans for Hosts</h2>", unsafe_allow_html=True)
        host_tab1, host_tab2, host_tab3 = st.tabs(["Free Plan", "Premium Plan ($50/month)", "Elite Plan ($100/month)"])
        
        with host_tab1:
            st.markdown("""
                <div class="subscription-card">
                    <h3>Free Plan</h3>
                    <div class="subscription-price">$0</div>
                    <div class="subscription-features">
                        <ul>
                            <li>Standard listing visibility</li>
                            <li>15% platform commission per booking</li>
                            <li>No dynamic pricing tools</li>
                            <li>Basic damage protection</li>
                            <li>Basic fraud prevention measures</li>
                            <li>Standard payout processing time</li>
                            <li>Standard customer support</li>
                            <li>No special marketing benefits</li>
                        </ul>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if current_plan != 'free_host':
                if st.button("Downgrade to Free", key="downgrade_free_host"):
                    if update_user_subscription(st.session_state.user_email, 'free_host'):
                        st.success("Successfully downgraded to Free plan!")
                        st.rerun()
        
        with host_tab2:
            st.markdown("""
                <div class="subscription-card premium">
                    <h3>Premium Plan</h3>
                    <div class="subscription-price">$50/month</div>
                    <div class="subscription-features">
                        <ul>
                            <li>Boosted visibility for listings</li>
                            <li>Lower platform commission (10%)</li>
                            <li>Dynamic pricing tools for optimizing earnings</li>
                            <li>Extra damage protection</li>
                            <li>Enhanced renter verification for fraud prevention</li>
                            <li>Faster payouts after each booking</li>
                            <li>Priority customer support</li>
                            <li>Eligible for promotional marketing</li>
                        </ul>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if current_plan != 'premium_host':
                duration = st.selectbox("Subscription Duration", [1, 3, 6, 12], key="premium_host_duration")
                if st.button(f"Subscribe for {duration} {'month' if duration == 1 else 'months'}", key="subscribe_premium_host"):
                    if update_user_subscription(st.session_state.user_email, 'premium_host', duration):
                        st.success(f"Successfully subscribed to Premium plan for {duration} {'month' if duration == 1 else 'months'}!")
                        st.rerun()
        
        with host_tab3:
            st.markdown("""
                <div class="subscription-card elite">
                    <h3>Elite Plan</h3>
                    <div class="subscription-price">$100/month</div>
                    <div class="subscription-features">
                        <ul>
                            <li>Top placement for listings</li>
                            <li>Lowest platform commission (5%) or zero commission up to a specific limit</li>
                            <li>Advanced AI-driven pricing optimization</li>
                            <li>Full damage protection</li>
                            <li>AI-based risk assessment for fraud prevention</li>
                            <li>Instant same-day payouts</li>
                            <li>24/7 dedicated support manager</li>
                            <li>Featured placement in app promotions and campaigns</li>
                        </ul>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if current_plan != 'elite_host':
                duration = st.selectbox("Subscription Duration", [1, 3, 6, 12], key="elite_host_duration")
                if st.button(f"Subscribe for {duration} {'month' if duration == 1 else 'months'}", key="subscribe_elite_host"):
                    if update_user_subscription(st.session_state.user_email, 'elite_host', duration):
                        st.success(f"Successfully subscribed to Elite plan for {duration} {'month' if duration == 1 else 'months'}!")
                        st.rerun()

def insurance_claims_page():
    st.markdown("<h1>Insurance Claims</h1>", unsafe_allow_html=True)
    
    if st.button('← Back to My Bookings', key='claims_back'):
        st.session_state.current_page = 'my_bookings'
    
    # Show two tabs: Submit New Claim and View Existing Claims
    tab1, tab2 = st.tabs(["Submit New Claim", "My Claims"])
    
    with tab1:
        st.markdown("<h3>Submit New Insurance Claim</h3>", unsafe_allow_html=True)
        
        # Get user's bookings that have insurance
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        c.execute('''
            SELECT b.id, cl.model, cl.year, b.pickup_date, b.return_date
            FROM bookings b
            JOIN car_listings cl ON b.car_id = cl.id
            WHERE b.user_email = ? AND b.insurance = TRUE
            ORDER BY b.created_at DESC
        ''', (st.session_state.user_email,))
        insured_bookings = c.fetchall()
        conn.close()
        
        if not insured_bookings:
            st.warning("You don't have any bookings with insurance coverage. Insurance must be added at booking time.")
            return
        
        # Create claim form
        with st.form("claim_form"):
            # Choose booking
            booking_options = [f"#{b[0]} - {b[1]} ({b[2]}) - {b[3]} to {b[4]}" for b in insured_bookings]
            selected_booking = st.selectbox("Select Insured Booking", booking_options)
            booking_id = int(selected_booking.split('#')[1].split(' ')[0])
            
            # Incident details
            incident_date = st.date_input("Incident Date")
            damage_type = st.selectbox("Type of Damage", get_damage_types())
            description = st.text_area("Describe the Incident", 
                                      placeholder="Please provide detailed information about what happened...")
            claim_amount = st.number_input("Claim Amount (AED)", min_value=0.0, step=100.0)
            
            # Evidence upload
            st.markdown("### Upload Evidence")
            evidence_files = st.file_uploader("Upload photos of damage (max 5 files)", 
                                             type=["jpg", "jpeg", "png"], accept_multiple_files=True)
            
            if evidence_files:
                if len(evidence_files) > 5:
                    st.warning("Maximum 5 files allowed. Only the first 5 will be processed.")
                    evidence_files = evidence_files[:5]
                
                # Preview images
                cols = st.columns(len(evidence_files))
                for i, file in enumerate(cols):
                    with cols[i]:
                        st.image(evidence_files[i], use_column_width=True)
            
            submit = st.form_submit_button("Submit Claim")
            
            if submit:
                if not all([incident_date, damage_type, description, claim_amount > 0]):
                    st.error("Please fill in all required fields")
                else:
                    # Process images if provided
                    evidence_images_data = None
                    if evidence_files:
                        evidence_images = []
                        for file in evidence_files:
                            img_data = save_uploaded_image(file)
                            if img_data:
                                evidence_images.append(img_data)
                        
                        if evidence_images:
                            evidence_images_data = json.dumps(evidence_images)
                    
                    # Create claim
                    success, message = create_insurance_claim(
                        booking_id, 
                        st.session_state.user_email,
                        incident_date.isoformat(),
                        description,
                        damage_type,
                        claim_amount,
                        evidence_images_data
                    )
                    
                    if success:
                        st.success(message)
                        st.experimental_rerun()
                    else:
                        st.error(message)
    with tab2:
        st.markdown("<h3>My Insurance Claims</h3>", unsafe_allow_html=True)
        
        # Get user's claims
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        c.execute('''
            SELECT ic.*, b.car_id, cl.model, cl.year  
            FROM insurance_claims ic
            JOIN bookings b ON ic.booking_id = b.id
            JOIN car_listings cl ON b.car_id = cl.id
            WHERE ic.user_email = ?
            ORDER BY ic.created_at DESC
        ''', (st.session_state.user_email,))
        claims = c.fetchall()
        conn.close()
        
        if not claims:
            st.info("You haven't submitted any insurance claims yet.")
            return
        
        # Display claims
        for claim in claims:
            with st.container():
                claim_id = claim[0]
                booking_id = claim[1]
                incident_date = claim[3]
                damage_type = claim[6]
                claim_amount = claim[7]
                status = claim[9]
                admin_notes = claim[10]
                car_model = claim[13]
                car_year = claim[14]
                
                # Status color
                status_colors = {
                    'pending': '#FFC107',
                    'approved': '#28a745',
                    'rejected': '#dc3545',
                    'paid': '#17a2b8'
                }
                status_color = status_colors.get(status.lower(), '#6c757d')
                
                st.markdown(f"""
                    <div class="insurance-claim-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3>Claim #{claim_id} - {car_model} ({car_year})</h3>
                            <span style="background-color: {status_color}; color: white; padding: 5px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: bold;">
                                {status.upper()}
                            </span>
                        </div>
                        <p><strong>Booking ID:</strong> #{booking_id}</p>
                        <p><strong>Incident Date:</strong> {incident_date}</p>
                        <p><strong>Damage Type:</strong> {damage_type}</p>
                        <p><strong>Claim Amount:</strong> {format_currency(claim_amount)}</p>
                """, unsafe_allow_html=True)
                
                # Show evidence images if available
                if claim[8]:  # evidence_images field
                    try:
                        evidence_images = json.loads(claim[8])
                        if evidence_images:
                            st.markdown("<h4>Evidence Photos</h4>", unsafe_allow_html=True)
                            cols = st.columns(min(len(evidence_images), 3))
                            for i, img_data in enumerate(evidence_images):
                                with cols[i % 3]:
                                    st.image(f"data:image/jpeg;base64,{img_data}", use_column_width=True)
                    except json.JSONDecodeError:
                        st.error("Error loading evidence images")
                
                # Show admin notes if available
                if admin_notes:
                    st.markdown(f"""
                        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; margin-top: 1rem;">
                            <h4>Admin Notes</h4>
                            <p>{admin_notes}</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
   


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
                    use_container_width=True
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
    
    # Booking button (only show if logged in)
    if st.session_state.logged_in:
        if st.button('Book Now'):
            st.session_state.current_page = 'book_car'
            st.rerun()
    else:
        st.warning("Please login to book this car")
        if st.button('Login'):
            st.session_state.current_page = 'login'
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
    
    # Get user subscription info for possible discounts
    user_info = get_user_info(st.session_state.user_email)
    subscription_type = user_info[7] if user_info else 'free_renter'
    
    st.markdown(f"<h1>Book {car['model']} ({car['year']})</h1>", unsafe_allow_html=True)
    
    # Define service prices
    service_prices = {
        'insurance': 50,  # per day
        'driver': 100,    # per day
        'delivery': 200,  # flat rate
        'vip_service': 300  # flat rate
    }
    
    # Apply subscription discounts if applicable
    discount_percentage = 0
    if subscription_type == 'premium_renter':
        discount_percentage = 10
    elif subscription_type == 'elite_renter':
        discount_percentage = 20
    
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
        insurance_price = service_prices['insurance'] * rental_days if insurance else 0
        driver_price = service_prices['driver'] * rental_days if driver else 0
        delivery_price = service_prices['delivery'] if delivery else 0
        vip_service_price = service_prices['vip_service'] if vip_service else 0
        
        subtotal = base_price + insurance_price + driver_price + delivery_price + vip_service_price
        
        # Apply subscription discount if applicable
        discount_amount = 0
        if discount_percentage > 0:
            discount_amount = (subtotal * discount_percentage / 100)
            total_price = subtotal - discount_amount
        else:
            total_price = subtotal
        
        # Display price breakdown
        st.markdown("### Price Breakdown")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Base Rental ({rental_days} days): {format_currency(base_price)}")
            if insurance:
                st.write(f"Insurance: {format_currency(insurance_price)}")
            if driver:
                st.write(f"Driver: {format_currency(driver_price)}")
        with col2:
            if delivery:
                st.write(f"Delivery: {format_currency(delivery_price)}")
            if vip_service:
                st.write(f"VIP Service: {format_currency(vip_service_price)}")
            
        # Show subscription discount if applicable
        if discount_percentage > 0:
            st.markdown(f"""
                <div style="background-color: #E8F5E9; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <p><strong>{subscription_type.replace('_', ' ').title()} Discount ({discount_percentage}%):</strong> 
                    {format_currency(discount_amount)}</p>
                </div>
            """, unsafe_allow_html=True)
        
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
                    insurance_price, driver_price, delivery_price, vip_service_price)
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
                    insurance_price,
                    driver_price,
                    delivery_price,
                    vip_service_price
                ))
                
                conn.commit()
                
                # Create notification for user
                create_notification(
                    st.session_state.user_email,
                    f"Booking confirmed for {car['model']} from {pickup_date} to {return_date}",
                    'booking_confirmed'
                )
                
                # Create notification for car owner
                create_notification(
                    car['owner_email'],
                    f"New booking request for your {car['model']} from {pickup_date} to {return_date}",
                    'new_booking'
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
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button('← Back to Browse', key='bookings_back'):
            st.session_state.current_page = 'browse_cars'
    with col3:
        if st.button('Submit Insurance Claim', key='submit_claim'):
            st.session_state.current_page = 'insurance_claims'
    
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
    
    # Clear bookings functionality
    with col2:
        # Only allow clearing if there are non-pending bookings
        completed_bookings = [b for b in bookings if b[11] != 'pending']
        if completed_bookings:
            if st.button('🗑️ Clear Completed'):
                try:
                    # Delete completed bookings
                    c.execute('''
                        DELETE FROM bookings 
                        WHERE user_email = ? AND booking_status != 'pending'
                    ''', (st.session_state.user_email,))
                    conn.commit()
                    st.success("Completed bookings cleared!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error clearing bookings: {e}")
    
    if not bookings:
        st.info("You haven't made any bookings yet.")
        conn.close()
        return
    
    # Get user's subscription type
    user_info = get_user_info(st.session_state.user_email)
    subscription_type = user_info[7] if user_info else 'free_renter'
    
    for booking in bookings:
        # Unpack booking details
        (booking_id, user_email, car_id, pickup_date, return_date, location, 
         total_price, insurance, driver, delivery, vip_service, 
         booking_status, created_at, 
         insurance_price, driver_price, delivery_price, vip_service_price,
         model, year, owner_email, image_data) = booking
        
        # Create a card-like container
        with st.container():
            # Display car image if available
            if image_data:
                st.image(
                    f"data:image/jpeg;base64,{image_data}", 
                    use_container_width=True, 
                    caption=f"{model} ({year})"
                )
            
            # Car details
            st.subheader(f"{model} ({year})")
            
            # Status display with color coding
            status_colors = {
                'pending': 'black',
                'confirmed': 'green',
                'rejected': 'red'
            }
            status_color = status_colors.get(booking_status.lower(), 'blue')
            st.markdown(f"### Booking Status: <span style='color: {status_color};'>{booking_status.upper()}</span>", unsafe_allow_html=True)
            
            # Booking details
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Booking ID:** #{booking_id}")
                st.write(f"**Pickup Date:** {pickup_date}")
                st.write(f"**Location:** {location}")
                st.write(f"**Owner Email:** {owner_email}")
            
            with col2:
                st.write(f"**Return Date:** {return_date}")
                st.write(f"**Total Price:** {format_currency(total_price)}")
                # Show subscription benefits if applicable
                if subscription_type in ['premium_renter', 'elite_renter']:
                    benefits = get_subscription_benefits(subscription_type)
                    st.markdown(f"""
                        <div style="background-color: #E0F7FA; padding: 5px 10px; border-radius: 5px; margin-top: 5px;">
                            <p><strong>{subscription_type.replace('_', ' ').title()} Benefits:</strong>
                            <br>• {benefits['damage_waiver']}
                            <br>• {benefits['cancellations']}
                            <br>• {benefits['roadside_assistance']}</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            # Price Breakdown
            st.subheader("Price Breakdown")
            col1, col2 = st.columns(2)
            with col1:
                # Calculate base rental by subtracting additional services
                base_price = total_price - (insurance_price + driver_price + delivery_price + vip_service_price)
                st.write(f"Base Rental: {format_currency(base_price)}")
                
                if insurance:
                    st.write(f"Insurance: {format_currency(insurance_price)}")
                if driver:
                    st.write(f"Driver: {format_currency(driver_price)}")
            with col2:
                if delivery:
                    st.write(f"Delivery: {format_currency(delivery_price)}")
                if vip_service:
                    st.write(f"VIP Service: {format_currency(vip_service_price)}")
            
            # Additional Services
            st.subheader("Additional Services")
            services = []
            if insurance:
                services.append(("Insurance", insurance_price))
            if driver:
                services.append(("Driver", driver_price))
            if delivery:
                services.append(("Delivery", delivery_price))
            if vip_service:
                services.append(("VIP Service", vip_service_price))
            
            if services:
                for service, price in services:
                    st.info(f"{service}: {format_currency(price)}")
            else:
                st.info("No additional services selected")
                
            # Insurance claim button (only show for confirmed bookings with insurance)
            if booking_status.lower() == 'confirmed' and insurance:
                # Check if a claim already exists
                c.execute('SELECT id FROM insurance_claims WHERE booking_id = ?', (booking_id,))
                existing_claim = c.fetchone()
                
                if not existing_claim:
                    if st.button(f"File Insurance Claim", key=f"claim_{booking_id}"):
                        st.session_state.selected_booking_for_claim = booking_id
                        st.session_state.current_page = 'insurance_claims'
                        st.rerun()
                else:
                    st.info(f"You've already submitted a claim for this booking. View it in the Insurance Claims section.")
            
            st.markdown("---")
    
    conn.close()

def owner_bookings_page():
    st.markdown("<h1>Bookings for My Cars</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button('← Back to Browse', key='owner_bookings_back'):
            st.session_state.current_page = 'browse_cars'
    
    # Connect to database
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Get user's subscription type
    user_info = get_user_info(st.session_state.user_email)
    subscription_type = user_info[7] if user_info else 'free_host'
    subscription_benefits = get_subscription_benefits(subscription_type)
    
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
    
    # Clear bookings functionality
    with col2:
        # Only allow clearing if there are non-pending bookings
        completed_bookings = [b for b in bookings if b[11] != 'pending']
        if completed_bookings:
            if st.button('🗑️ Clear Completed'):
                try:
                    # Delete completed bookings
                    c.execute('''
                        DELETE FROM bookings 
                        WHERE car_id IN (
                            SELECT id FROM car_listings 
                            WHERE owner_email = ?
                        ) AND booking_status != 'pending'
                    ''', (st.session_state.user_email,))
                    conn.commit()
                    st.success("Completed bookings cleared!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error clearing bookings: {e}")
    
    if not bookings:
        st.info("No bookings for your cars.")
        conn.close()
        return
    
    # Display subscription benefits for hosts
    if subscription_type != 'free_host':
        st.markdown(f"""
            <div style="background-color: #E0F7FA; padding: 10px 15px; border-radius: 8px; margin: 15px 0;">
                <h3>Your {subscription_type.replace('_', ' ').title()} Benefits</h3>
                <p><strong>Commission:</strong> {subscription_benefits['commission']}</p>
                <p><strong>Damage Protection:</strong> {subscription_benefits['damage_protection']}</p>
                <p><strong>Payout Speed:</strong> {subscription_benefits['payout_speed']}</p>
            </div>
        """, unsafe_allow_html=True)
    
    for booking in bookings:
        # Unpack booking details
        (booking_id, renter_email, car_id, pickup_date, return_date, location, 
         total_price, insurance, driver, delivery, vip_service, 
         booking_status, created_at, 
         insurance_price, driver_price, delivery_price, vip_service_price,
         model, year, booking_renter_email, image_data) = booking
        
        # Create a container for each booking
        with st.container():
            # Display car image if available
            if image_data:
                st.image(
                    f"data:image/jpeg;base64,{image_data}", 
                    use_container_width=True, 
                    caption=f"{model} ({year})"
                )
            
            # Car and Booking Details
            st.subheader(f"{model} ({year})")
            
            # Status display with color coding
            status_colors = {
                'pending': 'yellow',
                'confirmed': 'green',
                'rejected': 'red'
            }
            status_color = status_colors.get(booking_status.lower(), 'blue')
            st.markdown(f"### Booking Status: <span style='color: {status_color};'>{booking_status.upper()}</span>", unsafe_allow_html=True)
            
            # Booking details
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Booking ID:** #{booking_id}")
                st.write(f"**Renter:** {renter_email}")
                st.write(f"**Pickup Date:** {pickup_date}")
                st.write(f"**Location:** {location}")
            
            with col2:
                st.write(f"**Return Date:** {return_date}")
                
                # Calculate commission based on subscription
                commission_rate = 0.15  # default 15%
                if subscription_type == 'premium_host':
                    commission_rate = 0.10
                elif subscription_type == 'elite_host':
                    commission_rate = 0.05
                
                commission = total_price * commission_rate
                host_earnings = total_price - commission
                
                st.write(f"**Total Booking Price:** {format_currency(total_price)}")
                st.write(f"**Platform Fee ({int(commission_rate*100)}%):** {format_currency(commission)}")
                st.markdown(f"**<span style='color: green;'>Your Earnings:</span> {format_currency(host_earnings)}**", unsafe_allow_html=True)
            
            # Additional Services
            st.subheader("Included Services")
            services = []
            if insurance:
                services.append(("Insurance", insurance_price))
            if driver:
                services.append(("Driver", driver_price))
            if delivery:
                services.append(("Delivery", delivery_price))
            if vip_service:
                services.append(("VIP Service", vip_service_price))
            
            if services:
                for service, price in services:
                    st.info(f"{service}: {format_currency(price)}")
            else:
                st.info("No additional services included")
            
            # Approval buttons (only for pending bookings)
            if booking_status.lower() == 'pending':
                col1, col2 = st.columns(2)
                with col1:
                    approve = st.button("Approve Booking", key=f"approve_{booking_id}")
                with col2:
                    reject = st.button("Reject Booking", key=f"reject_{booking_id}")
                
                if approve or reject:
                    new_status = 'confirmed' if approve else 'rejected'
                    
                    # Update booking status
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
                    st.success(f"Booking {new_status}")
                    st.experimental_rerun()
            
            # Display payout info for confirmed bookings
            if booking_status.lower() == 'confirmed':
                # Calculate payout date based on subscription
                booking_date = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                
                if subscription_type == 'elite_host':
                    payout_date = booking_date.date()
                    payout_msg = "Same-day payout"
                elif subscription_type == 'premium_host':
                    payout_date = booking_date.date() + timedelta(days=1)
                    payout_msg = "Next-day payout"
                else:
                    payout_date = booking_date.date() + timedelta(days=3)
                    payout_msg = "Standard payout (3 days)"
                
                st.markdown(f"""
                    <div style="background-color: #F0FFF0; padding: 10px; border-radius: 5px; margin-top: 10px;">
                        <p><strong>Payout Status:</strong> {payout_msg}</p>
                        <p><strong>Payout Date:</strong> {payout_date.strftime('%d %b %Y')}</p>
                        <p><strong>Amount:</strong> {format_currency(host_earnings)}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
    
    conn.close()


def admin_panel():
    st.markdown("<h1>Admin Panel</h1>", unsafe_allow_html=True)
    
    if st.button('← Back to Browse', key='admin_back'):
        st.session_state.current_page = 'browse_cars'
    
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Pending Listings", "Approved Listings", "Rejected Listings", "Insurance Claims"])
    
    with tab1:
        show_pending_listings()
    with tab2:
        show_approved_listings()
    with tab3:
        show_rejected_listings()
    with tab4:
        show_admin_insurance_claims()

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
                                use_container_width=True
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
                                use_container_width=True
                            )
                    st.markdown("</div>", unsafe_allow_html=True)
    
    conn.close()

def show_approved_listings():
    st.subheader("Approved Listings")
    show_listings_by_status('approved')

def show_rejected_listings():
    st.subheader("Rejected Listings")
    show_listings_by_status('rejected')

def show_admin_insurance_claims():
    st.subheader("Insurance Claims Management")
    
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Get all insurance claims
    c.execute('''
        SELECT ic.*, u.full_name, b.car_id, cl.model, cl.year
        FROM insurance_claims ic
        JOIN users u ON ic.user_email = u.email
        JOIN bookings b ON ic.booking_id = b.id
        JOIN car_listings cl ON b.car_id = cl.id
        ORDER BY ic.claim_status = 'pending' DESC, ic.created_at DESC
    ''')
    
    claims = c.fetchall()
    
    if not claims:
        st.info("No insurance claims to review")
        conn.close()
        return
    
    # Group claims by status
    pending_claims = []
    processed_claims = []
    
    for claim in claims:
        if claim[9].lower() == 'pending':
            pending_claims.append(claim)
        else:
            processed_claims.append(claim)
    
    # Display pending claims first
    if pending_claims:
        st.markdown("<h3>Pending Claims</h3>", unsafe_allow_html=True)
        
        for claim in pending_claims:
            display_admin_claim(claim, conn, c)
    
    # Display processed claims
    if processed_claims:
        st.markdown("<h3>Processed Claims</h3>", unsafe_allow_html=True)
        
        for claim in processed_claims:
            display_admin_claim(claim, conn, c, show_actions=False)
    
    conn.close()

def display_admin_claim(claim, conn, c, show_actions=True):
    # Unpack claim data
    claim_id = claim[0]
    booking_id = claim[1]
    user_email = claim[2]
    incident_date = claim[3]
    description = claim[5]
    damage_type = claim[6]
    claim_amount = claim[7]
    evidence_images = claim[8]
    claim_status = claim[9]
    admin_notes = claim[10]
    user_name = claim[12]
    car_model = claim[14]
    car_year = claim[15]
    
    # Status color
    status_colors = {
        'pending': '#FFC107',
        'approved': '#28a745',
        'rejected': '#dc3545',
        'paid': '#17a2b8'
    }
    status_color = status_colors.get(claim_status.lower(), '#6c757d')
    
    with st.container():
        st.markdown(f"""
            <div class="insurance-claim-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3>Claim #{claim_id} - {car_model} ({car_year})</h3>
                    <span style="background-color: {status_color}; color: white; padding: 5px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: bold;">
                        {claim_status.upper()}
                    </span>
                </div>
                <p><strong>Submitted By:</strong> {user_name} ({user_email})</p>
                <p><strong>Booking ID:</strong> #{booking_id}</p>
                <p><strong>Incident Date:</strong> {incident_date}</p>
                <p><strong>Damage Type:</strong> {damage_type}</p>
                <p><strong>Claim Amount:</strong> {format_currency(claim_amount)}</p>
                <p><strong>Description:</strong> {description}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Show evidence images if available
        if evidence_images:
            try:
                images_data = json.loads(evidence_images)
                if images_data:
                    st.markdown("<h4>Evidence Photos</h4>", unsafe_allow_html=True)
                    cols = st.columns(min(len(images_data), 3))
                    for i, img_data in enumerate(images_data):
                        with cols[i % 3]:
                            st.image(f"data:image/jpeg;base64,{img_data}", use_column_width=True)
            except json.JSONDecodeError:
                st.error("Error loading evidence images")
        
        # Show admin notes if available
        if admin_notes:
            st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; margin-top: 1rem;">
                    <h4>Admin Notes</h4>
                    <p>{admin_notes}</p>
                </div>
            """, unsafe_allow_html=True)
        
        # Claim assessment form for pending claims
        if show_actions and claim_status.lower() == 'pending':
            with st.form(key=f"claim_review_{claim_id}"):
                admin_comment = st.text_area("Assessment Notes", placeholder="Provide details about your decision...")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    approve = st.form_submit_button("Approve Claim")
                with col2:
                    partial = st.form_submit_button("Partial Approval")
                with col3:
                    reject = st.form_submit_button("Reject Claim")
                
                if approve or partial or reject:
                    status = 'approved' if approve else 'partial' if partial else 'rejected'
                    
                    if update_claim_status(claim_id, status, admin_comment):
                        st.success(f"Claim has been {status}")
                        st.rerun()
        
        st.markdown("---")

def list_your_car_page():
    st.markdown("<h1>List Your Car</h1>", unsafe_allow_html=True)
    
    if st.button('← Back to Browse', key='list_back'):
        st.session_state.current_page = 'browse_cars'
    
    # Get user's subscription type to display benefits
    user_info = get_user_info(st.session_state.user_email)
    subscription_type = user_info[7] if user_info else 'free_host'
    
    # Display subscription benefits for hosts
    if subscription_type.endswith('_host'):
        benefits = get_subscription_benefits(subscription_type)
        commission_rate = '15%' if subscription_type == 'free_host' else '10%' if subscription_type == 'premium_host' else '5%'
        
        st.markdown(f"""
            <div style="background-color: #E8F5E9; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                <h3>Your {subscription_type.replace('_', ' ').title()} Benefits</h3>
                <p><strong>Commission Rate:</strong> {commission_rate}</p>
                <p><strong>Listing Visibility:</strong> {benefits['visibility']}</p>
                <p><strong>Damage Protection:</strong> {benefits['damage_protection']}</p>
                <p><strong>Payout Speed:</strong> {benefits['payout_speed']}</p>
                <p><strong>Support Level:</strong> {benefits['support']}</p>
            </div>
        """, unsafe_allow_html=True)
    
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
                        st.image(image, caption=f"Image {idx+1}", use_container_width=True)
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
                                use_container_width=True
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
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button('← Back to Browse', key='notifications_back'):
            st.session_state.current_page = 'browse_cars'
    
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Mark all notifications as read when viewing
    mark_notifications_as_read(st.session_state.user_email)
    
    # Fetch notifications
    c.execute('''
        SELECT * FROM notifications 
        WHERE user_email = ? 
        ORDER BY created_at DESC
    ''', (st.session_state.user_email,))
    
    notifications = c.fetchall()
    
    # Clear notifications functionality
    with col2:
        if notifications:
            if st.button('🗑️ Clear All'):
                try:
                    c.execute('''
                        DELETE FROM notifications 
                        WHERE user_email = ?
                    ''', (st.session_state.user_email,))
                    conn.commit()
                    st.success("Notifications cleared!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error clearing notifications: {e}")
    
    conn.close()
    
    if not notifications:
        st.info("No notifications")
        return
    
    for notif in notifications:
        # Color code notifications by type
        notification_colors = {
            'welcome': 'blue',
            'booking_confirmed': 'green',
            'booking_rejected': 'red',
            'listing_submitted': 'orange',
            'listing_approved': 'green',
            'listing_rejected': 'red',
            'claim_submitted': 'purple',
            'claim_approved': 'green',
            'claim_rejected': 'red',
            'claim_partial': 'orange',
            'subscription_activated': 'teal',
            'new_booking': 'blue'
        }
        
        color = notification_colors.get(notif[3], 'black')
        
        st.markdown(f"""
            <div style='background-color: white; padding: 1rem; border-radius: 10px; 
                 margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <p style='margin: 0; color: {color};'>{notif[2]}</p>
                <small style='color: #666;'>{notif[5]}</small>
            </div>
        """, unsafe_allow_html=True)

def update_bookings_table():
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Check existing columns
        c.execute("PRAGMA table_info(bookings)")
        columns = [column[1] for column in c.fetchall()]
        
        # Add missing columns if they don't exist
        if 'insurance_price' not in columns:
            c.execute("ALTER TABLE bookings ADD COLUMN insurance_price REAL DEFAULT 0")
        if 'driver_price' not in columns:
            c.execute("ALTER TABLE bookings ADD COLUMN driver_price REAL DEFAULT 0")
        if 'delivery_price' not in columns:
            c.execute("ALTER TABLE bookings ADD COLUMN delivery_price REAL DEFAULT 0")
        if 'vip_service_price' not in columns:
            c.execute("ALTER TABLE bookings ADD COLUMN vip_service_price REAL DEFAULT 0")
        
        conn.commit()
        print("Bookings table updated successfully")
    except sqlite3.Error as e:
        print(f"Database update error: {e}")
    finally:
        if conn:
            conn.close()
def about_us_page():
    st.markdown("<h1>About Luxury Car Rentals</h1>", unsafe_allow_html=True)
    
    if st.button('← Back to Welcome', key='about_back'):
        st.session_state.current_page = 'welcome'
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## Our Mission
        
        At Luxury Car Rentals, we're committed to transforming the car rental experience through sustainability, 
        innovation, and exceptional service. We believe in providing premium vehicles while contributing to a more 
        sustainable future for transportation.
        
        ## Our Commitment to Sustainable Development Goals
        
        Our business model aligns with multiple UN Sustainable Development Goals (SDGs), with particular focus on:
        
        ### SDG 11: Sustainable Cities and Communities
        
        We contribute to more sustainable cities and communities by:
        
        - Promoting shared mobility solutions to reduce the need for car ownership
        - Offering electric and hybrid vehicles to reduce urban emissions
        - Supporting smart mobility integration with public transportation
        - Implementing carbon offset programs for all rentals
        
        ### SDG 12: Responsible Consumption and Production
        
        We practice responsible business through:
        
        - Regular fleet maintenance to extend vehicle lifespan
        - Recycling and proper disposal of automotive fluids and parts
        - Paperless booking and digital receipts
        - Partner with sustainable suppliers and local businesses
        
        ### SDG 13: Climate Action
        
        We're actively fighting climate change by:
        
        - Transitioning our fleet to electric and hybrid vehicles
        - Carbon offsetting program for all rentals
        - Investment in renewable energy for our facilities
        - Educating customers on eco-friendly driving practices
        
        ## Our Sustainability Initiatives
        
        - **EV First**: 30% of our fleet is electric, growing to 75% by 2027
        - **Carbon Neutral**: All rentals include carbon offset in partnership with Climate Action UAE
        - **Green Facilities**: Our locations use solar power and rainwater harvesting
        - **Community Support**: 2% of profits go to sustainable transportation initiatives
        """, unsafe_allow_html=True)
    
    with col2:
        # SDG Logos and sustainability images
        st.image("https://www.localgovernmentassociation.sa.gov.au/__data/assets/image/0016/1205080/SDG-11.jpg", 
                caption="SDG 11: Sustainable Cities and Communities")
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRDayMFgGtUTvd6D_cWCYbCVQ46Hp0_6Bsh7xsODPvFX4nM3l63n8G11Zl6b3pWfE_Ia0A&usqp=CAU", 
                caption="SDG 12: Responsible Consumption and Production")
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSFdSP0D6_UN0LKhd-LdVffEuDdUomJA-OIB4v-sxDYVkSPNCcCTVuozTHfR1r4o4l1A5s&usqp=CAU", 
                caption="SDG 13: Climate Action")
    
    st.markdown("""
    ## Our Team
    
    Luxury Car Rentals was founded in 2020 by a team of automotive enthusiasts and sustainability experts 
    who believed luxury transportation could be both premium and environmentally responsible.
    
    Our leadership team brings together experience from the automotive industry, hospitality, technology, 
    and environmental science to create a truly innovative approach to car rentals.
    
    ## Contact Us
    
    **Address:** Dubai Marina, Tower 3, Floor 15  
    **Email:** info@luxurycarrentals.ae  
    **Phone:** +971 4 123 4567  
    
    Follow us on social media: @LuxuryCarRentalsUAE
    """, unsafe_allow_html=True)
def persist_session():
    """Ensure session persistence by storing login info in cookies"""
    # If we're logged in but haven't stored credentials in the session_state
    if 'persisted' not in st.session_state and st.session_state.logged_in:
        st.session_state.persisted = True  # Mark as persisted
        st.session_state.last_email = st.session_state.user_email  # Store the email
        
    # If we're not logged in but we have persisted credentials, restore them
    if not st.session_state.logged_in and 'persisted' in st.session_state and 'last_email' in st.session_state:
        if st.session_state.last_email:
            # Verify the user still exists in the database
            try:
                conn = sqlite3.connect('car_rental.db')
                c = conn.cursor()
                c.execute('SELECT * FROM users WHERE email = ?', (st.session_state.last_email,))
                user = c.fetchone()
                conn.close()
                
                if user:
                    # Restore login state
                    st.session_state.logged_in = True
                    st.session_state.user_email = st.session_state.last_email
                    print(f"Restored session for {st.session_state.user_email}")
            except Exception as e:
                print(f"Error restoring session: {e}")
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
    
    # Call session persistence function 
    persist_session()
    
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
