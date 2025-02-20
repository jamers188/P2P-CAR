import streamlit as st
import sqlite3
import os
import time
import json
import hashlib
import base64
import io
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from PIL import Image
from pathlib import Path
import uuid
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Constants
APP_NAME = "LuxeWheels"
APP_VERSION = "2.0.0"
DB_PATH = "luxewheels.db"
UPLOAD_DIR = Path("uploads")
TEMP_DIR = Path("temp")
CONFIG_DIR = Path("config")

# Ensure directories exist
for directory in [UPLOAD_DIR, TEMP_DIR, CONFIG_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# Color scheme
COLORS = {
    "primary": "#0A2647",       # Deep blue
    "secondary": "#144272",     # Medium blue
    "accent": "#205295",        # Light blue
    "highlight": "#2C74B3",     # Bright blue
    "white": "#FFFFFF",
    "light_gray": "#F8F9FA",
    "medium_gray": "#E9ECEF",
    "dark_gray": "#495057",
    "black": "#212529",
    "success": "#198754",       # Green
    "warning": "#FFC107",       # Yellow
    "danger": "#DC3545",        # Red
    "info": "#0DCAF0",          # Light blue
    "premium_gold": "#FFD700",  # Gold for premium features
    "elite_purple": "#7B2CBF",  # Purple for elite features
}

# Page configuration
st.set_page_config(
    page_title=f"{APP_NAME} | Luxury Car Rentals",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="auto"
)

# Database Management
class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.initialize_database()
        
    def get_connection(self):
        """Create and return a database connection"""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query, params=(), fetchone=False, fetchall=False, commit=False):
        """Execute a query with error handling"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            result = None
            if fetchone:
                result = cursor.fetchone()
            elif fetchall:
                result = cursor.fetchall()
                
            if commit:
                conn.commit()
                
            return result
        except sqlite3.Error as e:
            st.error(f"Database error: {e}")
            if conn and commit:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    def execute_script(self, script):
        """Execute a SQL script"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executescript(script)
            conn.commit()
            return True
        except sqlite3.Error as e:
            st.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def initialize_database(self):
        """Create database tables if they don't exist"""
        schema = '''
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            profile_image TEXT,
            subscription_type TEXT DEFAULT 'standard',
            subscription_expiry TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            preferences TEXT,
            verification_status TEXT DEFAULT 'pending',
            email_verified BOOLEAN DEFAULT FALSE,
            phone_verified BOOLEAN DEFAULT FALSE
        );
        
        -- Vehicles table
        CREATE TABLE IF NOT EXISTS vehicles (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            category TEXT NOT NULL,
            daily_rate REAL NOT NULL,
            location TEXT NOT NULL,
            description TEXT,
            specifications TEXT NOT NULL,
            available_from DATE,
            available_until DATE,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            average_rating REAL DEFAULT 0,
            total_bookings INTEGER DEFAULT 0,
            is_featured BOOLEAN DEFAULT FALSE,
            views INTEGER DEFAULT 0,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        );
        
        -- Vehicle Images table
        CREATE TABLE IF NOT EXISTS vehicle_images (
            id TEXT PRIMARY KEY,
            vehicle_id TEXT NOT NULL,
            image_data TEXT NOT NULL,
            image_type TEXT NOT NULL,
            is_primary BOOLEAN DEFAULT FALSE,
            display_order INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        );
        
        -- Bookings table
        CREATE TABLE IF NOT EXISTS bookings (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            vehicle_id TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            pickup_location TEXT NOT NULL,
            return_location TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            total_amount REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            payment_status TEXT DEFAULT 'unpaid',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            cancellation_date TIMESTAMP,
            cancellation_reason TEXT,
            has_insurance BOOLEAN DEFAULT FALSE,
            has_driver BOOLEAN DEFAULT FALSE,
            delivery_option TEXT,
            special_requests TEXT,
            insurance_amount REAL DEFAULT 0,
            driver_amount REAL DEFAULT 0,
            delivery_amount REAL DEFAULT 0,
            vip_services_amount REAL DEFAULT 0,
            discount_amount REAL DEFAULT 0,
            discount_code TEXT,
            tax_amount REAL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        );
        
        -- Reviews table
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            booking_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            vehicle_id TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'published',
            helpful_votes INTEGER DEFAULT 0,
            owner_response TEXT,
            owner_response_date TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        );
        
        -- Insurance Claims table
        CREATE TABLE IF NOT EXISTS insurance_claims (
            id TEXT PRIMARY KEY,
            booking_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            incident_date DATE NOT NULL,
            claim_date DATE NOT NULL,
            description TEXT NOT NULL,
            damage_type TEXT NOT NULL,
            claim_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            admin_notes TEXT,
            processed_by TEXT,
            processed_date TIMESTAMP,
            evidence_files TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        -- Claims Evidence table
        CREATE TABLE IF NOT EXISTS claim_evidence (
            id TEXT PRIMARY KEY,
            claim_id TEXT NOT NULL,
            file_data TEXT NOT NULL, 
            file_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (claim_id) REFERENCES insurance_claims(id)
        );
        
        -- Transactions table
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            booking_id TEXT,
            subscription_id TEXT,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'AED',
            transaction_type TEXT NOT NULL,
            payment_method TEXT,
            status TEXT NOT NULL,
            reference_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
        );
        
        -- Subscriptions table
        CREATE TABLE IF NOT EXISTS subscriptions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            plan_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            amount_paid REAL NOT NULL,
            auto_renew BOOLEAN DEFAULT FALSE,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            canceled_at TIMESTAMP,
            cancellation_reason TEXT,
            payment_method TEXT,
            discount_applied REAL DEFAULT 0,
            transaction_id TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        -- Notifications table
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            link TEXT,
            action_text TEXT,
            expires_at TIMESTAMP,
            priority TEXT DEFAULT 'normal',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        -- Admin Reviews table (for vehicle listings)
        CREATE TABLE IF NOT EXISTS admin_reviews (
            id TEXT PRIMARY KEY,
            vehicle_id TEXT NOT NULL,
            admin_id TEXT NOT NULL,
            comment TEXT,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
            FOREIGN KEY (admin_id) REFERENCES users(id)
        );
        
        -- Preferences table
        CREATE TABLE IF NOT EXISTS preferences (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            preference_key TEXT NOT NULL,
            preference_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, preference_key)
        );
        
        -- Promotional Codes table
        CREATE TABLE IF NOT EXISTS promo_codes (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            discount_type TEXT NOT NULL,
            discount_value REAL NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            usage_limit INTEGER,
            current_usage INTEGER DEFAULT 0,
            min_booking_amount REAL DEFAULT 0,
            applicable_vehicle_categories TEXT,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (created_by) REFERENCES users(id)
        );
        
        -- Analytics Events table
        CREATE TABLE IF NOT EXISTS analytics_events (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            event_type TEXT NOT NULL,
            event_data TEXT,
            device_info TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Wishlists table
        CREATE TABLE IF NOT EXISTS wishlists (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            vehicle_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
            UNIQUE(user_id, vehicle_id)
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_type, subscription_expiry);
        CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status);
        CREATE INDEX IF NOT EXISTS idx_vehicles_category ON vehicles(category);
        CREATE INDEX IF NOT EXISTS idx_vehicles_location ON vehicles(location);
        CREATE INDEX IF NOT EXISTS idx_vehicles_owner ON vehicles(owner_id);
        CREATE INDEX IF NOT EXISTS idx_vehicles_featured ON vehicles(is_featured);
        CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
        CREATE INDEX IF NOT EXISTS idx_bookings_dates ON bookings(start_date, end_date);
        CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id);
        CREATE INDEX IF NOT EXISTS idx_bookings_vehicle ON bookings(vehicle_id);
        CREATE INDEX IF NOT EXISTS idx_reviews_vehicle ON reviews(vehicle_id);
        CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(user_id);
        CREATE INDEX IF NOT EXISTS idx_claims_status ON insurance_claims(status);
        CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
        CREATE INDEX IF NOT EXISTS idx_subscriptions_dates ON subscriptions(start_date, end_date);
        CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, is_read);
        CREATE INDEX IF NOT EXISTS idx_promo_active ON promo_codes(is_active, start_date, end_date);
        CREATE INDEX IF NOT EXISTS idx_wishlists_user ON wishlists(user_id);
        '''
        
        # Execute the schema
        self.execute_script(schema)
        
        # Check if admin exists, if not create default admin
        admin_exists = self.execute_query(
            "SELECT id FROM users WHERE role = 'admin' LIMIT 1",
            fetchone=True
        )
        
        if not admin_exists:
            admin_id = str(uuid.uuid4())
            admin_password = "admin@LuxeWheels2025"
            password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
            
            self.execute_query(
                '''
                INSERT INTO users (
                    id, full_name, email, phone, password_hash, role, 
                    verification_status, email_verified, phone_verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                params=(
                    admin_id, 
                    "System Administrator",
                    "admin@luxewheels.com",
                    "+971501234567",
                    password_hash,
                    "admin",
                    "verified",
                    True,
                    True
                ),
                commit=True
            )
            
            print(f"Created admin user: admin@luxewheels.com with password: {admin_password}")

# Authentication and User Management
class AuthManager:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def hash_password(self, password):
        """Create a password hash"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, password_hash):
        """Verify a password against a hash"""
        return self.hash_password(password) == password_hash
    
    def create_user(self, full_name, email, phone, password, profile_image=None):
        """Create a new user account"""
        # Check if email already exists
        existing_user = self.db.execute_query(
            "SELECT id FROM users WHERE email = ?",
            params=(email,),
            fetchone=True
        )
        
        if existing_user:
            return False, "Email already registered"
        
        # Create new user
        user_id = str(uuid.uuid4())
        password_hash = self.hash_password(password)
        
        success = self.db.execute_query(
            '''
            INSERT INTO users (
                id, full_name, email, phone, password_hash, profile_image,
                created_at, verification_status
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'pending')
            ''',
            params=(user_id, full_name, email, phone, password_hash, profile_image),
            commit=True
        ) is not None
        
        if success:
            # Create welcome notification
            notification_id = str(uuid.uuid4())
            self.db.execute_query(
                '''
                INSERT INTO notifications (
                    id, user_id, title, message, notification_type, created_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''',
                params=(
                    notification_id,
                    user_id,
                    "Welcome to LuxeWheels!",
                    "Thank you for joining LuxeWheels. Start exploring our premium collection of luxury vehicles.",
                    "welcome"
                ),
                commit=True
            )
            
            return True, user_id
        return False, "Failed to create account"
    
    def login_user(self, email, password):
        """Authenticate a user"""
        user = self.db.execute_query(
            "SELECT id, password_hash, role, verification_status FROM users WHERE email = ?",
            params=(email,),
            fetchone=True
        )
        
        if not user:
            return False, "Invalid email or password"
        
        user_id, password_hash, role, verification_status = user
        
        if verification_status == 'suspended':
            return False, "Your account has been suspended. Please contact support."
        
        if self.verify_password(password, password_hash):
            # Update last login time
            self.db.execute_query(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                params=(user_id,),
                commit=True
            )
            return True, {"id": user_id, "role": role}
        
        return False, "Invalid email or password"
    
    def get_user_info(self, user_id):
        """Get user information"""
        return self.db.execute_query(
            '''
            SELECT id, full_name, email, phone, role, profile_image, 
                   subscription_type, subscription_expiry, created_at,
                   last_login, verification_status, email_verified, phone_verified
            FROM users WHERE id = ?
            ''',
            params=(user_id,),
            fetchone=True
        )
    
    def update_user_profile(self, user_id, full_name=None, phone=None, profile_image=None):
        """Update user profile information"""
        # Build update query based on provided parameters
        update_fields = []
        params = []
        
        if full_name:
            update_fields.append("full_name = ?")
            params.append(full_name)
            
        if phone:
            update_fields.append("phone = ?")
            params.append(phone)
            
        if profile_image:
            update_fields.append("profile_image = ?")
            params.append(profile_image)
            
        if not update_fields:
            return False, "No fields to update"
            
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        params.append(user_id)
        
        success = self.db.execute_query(query, params=params, commit=True) is not None
        return success, "Profile updated successfully" if success else "Failed to update profile"
    
    def change_password(self, user_id, current_password, new_password):
        """Change user password"""
        # Get current password hash
        current_hash = self.db.execute_query(
            "SELECT password_hash FROM users WHERE id = ?",
            params=(user_id,),
            fetchone=True
        )
        
        if not current_hash:
            return False, "User not found"
            
        current_hash = current_hash[0]
        
        # Verify current password
        if not self.verify_password(current_password, current_hash):
            return False, "Current password is incorrect"
            
        # Update to new password
        new_hash = self.hash_password(new_password)
        success = self.db.execute_query(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            params=(new_hash, user_id),
            commit=True
        ) is not None
        
        return success, "Password changed successfully" if success else "Failed to change password"


class UIComponents:
    def __init__(self, colors=COLORS):
        self.colors = colors
        self.apply_theme()
        
    def apply_theme(self):
        """Apply custom theme to Streamlit"""
        self.inject_custom_css()
        
    def inject_custom_css(self):
        """Inject custom CSS for styling"""
        st.markdown(f"""
        <style>
            /* Root variables for theming */
            :root {{
                --color-primary: {self.colors["primary"]};
                --color-secondary: {self.colors["secondary"]};
                --color-accent: {self.colors["accent"]};
                --color-highlight: {self.colors["highlight"]};
                --color-white: {self.colors["white"]};
                --color-light-gray: {self.colors["light_gray"]};
                --color-medium-gray: {self.colors["medium_gray"]};
                --color-dark-gray: {self.colors["dark_gray"]};
                --color-black: {self.colors["black"]};
                --color-success: {self.colors["success"]};
                --color-warning: {self.colors["warning"]};
                --color-danger: {self.colors["danger"]};
                --color-info: {self.colors["info"]};
                --color-premium-gold: {self.colors["premium_gold"]};
                --color-elite-purple: {self.colors["elite_purple"]};
                
                --font-family-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                --font-family-mono: 'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
                
                --border-radius-sm: 4px;
                --border-radius-md: 8px;
                --border-radius-lg: 12px;
                --border-radius-xl: 20px;
                
                --box-shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
                --box-shadow-md: 0 4px 6px rgba(0,0,0,0.1);
                --box-shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
                --box-shadow-xl: 0 20px 25px rgba(0,0,0,0.1);
            }}
            
            /* Base styles */
            .stApp {{
                background-color: var(--color-light-gray);
                font-family: var(--font-family-sans);
                color: var(--color-black);
            }}
            
            /* Typography */
            h1, h2, h3, h4, h5, h6 {{
                font-family: var(--font-family-sans);
                font-weight: 700;
                color: var(--color-primary);
                letter-spacing: -0.02em;
            }}
            
            h1 {{
                font-size: 2.5rem;
                letter-spacing: -0.03em;
            }}
            
            h2 {{
                font-size: 2rem;
                margin-top: 2rem;
            }}
            
            h3 {{
                font-size: 1.5rem;
                color: var(--color-secondary);
            }}
            
            p, li, span {{
                font-family: var(--font-family-sans);
                line-height: 1.6;
            }}
            
            code {{
                font-family: var(--font-family-mono);
                padding: 0.2em 0.4em;
                background-color: var(--color-medium-gray);
                border-radius: var(--border-radius-sm);
            }}
            
            /* Layout components */
            .main-container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 1rem;
            }}
            
            .container {{
                background-color: var(--color-white);
                border-radius: var(--border-radius-lg);
                padding: 2rem;
                margin-bottom: 1.5rem;
                box-shadow: var(--box-shadow-md);
            }}
            
            .card {{
                background-color: var(--color-white);
                border-radius: var(--border-radius-md);
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: var(--box-shadow-sm);
                transition: all 0.3s ease;
            }}
            
            .card:hover {{
                transform: translateY(-4px);
                box-shadow: var(--box-shadow-md);
            }}
            
            /* Custom button styles */
            .st-ba {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 0.625rem 1.25rem;
                font-size: 1rem;
                font-weight: 600;
                line-height: 1.5;
                border-radius: var(--border-radius-md);
                transition: all 0.15s ease-in-out;
                cursor: pointer;
            }}
            
            .stButton > button {{
                background-color: var(--color-primary);
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: var(--border-radius-md);
                font-weight: 600;
                transition: all 0.15s ease;
                width: 100%;
                height: auto;
                display: inline-flex;
                align-items: center;
                justify-content: center;
            }}
            
            .stButton > button:hover {{
                background-color: var(--color-highlight);
                transform: translateY(-2px);
                box-shadow: var(--box-shadow-md);
            }}
            
            .stButton > button:active {{
                transform: translateY(0);
                box-shadow: var(--box-shadow-sm);
            }}
            
            /* Custom input styles */
            .stTextInput > div > div > input,
            .stNumberInput > div > div > input,
            .stDateInput > div > div > input {{
                border-radius: var(--border-radius-md);
                border: 1px solid var(--color-medium-gray);
                padding: 0.625rem 1rem;
                transition: all 0.15s ease;
            }}
            
            .stTextInput > div > div > input:focus,
            .stNumberInput > div > div > input:focus,
            .stDateInput > div > div > input:focus {{
                border-color: var(--color-highlight);
                box-shadow: 0 0 0 2px rgba(44, 116, 179, 0.2);
            }}
            
            /* Sidebar styling */
            .css-1lcbmhc, .css-1d391kg {{
                background-color: var(--color-primary);
                color: var(--color-white);
            }}
            
            .css-1lcbmhc h1, .css-1d391kg h1,
            .css-1lcbmhc h2, .css-1d391kg h2,
            .css-1lcbmhc h3, .css-1d391kg h3 {{
                color: var(--color-white);
            }}
            
            /* Custom alert/message boxes */
            .message-box {{
                padding: 1rem;
                margin: 1rem 0;
                border-radius: var(--border-radius-md);
                border-left: 4px solid;
            }}
            
            .success-box {{
                background-color: #E8F5E9;
                border-left-color: var(--color-success);
                color: #2E7D32;
            }}
            
            .warning-box {{
                background-color: #FFF8E1;
                border-left-color: var(--color-warning);
                color: #F57F17;
            }}
            
            .error-box {{
                background-color: #FFEBEE;
                border-left-color: var(--color-danger);
                color: #C62828;
            }}
            
            .info-box {{
                background-color: #E3F2FD;
                border-left-color: var(--color-info);
                color: #1565C0;
            }}
            
            /* Status badges */
            .status-badge {{
                display: inline-block;
                padding: 0.25rem 0.75rem;
                font-size: 0.875rem;
                font-weight: 600;
                line-height: 1.5;
                text-align: center;
                white-space: nowrap;
                vertical-align: baseline;
                border-radius: 50rem;
            }}
            
            .status-pending {{
                background-color: #FFF8E1;
                color: #F57F17;
            }}
            
            .status-approved {{
                background-color: #E8F5E9;
                color: #2E7D32;
            }}
            
            .status-rejected {{
                background-color: #FFEBEE;
                color: #C62828;
            }}
            
            .status-completed {{
                background-color: #E8EAF6;
                color: #3949AB;
            }}
            
            .status-canceled {{
                background-color: #ECEFF1;
                color: #546E7A;
            }}
            
            /* Subscription level indicators */
            .subscription-standard {{
                color: var(--color-secondary);
            }}
            
            .subscription-premium {{
                color: var(--color-premium-gold);
            }}
            
            .subscription-elite {{
                color: var(--color-elite-purple);
            }}
            
            /* Header */
            .app-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem 2rem;
                background-color: var(--color-primary);
                color: white;
                border-radius: var(--border-radius-md);
                margin-bottom: 2rem;
                box-shadow: var(--box-shadow-md);
            }}
            
            .app-header-logo {{
                font-size: 1.75rem;
                font-weight: 800;
                letter-spacing: -0.03em;
            }}
            
            .app-header-nav {{
                display: flex;
                gap: 1.5rem;
                align-items: center;
            }}
            
            /* Footer */
            .app-footer {{
                padding: 2rem;
                margin-top: 3rem;
                text-align: center;
                color: var(--color-dark-gray);
                border-top: 1px solid var(--color-medium-gray);
            }}
            
            /* Vehicle cards */
            .vehicle-card {{
                display: flex;
                flex-direction: column;
                background-color: white;
                border-radius: var(--border-radius-lg);
                overflow: hidden;
                box-shadow: var(--box-shadow-md);
                transition: all 0.3s ease;
                height: 100%;
            }}
            
            .vehicle-card:hover {{
                transform: translateY(-5px);
                box-shadow: var(--box-shadow-lg);
            }}
            
            .vehicle-card-image {{
                height: 200px;
                width: 100%;
                object-fit: cover;
            }}
            
            .vehicle-card-content {{
                padding: 1.5rem;
                flex: 1;
                display: flex;
                flex-direction: column;
            }}
            
            .vehicle-card-title {{
                font-size: 1.25rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                color: var(--color-primary);
            }}
            
            .vehicle-card-footer {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem 1.5rem;
                background-color: var(--color-light-gray);
                margin-top: auto;
            }}
            
            /* Price display */
            .price-display {{
                font-size: 1.5rem;
                font-weight: 700;
                color: var(--color-primary);
            }}
            
            .price-unit {{
                font-size: 0.875rem;
                color: var(--color-dark-gray);
            }}
            
            /* Notification dot */
            .notification-dot {{
                position: relative;
            }}
            
            .notification-dot::after {{
                content: '';
                position: absolute;
                top: -2px;
                right: -2px;
                width: 8px;
                height: 8px;
                background-color: var(--color-danger);
                border-radius: 50%;
            }}
            
            /* Profile menu */
            .profile-menu {{
                position: relative;
                display: inline-block;
            }}
            
            .profile-menu-content {{
                display: none;
                position: absolute;
                right: 0;
                top: 100%;
                background-color: white;
                min-width: 200px;
                box-shadow: var(--box-shadow-md);
                border-radius: var(--border-radius-md);
                z-index: 1000;
            }}
            
            .profile-menu:hover .profile-menu-content {{
                display: block;
            }}
            
            .profile-menu-item {{
                padding: 0.75rem 1rem;
                display: block;
                color: var(--color-black);
                text-decoration: none;
                transition: all 0.2s ease;
            }}
            
            .profile-menu-item:hover {{
                background-color: var(--color-light-gray);
            }}
            
            /* Tabs */
            .custom-tabs {{
                display: flex;
                border-bottom: 1px solid var(--color-medium-gray);
                margin-bottom: 2rem;
            }}
            
            .custom-tab {{
                padding: 0.75rem 1.5rem;
                cursor: pointer;
                font-weight: 600;
                border-bottom: 3px solid transparent;
                transition: all 0.2s ease;
            }}
            
            .custom-tab:hover {{
                color: var(--color-highlight);
            }}
            
            .custom-tab.active {{
                color: var(--color-primary);
                border-bottom-color: var(--color-primary);
            }}

            /* Filter panel */
            .filter-panel {{
                background-color: white;
                border-radius: var(--border-radius-md);
                padding: 1.5rem;
                margin-bottom: 2rem;
                box-shadow: var(--box-shadow-sm);
            }}
            
            /* Subscription cards */
            .subscription-card {{
                background-color: white;
                border-radius: var(--border-radius-lg);
                overflow: hidden;
                box-shadow: var(--box-shadow-md);
                height: 100%;
                display: flex;
                flex-direction: column;
                transition: all 0.3s ease;
            }}
            
            .subscription-card:hover {{
                transform: translateY(-5px);
                box-shadow: var(--box-shadow-lg);
            }}
            
            .subscription-card-header {{
                background-color: var(--color-primary);
                color: white;
                padding: 1.5rem;
                text-align: center;
            }}
            
            .subscription-card-premium .subscription-card-header {{
                background-color: var(--color-premium-gold);
                background-image: linear-gradient(135deg, var(--color-premium-gold), #DAA520);
            }}
            
            .subscription-card-elite .subscription-card-header {{
                background-color: var(--color-elite-purple);
                background-image: linear-gradient(135deg, var(--color-elite-purple), #5B3A9F);
            }}
            
            .subscription-card-price {{
                font-size: 2.5rem;
                font-weight: 700;
                margin: 1rem 0;
            }}
            
            .subscription-card-period {{
                font-size: 0.875rem;
                opacity: 0.8;
            }}
            
            .subscription-card-content {{
                padding: 1.5rem;
                flex: 1;
            }}
            
            .subscription-card-features {{
                list-style-type: none;
                padding: 0;
                margin: 0;
            }}
            
            .subscription-card-features li {{
                padding: 0.5rem 0;
                display: flex;
                align-items: center;
            }}
            
            .subscription-card-features li::before {{
                content: '✓';
                margin-right: 0.5rem;
                color: var(--color-success);
                font-weight: bold;
            }}
            
            .subscription-card-footer {{
                padding: 1.5rem;
                background-color: var(--color-light-gray);
                text-align: center;
            }}
            
            /* Booking timeline */
            .booking-timeline {{
                position: relative;
                padding-left: 2.5rem;
                margin-bottom: 2rem;
            }}
            
            .booking-timeline::before {{
                content: '';
                position: absolute;
                left: 1rem;
                top: 0;
                bottom: 0;
                width: 2px;
                background-color: var(--color-medium-gray);
            }}
            
            .booking-timeline-item {{
                position: relative;
                padding-bottom: 2rem;
            }}
            
            .booking-timeline-item::before {{
                content: '';
                position: absolute;
                left: -1.5rem;
                top: 0.25rem;
                width: 1rem;
                height: 1rem;
                border-radius: 50%;
                background-color: var(--color-primary);
                border: 2px solid white;
            }}
            
            .booking-timeline-item.completed::before {{
                background-color: var(--color-success);
            }}
            
            .booking-timeline-item.pending::before {{
                background-color: var(--color-warning);
            }}
            
            .booking-timeline-item.canceled::before {{
                background-color: var(--color-danger);
            }}
            
            .booking-timeline-date {{
                font-size: 0.875rem;
                color: var(--color-dark-gray);
                margin-bottom: 0.25rem;
            }}
            
            .booking-timeline-title {{
                font-weight: 600;
                margin-bottom: 0.5rem;
            }}
            
            /* Review stars */
            .rating {{
                display: inline-flex;
                color: #FFD700;
            }}
            
            /* Image gallery */
            .image-gallery {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
                gap: 1rem;
                margin: 1.5rem 0;
            }}
            
            .gallery-image {{
                width: 100%;
                height: 150px;
                object-fit: cover;
                border-radius: var(--border-radius-md);
                transition: all 0.2s ease;
                cursor: pointer;
            }}
            
            .gallery-image:hover {{
                transform: scale(1.05);
                box-shadow: var(--box-shadow-md);
            }}
            
            /* Modal */
            .modal-backdrop {{
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            }}
            
            .modal-content {{
                background-color: white;
                border-radius: var(--border-radius-lg);
                width: 90%;
                max-width: 600px;
                max-height: 90vh;
                overflow-y: auto;
                padding: 2rem;
                box-shadow: var(--box-shadow-xl);
            }}
            
            .modal-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1.5rem;
            }}
            
            .modal-close {{
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                color: var(--color-dark-gray);
            }}
            
            .modal-body {{
                margin-bottom: 1.5rem;
            }}
            
            .modal-footer {{
                display: flex;
                justify-content: flex-end;
                gap: 1rem;
            }}
        </style>
        """, unsafe_allow_html=True)
    
    def header(self, title, subtitle=None):
        """Display a page header with optional subtitle"""
        st.markdown(f"""
        <div class="container">
            <h1>{title}</h1>
            {f'<p>{subtitle}</p>' if subtitle else ''}
        </div>
        """, unsafe_allow_html=True)
    
    def success_message(self, message):
        """Display a success message"""
        st.markdown(f"""
        <div class="message-box success-box">
            <strong>Success!</strong> {message}
        </div>
        """, unsafe_allow_html=True)
    
    def error_message(self, message):
        """Display an error message"""
        st.markdown(f"""
        <div class="message-box error-box">
            <strong>Error!</strong> {message}
        </div>
        """, unsafe_allow_html=True)
    
    def warning_message(self, message):
        """Display a warning message"""
        st.markdown(f"""
        <div class="message-box warning-box">
            <strong>Warning!</strong> {message}
        </div>
        """, unsafe_allow_html=True)
    
    def info_message(self, message):
        """Display an info message"""
        st.markdown(f"""
        <div class="message-box info-box">
            <strong>Info:</strong> {message}
        </div>
        """, unsafe_allow_html=True)
    
    def status_badge(self, status):
        """Display a status badge"""
        status = status.lower()
        return f"""
        <span class="status-badge status-{status}">
            {status.upper()}
        </span>
        """
    
    def vehicle_card(self, vehicle, show_buttons=True):
        """Display a vehicle card"""
        # Parse specifications from JSON if it's a string
        specs = vehicle.get('specifications', '{}')
        if isinstance(specs, str):
            try:
                specs = json.loads(specs)
            except:
                specs = {}
        
        # Get primary image or placeholder
        image_data = vehicle.get('primary_image', None)
        if image_data:
            image_html = f'<img src="data:image/jpeg;base64,{image_data}" class="vehicle-card-image" alt="{vehicle["brand"]} {vehicle["model"]}" />'
        else:
            image_html = f'<div class="vehicle-card-image" style="display: flex; justify-content: center; align-items: center; background-color: #f0f0f0;"><span>No Image Available</span></div>'
        
        # Format price
        price = vehicle.get('daily_rate', 0)
        formatted_price = f"AED {price:,.2f}"
        
        features = []
        if specs.get('engine'):
            features.append(f"<span>🏎️ {specs['engine']}</span>")
        if specs.get('transmission'):
            features.append(f"<span>⚙️ {specs['transmission']}</span>")
        if specs.get('mileage'):
            features.append(f"<span>📊 {specs['mileage']} km</span>")
        
        features_html = '<div style="display: flex; flex-wrap: wrap; gap: 1rem; margin: 1rem 0;">'
        for feature in features:
            features_html += f'<div style="color: var(--color-dark-gray); font-size: 0.875rem;">{feature}</div>'
        features_html += '</div>'
        
        buttons_html = ""
        if show_buttons:
            buttons_html = f"""
            <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                <a href="?page=vehicle_details&id={vehicle['id']}" 
                   style="flex: 1; background-color: var(--color-primary); color: white; padding: 0.5rem 1rem; border-radius: var(--border-radius-md); text-align: center; text-decoration: none; font-weight: 600;">
                   View Details
                </a>
                <button 
                   onclick="addToWishlist('{vehicle['id']}')" 
                   style="background: none; border: none; cursor: pointer; color: var(--color-dark-gray);">
                   ❤️
                </button>
            </div>
            """
        
        return f"""
        <div class="vehicle-card">
            {image_html}
            <div class="vehicle-card-content">
                <div class="vehicle-card-title">{vehicle['brand']} {vehicle['model']} ({vehicle['year']})</div>
                <div style="color: var(--color-dark-gray); font-size: 0.875rem;">
                    📍 {vehicle.get('location', 'N/A')}
                </div>
                {features_html}
                <div class="price-display">
                    {formatted_price}<span class="price-unit">/day</span>
                </div>
                {buttons_html}
            </div>
        </div>
        """
    
    def subscription_card(self, plan, is_current=False):
        """Display a subscription plan card"""
        plan_type = plan.get('type', 'standard')
        
        # Calculate classes based on plan type
        classes = "subscription-card"
        if plan_type == 'premium':
            classes += " subscription-card-premium"
        elif plan_type == 'elite':
            classes += " subscription-card-elite"
        
        price = plan.get('price', 0)
        period = plan.get('period', 'month')
        
        # Generate features list
        features_html = ""
        for feature in plan.get('features', []):
            features_html += f"<li>{feature}</li>"
        
        button_text = "Current Plan" if is_current else f"Subscribe for AED {price:,.2f}/{period}"
        button_disabled = "disabled" if is_current else ""
        
        return f"""
        <div class="{classes}">
            <div class="subscription-card-header">
                <h3>{plan.get('name', 'Standard')}</h3>
                <div class="subscription-card-price">
                    AED {price:,.2f}
                    <span class="subscription-card-period">/{period}</span>
                </div>
            </div>
            <div class="subscription-card-content">
                <ul class="subscription-card-features">
                    {features_html}
                </ul>
            </div>
            <div class="subscription-card-footer">
                <button {button_disabled} onclick="subscribePlan('{plan_type}')" 
                    class="stButton" style="width: 100%; padding: 0.625rem 1.25rem;">
                    {button_text}
                </button>
            </div>
        </div>
        """

# Helper classes - these provide functionality used throughout the app

class ImageHandler:
    """Class for handling image operations"""
    
    @staticmethod
    def save_uploaded_image(uploaded_file, max_size=(1200, 1200), quality=85):
        """Convert uploaded image to base64 encoded string"""
        try:
            # Open the image
            image = Image.open(uploaded_file)
            
            # Resize if needed
            if image.width > max_size[0] or image.height > max_size[1]:
                image.thumbnail(max_size, Image.LANCZOS)
            
            # Convert RGBA to RGB if needed
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
                
            # Save to bytes buffer
            buf = io.BytesIO()
            image.save(buf, format='JPEG', quality=quality)
            
            # Get the binary data and encode as base64
            image_data = base64.b64encode(buf.getvalue()).decode()
            return image_data
        
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
            return None
    
    @staticmethod
    def validate_image(uploaded_file, max_size_mb=5, valid_formats=None):
        """Validate an uploaded image file"""
        if valid_formats is None:
            valid_formats = ['JPEG', 'JPG', 'PNG']
            
        try:
            # Check file size
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                return False, f"Image size exceeds {max_size_mb}MB limit. Please upload a smaller image."
                
            # Check file format
            image = Image.open(uploaded_file)
            if image.format.upper() not in [fmt.upper() for fmt in valid_formats]:
                return False, f"Invalid image format. Please upload one of these formats: {', '.join(valid_formats)}"
                
            return True, "Image is valid"
            
        except Exception as e:
            return False, f"Error validating image: {str(e)}"
    
    @staticmethod
    def render_image_gallery(images, on_click=None):
        """Render an image gallery from a list of image data"""
        if not images:
            return "<div>No images available</div>"
            
        gallery_html = '<div class="image-gallery">'
        
        for i, image_data in enumerate(images):
            onclick = f"onclick=\"{on_click}('{i}')\"" if on_click else ""
            gallery_html += f"""
            <img 
                src="data:image/jpeg;base64,{image_data}" 
                class="gallery-image"
                {onclick}
                alt="Image {i+1}"
            />
            """
            
        gallery_html += '</div>'
        return gallery_html


        class NotificationManager:
    """Class for managing user notifications"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_notification(self, user_id, title, message, notification_type, link=None, action_text=None, priority='normal'):
        """Create a new notification for a user"""
        notification_id = str(uuid.uuid4())
        
        result = self.db.execute_query(
            '''
            INSERT INTO notifications (
                id, user_id, title, message, notification_type, link, action_text, 
                priority, created_at, is_read
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, FALSE)
            ''',
            params=(
                notification_id, user_id, title, message, notification_type, 
                link, action_text, priority
            ),
            commit=True
        )
        
        return result is not None
    
    def get_user_notifications(self, user_id, limit=50, unread_only=False):
        """Get notifications for a user"""
        query = '''
            SELECT id, title, message, notification_type, is_read, created_at, 
                   link, action_text, priority
            FROM notifications
            WHERE user_id = ?
        '''
        
        params = [user_id]
        
        if unread_only:
            query += " AND is_read = FALSE"
            
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        return self.db.execute_query(query, params=params, fetchall=True)
    
    def mark_as_read(self, notification_id):
        """Mark a notification as read"""
        return self.db.execute_query(
            "UPDATE notifications SET is_read = TRUE WHERE id = ?",
            params=(notification_id,),
            commit=True
        ) is not None
    
    def mark_all_as_read(self, user_id):
        """Mark all notifications for a user as read"""
        return self.db.execute_query(
            "UPDATE notifications SET is_read = TRUE WHERE user_id = ?",
            params=(user_id,),
            commit=True
        ) is not None
    
    def delete_notification(self, notification_id):
        """Delete a notification"""
        return self.db.execute_query(
            "DELETE FROM notifications WHERE id = ?",
            params=(notification_id,),
            commit=True
        ) is not None
    
    def delete_all_notifications(self, user_id):
        """Delete all notifications for a user"""
        return self.db.execute_query(
            "DELETE FROM notifications WHERE user_id = ?",
            params=(user_id,),
            commit=True
        ) is not None
    
    def get_unread_count(self, user_id):
        """Get count of unread notifications for a user"""
        result = self.db.execute_query(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = FALSE",
            params=(user_id,),
            fetchone=True
        )
        
        return result[0] if result else 0

class VehicleManager:
    """Class for managing vehicle listings"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_vehicle(self, owner_id, brand, model, year, category, daily_rate, 
                       location, description, specifications):
        """Create a new vehicle listing"""
        vehicle_id = str(uuid.uuid4())
        
        # Convert specifications to JSON if it's a dict
        if isinstance(specifications, dict):
            specifications = json.dumps(specifications)
        
        result = self.db.execute_query(
            '''
            INSERT INTO vehicles (
                id, owner_id, brand, model, year, category, daily_rate, location,
                description, specifications, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''',
            params=(
                vehicle_id, owner_id, brand, model, year, category, daily_rate,
                location, description, specifications
            ),
            commit=True
        )
        
        return (result is not None, vehicle_id)
    
    def add_vehicle_image(self, vehicle_id, image_data, image_type='jpeg', is_primary=False):
        """Add an image to a vehicle listing"""
        image_id = str(uuid.uuid4())
        
        # Get the current highest display_order for this vehicle
        max_order = self.db.execute_query(
            "SELECT MAX(display_order) FROM vehicle_images WHERE vehicle_id = ?",
            params=(vehicle_id,),
            fetchone=True
        )
        
        display_order = 1
        if max_order and max_order[0] is not None:
            display_order = max_order[0] + 1
        
        # If this is a primary image, update all other images to non-primary
        if is_primary:
            self.db.execute_query(
                "UPDATE vehicle_images SET is_primary = FALSE WHERE vehicle_id = ?",
                params=(vehicle_id,),
                commit=True
            )
        
        result = self.db.execute_query(
            '''
            INSERT INTO vehicle_images (
                id, vehicle_id, image_data, image_type, is_primary, 
                display_order, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''',
            params=(
                image_id, vehicle_id, image_data, image_type, 
                is_primary, display_order
            ),
            commit=True
        )
        
        return result is not None
    
    def get_vehicle(self, vehicle_id, include_images=True):
        """Get a vehicle by ID with optional images"""
        vehicle = self.db.execute_query(
            '''
            SELECT v.*, u.full_name as owner_name, u.email as owner_email
            FROM vehicles v
            JOIN users u ON v.owner_id = u.id
            WHERE v.id = ?
            ''',
            params=(vehicle_id,),
            fetchone=True
        )
        
        if not vehicle:
            return None
        
        # Convert to dictionary for easier access
        columns = [
            'id', 'owner_id', 'brand', 'model', 'year', 'category', 'daily_rate',
            'location', 'description', 'specifications', 'available_from', 
            'available_until', 'status', 'created_at', 'updated_at', 
            'average_rating', 'total_bookings', 'is_featured', 'views',
            'owner_name', 'owner_email'
        ]
        
        vehicle_dict = {columns[i]: vehicle[i] for i in range(len(columns))}
        
        # Get images if requested
        if include_images:
            images = self.db.execute_query(
                '''
                SELECT id, image_data, image_type, is_primary, display_order
                FROM vehicle_images
                WHERE vehicle_id = ?
                ORDER BY is_primary DESC, display_order ASC
                ''',
                params=(vehicle_id,),
                fetchall=True
            )
            
            # Add images to vehicle dict
            vehicle_dict['images'] = []
            vehicle_dict['primary_image'] = None
            
            if images:
                for image in images:
                    image_dict = {
                        'id': image[0],
                        'data': image[1],
                        'type': image[2],
                        'is_primary': bool(image[3]),
                        'display_order': image[4]
                    }
                    vehicle_dict['images'].append(image_dict)
                    
                    # Set primary image
                    if image_dict['is_primary'] and not vehicle_dict['primary_image']:
                        vehicle_dict['primary_image'] = image_dict['data']
        
        return vehicle_dict
    
    def get_vehicles(self, filters=None, sort_by='created_at', sort_order='DESC', limit=50, offset=0):
        """Get vehicles with filters and sorting"""
        if filters is None:
            filters = {}
        
        # Base query
        query = '''
            SELECT v.*, 
                   u.full_name as owner_name,
                   (SELECT image_data FROM vehicle_images 
                    WHERE vehicle_id = v.id AND is_primary = TRUE 
                    LIMIT 1) as primary_image
            FROM vehicles v
            JOIN users u ON v.owner_id = u.id
            WHERE 1=1
        '''
        
        params = []
        
        # Add filters
        if 'status' in filters:
            query += " AND v.status = ?"
            params.append(filters['status'])
        
        if 'category' in filters:
            query += " AND v.category = ?"
            params.append(filters['category'])
            
        if 'location' in filters:
            query += " AND v.location = ?"
            params.append(filters['location'])
            
        if 'owner_id' in filters:
            query += " AND v.owner_id = ?"
            params.append(filters['owner_id'])
            
        if 'min_price' in filters:
            query += " AND v.daily_rate >= ?"
            params.append(filters['min_price'])
            
        if 'max_price' in filters:
            query += " AND v.daily_rate <= ?"
            params.append(filters['max_price'])
            
        if 'search' in filters and filters['search']:
            search_term = f"%{filters['search']}%"
            query += " AND (v.brand LIKE ? OR v.model LIKE ? OR v.description LIKE ?)"
            params.extend([search_term, search_term, search_term])
            
        if 'available_from' in filters and 'available_until' in filters:
            # Complex availability check considering bookings
            query += '''
                AND v.id NOT IN (
                    SELECT vehicle_id FROM bookings
                    WHERE status IN ('confirmed', 'pending')
                    AND (
                        (start_date <= ? AND end_date >= ?) OR
                        (start_date <= ? AND end_date >= ?) OR
                        (start_date >= ? AND end_date <= ?)
                    )
                )
            '''
            start_date = filters['available_from']
            end_date = filters['available_until']
            params.extend([end_date, start_date, start_date, start_date, start_date, end_date])
        
        # Featured vehicles first, then sort by specified field
        if 'featured_first' in filters and filters['featured_first']:
            query += f" ORDER BY v.is_featured DESC, v.{sort_by} {sort_order}"
        else:
            query += f" ORDER BY v.{sort_by} {sort_order}"
            
        # Add limit and offset
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        vehicles = self.db.execute_query(query, params=params, fetchall=True)
        
        if not vehicles:
            return []
            
        # Convert to list of dictionaries
        columns = [
            'id', 'owner_id', 'brand', 'model', 'year', 'category', 'daily_rate',
            'location', 'description', 'specifications', 'available_from', 
            'available_until', 'status', 'created_at', 'updated_at', 
            'average_rating', 'total_bookings', 'is_featured', 'views',
            'owner_name', 'primary_image'
        ]
        
        result = []
        for vehicle in vehicles:
            vehicle_dict = {columns[i]: vehicle[i] for i in range(min(len(columns), len(vehicle)))}
            result.append(vehicle_dict)
            
        return result
    
    def update_vehicle(self, vehicle_id, **kwargs):
        """Update vehicle details"""
        allowed_fields = {
            'brand', 'model', 'year', 'category', 'daily_rate', 'location',
            'description', 'specifications', 'available_from', 'available_until',
            'status', 'is_featured'
        }
        
        # Filter out disallowed fields
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_data:
            return False, "No valid fields to update"
            
        # Handle specifications dict
        if 'specifications' in update_data and isinstance(update_data['specifications'], dict):
            update_data['specifications'] = json.dumps(update_data['specifications'])
            
        # Build update query
        set_clauses = [f"{field} = ?" for field in update_data.keys()]
        set_clause = ", ".join(set_clauses)
        set_clause += ", updated_at = CURRENT_TIMESTAMP"
        
        query = f"UPDATE vehicles SET {set_clause} WHERE id = ?"
        
        params = list(update_data.values())
        params.append(vehicle_id)
        
        result = self.db.execute_query(query, params=params, commit=True)
        
        return result is not None, "Vehicle updated successfully" if result is not None else "Failed to update vehicle"
    
    def delete_vehicle(self, vehicle_id):
        """Delete a vehicle and its images"""
        # First delete related images
        self.db.execute_query(
            "DELETE FROM vehicle_images WHERE vehicle_id = ?",
            params=(vehicle_id,),
            commit=True
        )
        
        # Then delete the vehicle
        result = self.db.execute_query(
            "DELETE FROM vehicles WHERE id = ?",
            params=(vehicle_id,),
            commit=True
        )
        
        return result is not None
    
    def increment_views(self, vehicle_id):
        """Increment the view count for a vehicle"""
        return self.db.execute_query(
            "UPDATE vehicles SET views = views + 1 WHERE id = ?",
            params=(vehicle_id,),
            commit=True
        ) is not None
    
    def get_vehicle_categories(self):
        """Get list of all vehicle categories in use"""
        results = self.db.execute_query(
            "SELECT DISTINCT category FROM vehicles WHERE status = 'approved'",
            fetchall=True
        )
        
        return [r[0] for r in results] if results else []
    
    def get_vehicle_locations(self):
        """Get list of all vehicle locations in use"""
        results = self.db.execute_query(
            "SELECT DISTINCT location FROM vehicles WHERE status = 'approved'",
            fetchall=True
        )
        
        return [r[0] for r in results] if results else []
    
    def get_price_range(self):
        """Get min and max price of approved vehicles"""
        result = self.db.execute_query(
            "SELECT MIN(daily_rate), MAX(daily_rate) FROM vehicles WHERE status = 'approved'",
            fetchone=True
        )
        
        if result and result[0] is not None:
            return {
                'min': result[0],
                'max': result[1]
            }
        else:
            return {
                'min': 0,
                'max': 5000  # Default max price
            }
    
    def add_to_wishlist(self, user_id, vehicle_id):
        """Add a vehicle to user's wishlist"""
        wishlist_id = str(uuid.uuid4())
        
        # Check if already in wishlist
        exists = self.db.execute_query(
            "SELECT id FROM wishlists WHERE user_id = ? AND vehicle_id = ?",
            params=(user_id, vehicle_id),
            fetchone=True
        )
        
        if exists:
            return True  # Already in wishlist
        
        result = self.db.execute_query(
            '''
            INSERT INTO wishlists (id, user_id, vehicle_id, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''',
            params=(wishlist_id, user_id, vehicle_id),
            commit=True
        )
        
        return result is not None
    
    def remove_from_wishlist(self, user_id, vehicle_id):
        """Remove a vehicle from user's wishlist"""
        result = self.db.execute_query(
            "DELETE FROM wishlists WHERE user_id = ? AND vehicle_id = ?",
            params=(user_id, vehicle_id),
            commit=True
        )
        
        return result is not None
    
    def get_wishlist(self, user_id):
        """Get user's wishlist vehicles"""
        results = self.db.execute_query(
            '''
            SELECT v.*, 
                   (SELECT image_data FROM vehicle_images 
                    WHERE vehicle_id = v.id AND is_primary = TRUE 
                    LIMIT 1) as primary_image
            FROM vehicles v
            JOIN wishlists w ON v.id = w.vehicle_id
            WHERE w.user_id = ? AND v.status = 'approved'
            ORDER BY w.created_at DESC
            ''',
            params=(user_id,),
            fetchall=True
        )
        
        if not results:
            return []
            
        # Convert to list of dictionaries
        columns = [
            'id', 'owner_id', 'brand', 'model', 'year', 'category', 'daily_rate',
            'location', 'description', 'specifications', 'available_from', 
            'available_until', 'status', 'created_at', 'updated_at', 
            'average_rating', 'total_bookings', 'is_featured', 'views',
            'primary_image'
        ]
        
        wishlist = []
        for vehicle in results:
            vehicle_dict = {columns[i]: vehicle[i] for i in range(min(len(columns), len(vehicle)))}
            wishlist.append(vehicle_dict)
            
        return wishlist
    
    def is_in_wishlist(self, user_id, vehicle_id):
        """Check if a vehicle is in user's wishlist"""
        result = self.db.execute_query(
            "SELECT id FROM wishlists WHERE user_id = ? AND vehicle_id = ?",
            params=(user_id, vehicle_id),
            fetchone=True
        )
        
        return result is not None
    
    def approve_vehicle(self, vehicle_id, admin_id, comment=None):
        """Approve a vehicle listing"""
        # First update the vehicle status
        vehicle_update = self.db.execute_query(
            "UPDATE vehicles SET status = 'approved' WHERE id = ?",
            params=(vehicle_id,),
            commit=True
        )
        
        if not vehicle_update:
            return False, "Failed to update vehicle status"
        
        # Create admin review
        review_id = str(uuid.uuid4())
        
        review_result = self.db.execute_query(
            '''
            INSERT INTO admin_reviews (id, vehicle_id, admin_id, comment, status, created_at)
            VALUES (?, ?, ?, ?, 'approved', CURRENT_TIMESTAMP)
            ''',
            params=(review_id, vehicle_id, admin_id, comment),
            commit=True
        )
        
        if not review_result:
            return False, "Failed to create admin review"
        
        # Get vehicle and owner info for notification
        vehicle = self.get_vehicle(vehicle_id, include_images=False)
        
        if vehicle:
            # Create notification for owner
            notification_manager = NotificationManager(self.db)
            notification_manager.create_notification(
                vehicle['owner_id'],
                "Vehicle Listing Approved",
                f"Your {vehicle['brand']} {vehicle['model']} has been approved and is now live.",
                "listing_approved",
                link=f"?page=vehicle_details&id={vehicle_id}",
                action_text="View Listing"
            )
        
        return True, "Vehicle listing approved successfully"
    
    def reject_vehicle(self, vehicle_id, admin_id, comment=None):
        """Reject a vehicle listing"""
        # First update the vehicle status
        vehicle_update = self.db.execute_query(
            "UPDATE vehicles SET status = 'rejected' WHERE id = ?",
            params=(vehicle_id,),
            commit=True
        )
        
        if not vehicle_update:
            return False, "Failed to update vehicle status"
        
        # Create admin review
        review_id = str(uuid.uuid4())
        
        review_result = self.db.execute_query(
            '''
            INSERT INTO admin_reviews (id, vehicle_id, admin_id, comment, status, created_at)
            VALUES (?, ?, ?, ?, 'rejected', CURRENT_TIMESTAMP)
            ''',
            params=(review_id, vehicle_id, admin_id, comment),
            commit=True
        )
        
        if not review_result:
            return False, "Failed to create admin review"
        
        # Get vehicle and owner info for notification
        vehicle = self.get_vehicle(vehicle_id, include_images=False)
        
        if vehicle:
            rejection_reason = comment if comment else "It does not meet our listing requirements."
            
            # Create notification for owner
            notification_manager = NotificationManager(self.db)
            notification_manager.create_notification(
                vehicle['owner_id'],
                "Vehicle Listing Rejected",
                f"Your {vehicle['brand']} {vehicle['model']} listing was not approved. Reason: {rejection_reason}",
                "listing_rejected",
                link=f"?page=my_listings",
                action_text="View My Listings"
            )
        
        return True, "Vehicle listing rejected successfully"
    
    def get_admin_reviews(self, vehicle_id=None, admin_id=None, status=None, limit=50, offset=0):
        """Get admin reviews with filters"""
        query = '''
            SELECT ar.*, v.brand, v.model, v.year, u.full_name as admin_name
            FROM admin_reviews ar
            JOIN vehicles v ON ar.vehicle_id = v.id
            JOIN users u ON ar.admin_id = u.id
            WHERE 1=1
        '''
        
        params = []
        
        if vehicle_id:
            query += " AND ar.vehicle_id = ?"
            params.append(vehicle_id)
            
        if admin_id:
            query += " AND ar.admin_id = ?"
            params.append(admin_id)
            
        if status:
            query += " AND ar.status = ?"
            params.append(status)
            
        query += " ORDER BY ar.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        reviews = self.db.execute_query(query, params=params, fetchall=True)
        
        if not reviews:
            return []
            
        # Convert to list of dictionaries
        columns = [
            'id', 'vehicle_id', 'admin_id', 'comment', 'status', 'created_at',
            'vehicle_brand', 'vehicle_model', 'vehicle_year', 'admin_name'
        ]
        
        result = []
        for review in reviews:
            review_dict = {columns[i]: review[i] for i in range(min(len(columns), len(review)))}
            result.append(review_dict)
            
        return result

class BookingManager:
    """Class for managing vehicle bookings"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_booking(self, user_id, vehicle_id, start_date, end_date, pickup_location,
                      return_location, has_insurance=False, has_driver=False,
                      delivery_option=None, special_requests=None, discount_code=None):
        """Create a new booking"""
        booking_id = str(uuid.uuid4())
        
        # Get vehicle details for pricing
        vehicle = self.db.execute_query(
            "SELECT daily_rate, owner_id FROM vehicles WHERE id = ?",
            params=(vehicle_id,),
            fetchone=True
        )
        
        if not vehicle:
            return False, "Vehicle not found", None
            
        daily_rate, owner_id = vehicle
        
        # Calculate booking duration in days
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        duration = (end_date_obj - start_date_obj).days + 1
        
        if duration <= 0:
            return False, "Invalid booking dates", None
        
        # Calculate base amount
        base_amount = daily_rate * duration
        
        # Calculate additional services amounts
        insurance_amount = 0
        if has_insurance:
            insurance_amount = base_amount * 0.10  # 10% of base amount
            
        driver_amount = 0
        if has_driver:
            driver_amount = 150 * duration  # AED 150 per day
            
        delivery_amount = 0
        if delivery_option:
            if delivery_option == 'standard':
                delivery_amount = 100
            elif delivery_option == 'premium':
                delivery_amount = 250
                
        # Apply discount if code provided
        discount_amount = 0
        if discount_code:
            discount = self.validate_promo_code(discount_code, base_amount, user_id)
            if discount:
                discount_amount = discount
        
        # Calculate tax (5% VAT)
        subtotal = base_amount + insurance_amount + driver_amount + delivery_amount - discount_amount
        tax_amount = subtotal * 0.05
        
        # Calculate total amount
        total_amount = subtotal + tax_amount
        
        # Create the booking
        result = self.db.execute_query(
            '''
            INSERT INTO bookings (
                id, user_id, vehicle_id, start_date, end_date, pickup_location, return_location,
                status, total_amount, created_at, updated_at, has_insurance, has_driver,
                delivery_option, special_requests, insurance_amount, driver_amount,
                delivery_amount, discount_amount, discount_code, tax_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            params=(
                booking_id, user_id, vehicle_id, start_date, end_date, pickup_location, 
                return_location, total_amount, has_insurance, has_driver, delivery_option,
                special_requests, insurance_amount, driver_amount, delivery_amount,
                discount_amount, discount_code, tax_amount
            ),
            commit=True
        )
        
        if result is None:
            return False, "Failed to create booking", None
            
        # Create notifications
        self._create_booking_notifications(booking_id, user_id, owner_id)
        
        return True, "Booking created successfully", booking_id
    
    def _create_booking_notifications(self, booking_id, user_id, owner_id):
        """Create notifications for booking"""
        # Get booking details
        booking = self.get_booking(booking_id)
        if not booking:
            return
            
        notification_manager = NotificationManager(self.db)
        
        # Notification for renter
        notification_manager.create_notification(
            user_id,
            "Booking Requested",
            f"Your booking request for {booking['vehicle_brand']} {booking['vehicle_model']} has been submitted and is pending approval.",
            "booking_created",
            link=f"?page=booking_details&id={booking_id}",
            action_text="View Booking"
        )
        
        # Notification for owner
        notification_manager.create_notification(
            owner_id,
            "New Booking Request",
            f"You have received a new booking request for your {booking['vehicle_brand']} {booking['vehicle_model']}.",
            "new_booking_request",
            link=f"?page=owner_bookings",
            action_text="View Bookings"
        )
    
    def get_booking(self, booking_id):
        """Get a booking by ID"""
        booking = self.db.execute_query(
            '''
            SELECT b.*, 
                   v.brand as vehicle_brand, 
                   v.model as vehicle_model,
                   v.year as vehicle_year,
                   v.owner_id as owner_id,
                   u.full_name as user_name,
                   u.email as user_email,
                   (SELECT image_data FROM vehicle_images 
                    WHERE vehicle_id = b.vehicle_id AND is_primary = TRUE 
                    LIMIT 1) as vehicle_image
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.id
            JOIN users u ON b.user_id = u.id
            WHERE b.id = ?
            ''',
            params=(booking_id,),
            fetchone=True
        )
        
        if not booking:
            return None
            
        # Convert to dictionary
        columns = [
            'id', 'user_id', 'vehicle_id', 'start_date', 'end_date', 
            'pickup_location', 'return_location', 'status', 'total_amount',
            'paid_amount', 'payment_status', 'created_at', 'updated_at',
            'cancellation_date', 'cancellation_reason', 'has_insurance',
            'has_driver', 'delivery_option', 'special_requests',
            'insurance_amount', 'driver_amount', 'delivery_amount',
            'vip_services_amount', 'discount_amount', 'discount_code',
            'tax_amount', 'vehicle_brand', 'vehicle_model', 'vehicle_year',
            'owner_id', 'user_name', 'user_email', 'vehicle_image'
        ]
        
        result = {columns[i]: booking[i] for i in range(min(len(columns), len(booking)))}
        
        # Calculate booking duration
        if result['start_date'] and result['end_date']:
            start_date = datetime.strptime(result['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(result['end_date'], '%Y-%m-%d').date()
            result['duration_days'] = (end_date - start_date).days + 1
        else:
            result['duration_days'] = 0
            
        return result
    
    def get_bookings(self, filters=None, sort_by='created_at', sort_order='DESC', limit=50, offset=0):
        """Get bookings with filters"""
        if filters is None:
            filters = {}
            
        query = '''
            SELECT b.*, 
                   v.brand as vehicle_brand, 
                   v.model as vehicle_model,
                   v.year as vehicle_year,
                   u.full_name as user_name,
                   (SELECT image_data FROM vehicle_images 
                    WHERE vehicle_id = b.vehicle_id AND is_primary = TRUE 
                    LIMIT 1) as vehicle_image
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.id
            JOIN users u ON b.user_id = u.id
            WHERE 1=1
        '''
        
        params = []
        
        # Add filters
        if 'user_id' in filters:
            query += " AND b.user_id = ?"
            params.append(filters['user_id'])
            
        if 'vehicle_id' in filters:
            query += " AND b.vehicle_id = ?"
            params.append(filters['vehicle_id'])
            
        if 'owner_id' in filters:
            query += " AND v.owner_id = ?"
            params.append(filters['owner_id'])
            
        if 'status' in filters:
            if isinstance(filters['status'], list):
                placeholders = ', '.join(['?' for _ in filters['status']])
                query += f" AND b.status IN ({placeholders})"
                params.extend(filters['status'])
            else:
                query += " AND b.status = ?"
                params.append(filters['status'])
                
        if 'date_from' in filters:
            query += " AND b.start_date >= ?"
            params.append(filters['date_from'])
            
        if 'date_to' in filters:
            query += " AND b.end_date <= ?"
            params.append(filters['date_to'])
            
        if 'payment_status' in filters:
            query += " AND b.payment_status = ?"
            params.append(filters['payment_status'])
            
        if 'min_total' in filters:
            query += " AND b.total_amount >= ?"
            params.append(filters['min_total'])
            
        if 'max_total' in filters:
            query += " AND b.total_amount <= ?"
            params.append(filters['max_total'])
            
        if 'search' in filters and filters['search']:
            search_term = f"%{filters['search']}%"
            query += " AND (v.brand LIKE ? OR v.model LIKE ? OR u.full_name LIKE ? OR b.id LIKE ?)"
            params.extend([search_term, search_term, search_term, search_term])
            
        # Add sorting    
        valid_sort_fields = {
            'created_at', 'start_date', 'end_date', 'total_amount', 
            'status', 'payment_status'
        }
        
        if sort_by in valid_sort_fields:
            query += f" ORDER BY b.{sort_by} {sort_order}"
        else:
            query += f" ORDER BY b.created_at DESC"
            
        # Add limit and offset
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        bookings = self.db.execute_query(query, params=params, fetchall=True)
        
        if not bookings:
            return []
            
        # Convert to list of dictionaries
        columns = [
            'id', 'user_id', 'vehicle_id', 'start_date', 'end_date', 
            'pickup_location', 'return_location', 'status', 'total_amount',
            'paid_amount', 'payment_status', 'created_at', 'updated_at',
            'cancellation_date', 'cancellation_reason', 'has_insurance',
            'has_driver', 'delivery_option', 'special_requests',
            'insurance_amount', 'driver_amount', 'delivery_amount',
            'vip_services_amount', 'discount_amount', 'discount_code',
            'tax_amount', 'vehicle_brand', 'vehicle_model', 'vehicle_year',
            'user_name', 'vehicle_image'
        ]
        
        result = []
        for booking in bookings:
            booking_dict = {columns[i]: booking[i] for i in range(min(len(columns), len(booking)))}
            
            # Calculate booking duration
            if booking_dict['start_date'] and booking_dict['end_date']:
                start_date = datetime.strptime(booking_dict['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(booking_dict['end_date'], '%Y-%m-%d').date()
                booking_dict['duration_days'] = (end_date - start_date).days + 1
            else:
                booking_dict['duration_days'] = 0
                
            result.append(booking_dict)
            
        return result
    
    def update_booking_status(self, booking_id, new_status, notes=None):
        """Update a booking status"""
        # Get current booking status
        current = self.db.execute_query(
            "SELECT status, user_id, vehicle_id FROM bookings WHERE id = ?",
            params=(booking_id,),
            fetchone=True
        )
        
        if not current:
            return False, "Booking not found"
            
        current_status, user_id, vehicle_id = current
        
        # Check if status transition is valid
        valid_transitions = {
            'pending': ['confirmed', 'rejected', 'canceled'],
            'confirmed': ['completed', 'canceled'],
            'rejected': [], # Cannot transition from rejected
            'completed': [], # Cannot transition from completed
            'canceled': []   # Cannot transition from canceled
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            return False, f"Cannot transition from '{current_status}' to '{new_status}'"
            
        # Update the booking
        update_data = {
            'status': new_status,
            'updated_at': datetime.now().isoformat()
        }
        
        # Add cancellation data if canceled
        if new_status == 'canceled':
            update_data['cancellation_date'] = datetime.now().isoformat()
            update_data['cancellation_reason'] = notes
        
        # Build update query
        set_clauses = [f"{field} = ?" for field in update_data.keys()]
        set_clause = ", ".join(set_clauses)
        
        query = f"UPDATE bookings SET {set_clause} WHERE id = ?"
        
        params = list(update_data.values())
        params.append(booking_id)
        
        result = self.db.execute_query(query, params=params, commit=True)
        
        if result is None:
            return False, "Failed to update booking status"
            
        # Create notification
        self._create_status_change_notification(booking_id, user_id, new_status, notes)
        
        # Special handling for confirmed bookings - update vehicle availability
        if new_status == 'confirmed':
            booking = self.get_booking(booking_id)
            if booking:
                # Increment total_bookings counter
                self.db.execute_query(
                    "UPDATE vehicles SET total_bookings = total_bookings + 1 WHERE id = ?",
                    params=(vehicle_id,),
                    commit=True
                )
        
        return True, f"Booking status updated to {new_status}"
    
    def _create_status_change_notification(self, booking_id, user_id, new_status, notes=None):
        """Create notification for booking status change"""
        booking = self.get_booking(booking_id)
        if not booking:
            return
            
        notification_manager = NotificationManager(self.db)
        vehicle_name = f"{booking['vehicle_brand']} {booking['vehicle_model']}"
        
        # Create message based on status
        if new_status == 'confirmed':
            title = "Booking Confirmed"
            message = f"Your booking for {vehicle_name} has been confirmed."
        elif new_status == 'rejected':
            title = "Booking Rejected"
            message = f"Your booking for {vehicle_name} has been rejected."
            if notes:
                message += f" Reason: {notes}"
        elif new_status == 'canceled':
            title = "Booking Canceled"
            message = f"Your booking for {vehicle_name} has been canceled."
            if notes:
                message += f" Reason: {notes}"
        elif new_status == 'completed':
            title = "Booking Completed"
            message = f"Your booking for {vehicle_name} has been marked as completed."
        else:
            title = "Booking Update"
            message = f"Your booking for {vehicle_name} has been updated to {new_status}."
        
        # Notify the renter
        notification_manager.create_notification(
            user_id,
            title,
            message,
            f"booking_{new_status}",
            link=f"?page=booking_details&id={booking_id}",
            action_text="View Booking"
        )
        
        # Also notify the owner
        if booking['owner_id']:
            owner_title = f"Booking {new_status.capitalize()}"
            owner_message = f"A booking for your {vehicle_name} has been {new_status}."
            
            notification_manager.create_notification(
                booking['owner_id'],
                owner_title,
                owner_message,
                f"owner_booking_{new_status}",
                link=f"?page=owner_bookings",
                action_text="View Bookings"
            )
    
    def process_payment(self, booking_id, amount, payment_method):
        """Process a payment for a booking"""
        # Get booking details
        booking = self.get_booking(booking_id)
        if not booking:
            return False, "Booking not found", None
            
        # Check payment amount doesn't exceed remaining balance
        remaining_balance = booking['total_amount'] - booking['paid_amount']
        if amount > remaining_balance:
            return False, "Payment amount exceeds remaining balance", None
            
        # Create transaction
        transaction_id = str(uuid.uuid4())
        
        transaction_result = self.db.execute_query(
            '''
            INSERT INTO transactions (
                id, user_id, booking_id, amount, transaction_type,
                payment_method, status, created_at, completed_at
            ) VALUES (?, ?, ?, ?, 'booking_payment', ?, 'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''',
            params=(
                transaction_id, booking['user_id'], booking_id, 
                amount, payment_method
            ),
            commit=True
        )
        
        if transaction_result is None:
            return False, "Failed to record transaction", None
            
        # Update booking payment status
        new_paid_amount = booking['paid_amount'] + amount
        new_payment_status = 'partially_paid'
        
        if new_paid_amount >= booking['total_amount']:
            new_payment_status = 'paid'
        
        booking_update = self.db.execute_query(
            '''
            UPDATE bookings SET 
                paid_amount = ?,
                payment_status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''',
            params=(new_paid_amount, new_payment_status, booking_id),
            commit=True
        )
        
        if booking_update is None:
            # Payment recorded but booking update failed
            return True, "Payment recorded but booking status update failed", transaction_id
        
        # Create notification
        notification_manager = NotificationManager(self.db)
        
        # Notify renter
        notification_manager.create_notification(
            booking['user_id'],
            "Payment Processed",
            f"Your payment of AED {amount:,.2f} for booking #{booking_id} has been processed.",
            "payment_processed",
            link=f"?page=booking_details&id={booking_id}",
            action_text="View Booking"
        )
        
        # Notify owner
        if booking['owner_id']:
            notification_manager.create_notification(
                booking['owner_id'],
                "Payment Received",
                f"A payment of AED {amount:,.2f} has been received for booking #{booking_id}.",
                "payment_received",
                link=f"?page=owner_bookings",
                action_text="View Bookings"
            )
        
        return True, "Payment processed successfully", transaction_id
    
    def cancel_booking(self, booking_id, user_id, reason=None):
        """Cancel a booking"""
        # Check if booking exists and belongs to user
        booking = self.db.execute_query(
            "SELECT status, user_id, vehicle_id FROM bookings WHERE id = ?",
            params=(booking_id,),
            fetchone=True
        )
        
        if not booking:
            return False, "Booking not found"
            
        status, booking_user_id, vehicle_id = booking
        
        # Check if user is the booking owner
        if booking_user_id != user_id:
            return False, "You can only cancel your own bookings"
            
        # Check if booking can be canceled
        if status not in ['pending', 'confirmed']:
            return False, f"Cannot cancel a booking with status '{status}'"
            
        # Cancel the booking
        update_result = self.db.execute_query(
            '''
            UPDATE bookings SET 
                status = 'canceled',
                cancellation_date = CURRENT_TIMESTAMP,
                cancellation_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''',
            params=(reason, booking_id),
            commit=True
        )
        
        if update_result is None:
            return False, "Failed to cancel booking"
            
        # Get full booking details for notifications
        full_booking = self.get_booking(booking_id)
        if full_booking:
            # Create notifications
            notification_manager = NotificationManager(self.db)
            vehicle_name = f"{full_booking['vehicle_brand']} {full_booking['vehicle_model']}"
            
            # Notify renter
            notification_manager.create_notification(
                user_id,
                "Booking Canceled",
                f"Your booking for {vehicle_name} has been canceled.",
                "booking_canceled",
                link=f"?page=my_bookings",
                action_text="View Bookings"
            )
            
            # Notify owner
            if full_booking['owner_id']:
                notification_manager.create_notification(
                    full_booking['owner_id'],
                    "Booking Canceled",
                    f"A booking for your {vehicle_name} has been canceled by the renter.",
                    "owner_booking_canceled",
                    link=f"?page=owner_bookings",
                    action_text="View Bookings"
                )
        
        return True, "Booking canceled successfully"
    
    def get_booking_statistics(self, user_id=None, is_owner=False, period='all'):
        """Get booking statistics for a user or the entire system"""
        # Base query
        if is_owner:
            # Stats for vehicle owner
            base_query = '''
                SELECT b.status, COUNT(*) as count, SUM(b.total_amount) as total_value
                FROM bookings b
                JOIN vehicles v ON b.vehicle_id = v.id
                WHERE v.owner_id = ?
            '''
            params = [user_id]
        elif user_id:
            # Stats for renter
            base_query = '''
                SELECT b.status, COUNT(*) as count, SUM(b.total_amount) as total_value
                FROM bookings b
                WHERE b.user_id = ?
            '''
            params = [user_id]
        else:
            # System-wide stats
            base_query = '''
                SELECT status, COUNT(*) as count, SUM(total_amount) as total_value
                FROM bookings
                WHERE 1=1
            '''
            params = []
        
        # Add time period filter
        if period != 'all':
            if period == 'today':
                base_query += " AND DATE(created_at) = DATE('now')"
            elif period == 'week':
                base_query += " AND created_at >= datetime('now', '-7 days')"
            elif period == 'month':
                base_query += " AND created_at >= datetime('now', '-1 month')"
            elif period == 'year':
                base_query += " AND created_at >= datetime('now', '-1 year')"
        
        # Group by status
        base_query += " GROUP BY status"
        
        results = self.db.execute_query(base_query, params=params, fetchall=True)
        
        if not results:
            return {
                'total_bookings': 0,
                'pending_bookings': 0,
                'confirmed_bookings': 0,
                'completed_bookings': 0,
                'canceled_bookings': 0,
                'rejected_bookings': 0,
                'total_value': 0,
                'confirmed_value': 0,
                'completed_value': 0
            }
        
        # Process results
        stats = {
            'total_bookings': 0,
            'pending_bookings': 0,
            'confirmed_bookings': 0,
            'completed_bookings': 0,
            'canceled_bookings': 0,
            'rejected_bookings': 0,
            'total_value': 0,
            'confirmed_value': 0,
            'completed_value': 0
        }
        
        for status, count, value in results:
            if value is None:
                value = 0
                
            stats['total_bookings'] += count
            stats['total_value'] += value
            
            if status == 'pending':
                stats['pending_bookings'] = count
            elif status == 'confirmed':
                stats['confirmed_bookings'] = count
                stats['confirmed_value'] = value
            elif status == 'completed':
                stats['completed_bookings'] = count
                stats['completed_value'] = value
            elif status == 'canceled':
                stats['canceled_bookings'] = count
            elif status == 'rejected':
                stats['rejected_bookings'] = count
        
        return stats
    
    def get_booking_timeline(self, booking_id):
        """Get the timeline of events for a booking"""
        booking = self.get_booking(booking_id)
        if not booking:
            return []
            
        timeline = []
        
        # Created event
        timeline.append({
            'date': booking['created_at'],
            'title': 'Booking Created',
            'description': 'Booking request was submitted',
            'status': 'completed'
        })
        
        # Status changes based on current status
        if booking['status'] == 'confirmed':
            timeline.append({
                'date': booking['updated_at'],
                'title': 'Booking Confirmed',
                'description': 'Booking was confirmed by the vehicle owner',
                'status': 'completed'
            })
            
            # Add upcoming events
            timeline.append({
                'date': booking['start_date'],
                'title': 'Pickup',
                'description': f"Pickup from {booking['pickup_location']}",
                'status': 'pending'
            })
            
            timeline.append({
                'date': booking['end_date'],
                'title': 'Return',
                'description': f"Return to {booking['return_location']}",
                'status': 'pending'
            })
            
        elif booking['status'] == 'completed':
            timeline.append({
                'date': booking['updated_at'],  # This should be the confirmation date
                'title': 'Booking Confirmed',
                'description': 'Booking was confirmed by the vehicle owner',
                'status': 'completed'
            })
            
            timeline.append({
                'date': booking['start_date'],
                'title': 'Pickup',
                'description': f"Pickup from {booking['pickup_location']}",
                'status': 'completed'
            })
            
            timeline.append({
                'date': booking['end_date'],
                'title': 'Return',
                'description': f"Return to {booking['return_location']}",
                'status': 'completed'
            })
            
            timeline.append({
                'date': booking['updated_at'],  # This should be completion date
                'title': 'Booking Completed',
                'description': 'Rental period completed successfully',
                'status': 'completed'
            })
            
        elif booking['status'] == 'rejected':
            timeline.append({
                'date': booking['updated_at'],
                'title': 'Booking Rejected',
                'description': 'Booking request was rejected by the vehicle owner',
                'status': 'canceled'
            })
            
        elif booking['status'] == 'canceled':
            timeline.append({
                'date': booking['cancellation_date'] or booking['updated_at'],
                'title': 'Booking Canceled',
                'description': booking['cancellation_reason'] or 'Booking was canceled',
                'status': 'canceled'
            })
        
        # Payment events
        if booking['payment_status'] != 'unpaid':
            # Get payment transactions
            transactions = self.db.execute_query(
                '''
                SELECT id, amount, payment_method, status, created_at, completed_at
                FROM transactions
                WHERE booking_id = ? AND transaction_type = 'booking_payment'
                ORDER BY created_at ASC
                ''',
                params=(booking_id,),
                fetchall=True
            )
            
            if transactions:
                for tx in transactions:
                    tx_id, amount, payment_method, status, created_at, completed_at = tx
                    
                    timeline.append({
                        'date': completed_at or created_at,
                        'title': 'Payment',
                        'description': f"Payment of AED {amount:,.2f} via {payment_method}",
                        'status': 'completed' if status == 'completed' else 'pending'
                    })
        
        # Sort timeline by date
        timeline.sort(key=lambda x: x['date'])
        
        return timeline
        
    def validate_promo_code(self, code, booking_amount, user_id):
        """Validate a promo code and return discount amount if valid"""
        promo = self.db.execute_query(
            '''
            SELECT id, discount_type, discount_value, start_date, end_date,
                   usage_limit, current_usage, min_booking_amount
            FROM promo_codes
            WHERE code = ? AND is_active = TRUE
            ''',
            params=(code,),
            fetchone=True
        )
        
        if not promo:
            return 0  # Invalid code
            
        promo_id, discount_type, discount_value, start_date, end_date, \
        usage_limit, current_usage, min_booking_amount = promo
        
        # Check if code is expired
        today = datetime.now().date()
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if today < start or today > end:
            return 0  # Expired or not started yet
            
        # Check usage limit
        if usage_limit and current_usage >= usage_limit:
            return 0  # Usage limit reached
            
        # Check minimum booking amount
        if booking_amount < min_booking_amount:
            return 0  # Booking amount below minimum
            
        # Check if user has already used this code
        previous_usage = self.db.execute_query(
            '''
            SELECT COUNT(*) FROM bookings
            WHERE user_id = ? AND discount_code = ?
            ''',
            params=(user_id, code),
            fetchone=True
        )
        
        if previous_usage and previous_usage[0] > 0:
            return 0  # User already used this code
            
        # Calculate discount amount
        discount_amount = 0
        if discount_type == 'percentage':
            discount_amount = booking_amount * (discount_value / 100)
        elif discount_type == 'fixed':
            discount_amount = discount_value
            
        # Increment usage counter
        self.db.execute_query(
            "UPDATE promo_codes SET current_usage = current_usage + 1 WHERE id = ?",
            params=(promo_id,),
            commit=True
        )
        
        return discount_amount

class SubscriptionManager:
    """Class for managing user subscriptions"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        
    def get_subscription_plans(self, user_type='renter'):
        """Get available subscription plans by user type"""
        if user_type == 'renter':
            return [
                {
                    'type': 'standard',
                    'name': 'Standard',
                    'price': 0,
                    'period': 'month',
                    'features': [
                        'Standard service fees (15%)',
                        'Basic customer support',
                        'Access to standard vehicles',
                        'Regular search results visibility',
                        'Standard booking process'
                    ]
                },
                {
                    'type': 'premium',
                    'name': 'Premium',
                    'price': 199,
                    'period': 'month',
                    'features': [
                        'Reduced service fees (10%)',
                        'Priority customer support',
                        'Access to premium vehicles',
                        'Free cancellations (up to 24h before)',
                        'Discounts up to 10% on bookings',
                        'Priority in search results',
                        'Dedicated account manager'
                    ]
                },
                {
                    'type': 'elite',
                    'name': 'Elite',
                    'price': 499,
                    'period': 'month',
                    'features': [
                        'Minimal service fees (5%)',
                        '24/7 premium customer support',
                        'Access to elite and exotic vehicles',
                        'Free cancellations (anytime)',
                        'Discounts up to 20% on bookings',
                        'Top priority in search results',
                        'Complimentary airport pickup',
                        'Personal concierge service',
                        'Exclusive events and experiences',
                        'Free upgrades when available'
                    ]
                }
            ]
        elif user_type == 'owner':
            return [
                {
                    'type': 'standard',
                    'name': 'Standard Host',
                    'price': 0,
                    'period': 'month',
                    'features': [
                        'Standard listing visibility',
                        'Standard commission fees (15%)',
                        'Basic vehicle protection',
                        'Standard payout schedule (5 days)',
                        'Basic customer support',
                        'Up to 3 active listings'
                    ]
                },
                {
                    'type': 'premium',
                    'name': 'Premium Host',
                    'price': 299,
                    'period': 'month',
                    'features': [
                        'Enhanced listing visibility',
                        'Reduced commission fees (10%)',
                        'Enhanced vehicle protection',
                        'Faster payouts (2 days)',
                        'Priority customer support',
                        'Professional photoshoot for 1 vehicle',
                        'Up to 10 active listings',
                        'Featured listings rotation'
                    ]
                },
                {
                    'type': 'elite',
                    'name': 'Elite Host',
                    'price': 799,
                    'period': 'month',
                    'features': [
                        'Top listing visibility',
                        'Minimal commission fees (5%)',
                        'Premium vehicle protection',
                        'Same-day payouts',
                        '24/7 dedicated support',
                        'Professional photoshoot for all vehicles',
                        'Unlimited active listings',
                        'Permanent featured listings',
                        'Marketing promotion package',
                        'Elite host badge',
                        'Dedicated account manager'
                    ]
                }
            ]
        else:
            return []
    
    def subscribe_user(self, user_id, plan_type, duration_months=1, payment_method='credit_card', auto_renew=False):
        """Subscribe a user to a plan"""
        # Validate plan type
        valid_plans = ['standard', 'premium', 'elite']
        if plan_type not in valid_plans:
            return False, "Invalid subscription plan"
            
        # Get plan price
        plan_price = 0
        if plan_type == 'premium':
            plan_price = 199  # Update with actual prices
        elif plan_type == 'elite':
            plan_price = 499  # Update with actual prices
            
        total_amount = plan_price * duration_months
        
        # Calculate subscription dates
        start_date = datetime.now().date()
        end_date = start_date + relativedelta(months=duration_months)
        
        # Create subscription record
        subscription_id = str(uuid.uuid4())
        
        result = self.db.execute_query(
            '''
            INSERT INTO subscriptions (
                id, user_id, plan_type, start_date, end_date, amount_paid,
                auto_renew, status, created_at, payment_method
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP, ?)
            ''',
            params=(
                subscription_id, user_id, plan_type, start_date.isoformat(),
                end_date.isoformat(), total_amount, auto_renew, payment_method
            ),
            commit=True
        )
        
        if result is None:
            return False, "Failed to create subscription"
            
        # Update user subscription info
        user_update = self.db.execute_query(
            '''
            UPDATE users SET 
                subscription_type = ?,
                subscription_expiry = ?
            WHERE id = ?
            ''',
            params=(plan_type, end_date.isoformat(), user_id),
            commit=True
        )
        
        if user_update is None:
            return False, "Subscription created but user profile update failed"
            
        # Create transaction record if paid plan
        if total_amount > 0:
            transaction_id = str(uuid.uuid4())
            
            transaction_result = self.db.execute_query(
                '''
                INSERT INTO transactions (
                    id, user_id, subscription_id, amount, transaction_type,
                    payment_method, status, created_at, completed_at
                ) VALUES (?, ?, ?, ?, 'subscription_payment', ?, 'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''',
                params=(
                    transaction_id, user_id, subscription_id, 
                    total_amount, payment_method
                ),
                commit=True
            )
            
            if transaction_result is None:
                return True, "Subscription activated but payment record failed"
        
        # Create notification
        notification_manager = NotificationManager(self.db)
        notification_manager.create_notification(
            user_id,
            "Subscription Activated",
            f"Your {plan_type.capitalize()} plan has been activated until {end_date.strftime('%B %d, %Y')}.",
            "subscription_activated",
            link="?page=subscription",
            action_text="View Subscription"
        )
        
        return True, "Subscription activated successfully"
    
    def get_user_subscription(self, user_id):
        """Get current user subscription details"""
        # Get user subscription info
        user = self.db.execute_query(
            "SELECT subscription_type, subscription_expiry FROM users WHERE id = ?",
            params=(user_id,),
            fetchone=True
        )
        
        if not user or not user[0] or not user[1]:
            return {
                'type': 'standard',
                'expiry': None,
                'is_active': True,
                'days_remaining': 0,
                'auto_renew': False
            }
            
        subscription_type, expiry = user
        
        # Get latest subscription record
        subscription = self.db.execute_query(
            '''
            SELECT id, start_date, end_date, amount_paid, auto_renew, 
                   status, created_at
            FROM subscriptions
            WHERE user_id = ? AND plan_type = ? AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
            ''',
            params=(user_id, subscription_type),
            fetchone=True
        )
        
        if not subscription:
            return {
                'type': subscription_type,
                'expiry': expiry,
                'is_active': False,
                'days_remaining': 0,
                'auto_renew': False
            }
            
        sub_id, start_date, end_date, amount_paid, auto_renew, status, created_at = subscription
        
        # Calculate days remaining
        today = datetime.now().date()
        expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date()
        days_remaining = (expiry_date - today).days
        
        return {
            'id': sub_id,
            'type': subscription_type,
            'expiry': expiry,
            'is_active': days_remaining >= 0 and status == 'active',
            'days_remaining': max(0, days_remaining),
            'auto_renew': bool(auto_renew),
            'amount_paid': amount_paid,
            'start_date': start_date,
            'created_at': created_at
        }
    
    def cancel_subscription(self, user_id, subscription_id, reason=None):
        """Cancel a subscription (will remain active until expiry)"""
        # Verify subscription belongs to user
        subscription = self.db.execute_query(
            "SELECT id, plan_type, status FROM subscriptions WHERE id = ? AND user_id = ?",
            params=(subscription_id, user_id),
            fetchone=True
        )
        
        if not subscription:
            return False, "Subscription not found or doesn't belong to user"
            
        _, plan_type, status = subscription
        
        if status != 'active':
            return False, "Only active subscriptions can be canceled"
            
        # Update subscription
        update_result = self.db.execute_query(
            '''
            UPDATE subscriptions 
            SET status = 'canceled', 
                auto_renew = FALSE,
                canceled_at = CURRENT_TIMESTAMP,
                cancellation_reason = ?
            WHERE id = ?
            ''',
            params=(reason, subscription_id),
            commit=True
        )
        
        if update_result is None:
            return False, "Failed to cancel subscription"
            
        # Create notification
        notification_manager = NotificationManager(self.db)
        notification_manager.create_notification(
            user_id,
            "Subscription Canceled",
            f"Your {plan_type.capitalize()} subscription has been canceled. You'll continue to enjoy benefits until your current billing cycle ends.",
            "subscription_canceled",
            link="?page=subscription",
            action_text="View Details"
        )
        
        return True, "Subscription canceled successfully"
    
    def check_expired_subscriptions(self):
        """Check and update expired subscriptions"""
        today = datetime.now().date().isoformat()
        
        # Find users with expired subscriptions
        expired_users = self.db.execute_query(
            '''
            SELECT id, email, subscription_type, subscription_expiry 
            FROM users 
            WHERE subscription_type != 'standard'
              AND subscription_expiry < ?
            ''',
            params=(today,),
            fetchall=True
        )
        
        if not expired_users:
            return 0
            
        updated_count = 0
        notification_manager = NotificationManager(self.db)
        
        for user in expired_users:
            user_id, email, sub_type, expiry = user
            
            # Check if auto-renewal is enabled
            latest_subscription = self.db.execute_query(
                '''
                SELECT id, auto_renew FROM subscriptions
                WHERE user_id = ? AND plan_type = ? AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
                ''',
                params=(user_id, sub_type),
                fetchone=True
            )
            
            if latest_subscription and latest_subscription[1]:
                # Auto-renew subscription
                sub_id = latest_subscription[0]
                self.db.execute_query(
                    "UPDATE subscriptions SET status = 'completed' WHERE id = ?",
                    params=(sub_id,),
                    commit=True
                )
                
                # Create new subscription for next period
                success, _ = self.subscribe_user(
                    user_id, sub_type, 
                    duration_months=1, 
                    payment_method='auto_renewal',
                    auto_renew=True
                )
                
                if success:
                    updated_count += 1
                    
                    # Notification for auto-renewal
                    notification_manager.create_notification(
                        user_id,
                        "Subscription Auto-Renewed",
                        f"Your {sub_type.capitalize()} subscription has been automatically renewed for another month.",
                        "subscription_renewed",
                        link="?page=subscription",
                        action_text="View Subscription"
                    )
            else:
                # Downgrade to standard
                self.db.execute_query(
                    '''
                    UPDATE users 
                    SET subscription_type = 'standard',
                        subscription_expiry = NULL
                    WHERE id = ?
                    ''',
                    params=(user_id,),
                    commit=True
                )
                
                updated_count += 1
                
                # Mark subscription as expired
                if latest_subscription:
                    self.db.execute_query(
                        "UPDATE subscriptions SET status = 'expired' WHERE id = ?",
                        params=(latest_subscription[0],),
                        commit=True
                    )
                
                # Notification for expiration
                notification_manager.create_notification(
                    user_id,
                    "Subscription Expired",
                    f"Your {sub_type.capitalize()} subscription has expired. You've been downgraded to Standard plan.",
                    "subscription_expired",
                    link="?page=subscription",
                    action_text="Renew Subscription"
                )
        
        return updated_count

class InsuranceClaimManager:
    """Class for managing insurance claims"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def submit_claim(self, user_id, booking_id, incident_date, description, damage_type, claim_amount, evidence_files=None):
        """Submit a new insurance claim"""
        # Verify booking exists and belongs to user
        booking = self.db.execute_query(
            "SELECT id, has_insurance, status FROM bookings WHERE id = ? AND user_id = ?",
            params=(booking_id, user_id),
            fetchone=True
        )
        
        if not booking:
            return False, "Booking not found or doesn't belong to you", None
            
        booking_id, has_insurance, booking_status = booking
        
        # Check if insurance was included in booking
        if not has_insurance:
            return False, "This booking doesn't include insurance coverage", None
            
        # Check if booking is completed or confirmed
        if booking_status not in ['confirmed', 'completed']:
            return False, f"Cannot file a claim for a booking with status '{booking_status}'", None
            
        # Create claim
        claim_id = str(uuid.uuid4())
        claim_date = datetime.now().date().isoformat()
        
        result = self.db.execute_query(
            '''
            INSERT INTO insurance_claims (
                id, booking_id, user_id, incident_date, claim_date,
                description, damage_type, claim_amount, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''',
            params=(
                claim_id, booking_id, user_id, incident_date, claim_date,
                description, damage_type, claim_amount
            ),
            commit=True
        )
        
        if result is None:
            return False, "Failed to submit claim", None
            
        # Add evidence files if provided
        if evidence_files:
            for file_data in evidence_files:
                evidence_id = str(uuid.uuid4())
                
                evidence_result = self.db.execute_query(
                    '''
                    INSERT INTO claim_evidence (
                        id, claim_id, file_data, file_type, created_at
                    ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''',
                    params=(
                        evidence_id, claim_id, 
                        file_data.get('data'), 
                        file_data.get('type', 'image/jpeg')
                    ),
                    commit=True
                )
                
                if evidence_result is None:
                    # Continue even if some evidence files fail to upload
                    continue
        
        # Create notifications
        notification_manager = NotificationManager(self.db)
        
        # Notify user
        notification_manager.create_notification(
            user_id,
            "Insurance Claim Submitted",
            f"Your insurance claim for AED {claim_amount:,.2f} has been submitted and is pending review.",
            "claim_submitted",
            link=f"?page=claim_details&id={claim_id}",
            action_text="View Claim"
        )
        
        # Notify admin (using a generic admin ID or get actual admin IDs)
        admin_users = self.db.execute_query(
            "SELECT id FROM users WHERE role = 'admin' LIMIT 1",
            fetchall=True
        )
        
        if admin_users:
            for admin in admin_users:
                notification_manager.create_notification(
                    admin[0],
                    "New Insurance Claim",
                    f"A new insurance claim for AED {claim_amount:,.2f} has been submitted and requires review.",
                    "admin_new_claim",
                    link=f"?page=admin_claims&id={claim_id}",
                    action_text="Review Claim",
                    priority="high"
                )
        
        return True, "Claim submitted successfully", claim_id
    
    def get_claim(self, claim_id, include_evidence=True):
        """Get claim details by ID"""
        claim = self.db.execute_query(
            '''
            SELECT ic.*, 
                   u.full_name as user_name,
                   b.vehicle_id,
                   v.brand as vehicle_brand,
                   v.model as vehicle_model,
                   v.year as vehicle_year
            FROM insurance_claims ic
            JOIN users u ON ic.user_id = u.id
            JOIN bookings b ON ic.booking_id = b.id
            JOIN vehicles v ON b.vehicle_id = v.id
            WHERE ic.id = ?
            ''',
            params=(claim_id,),
            fetchone=True
        )
        
        if not claim:
            return None
            
        # Convert to dictionary
        columns = [
            'id', 'booking_id', 'user_id', 'incident_date', 'claim_date',
            'description', 'damage_type', 'claim_amount', 'status',
            'admin_notes', 'processed_by', 'processed_date', 'evidence_files',
            'created_at', 'updated_at', 'user_name', 'vehicle_id',
            'vehicle_brand', 'vehicle_model', 'vehicle_year'
        ]
        
        claim_dict = {columns[i]: claim[i] for i in range(min(len(columns), len(claim)))}
        
        # Get evidence files if requested
        if include_evidence:
            evidence = self.db.execute_query(
                "SELECT id, file_data, file_type, created_at FROM claim_evidence WHERE claim_id = ?",
                params=(claim_id,),
                fetchall=True
            )
            
            evidence_files = []
            if evidence:
                for file in evidence:
                    evidence_files.append({
                        'id': file[0],
                        'data': file[1],
                        'type': file[2],
                        'created_at': file[3]
                    })
                    
            claim_dict['evidence_files'] = evidence_files
            
        return claim_dict
    
    def get_claims(self, filters=None, sort_by='created_at', sort_order='DESC', limit=50, offset=0):
        """Get claims with filters"""
        if filters is None:
            filters = {}
            
        query = '''
            SELECT ic.*, 
                   u.full_name as user_name,
                   v.brand as vehicle_brand,
                   v.model as vehicle_model,
                   v.year as vehicle_year
            FROM insurance_claims ic
            JOIN users u ON ic.user_id = u.id
            JOIN bookings b ON ic.booking_id = b.id
            JOIN vehicles v ON b.vehicle_id = v.id
            WHERE 1=1
        '''
        
        params = []
        
        # Add filters
        if 'user_id' in filters:
            query += " AND ic.user_id = ?"
            params.append(filters['user_id'])
            
        if 'booking_id' in filters:
            query += " AND ic.booking_id = ?"
            params.append(filters['booking_id'])
            
        if 'status' in filters:
            if isinstance(filters['status'], list):
                placeholders = ', '.join(['?' for _ in filters['status']])
                query += f" AND ic.status IN ({placeholders})"
                params.extend(filters['status'])
            else:
                query += " AND ic.status = ?"
                params.append(filters['status'])
                
        if 'processed_by' in filters:
            query += " AND ic.processed_by = ?"
            params.append(filters['processed_by'])
            
        if 'vehicle_id' in filters:
            query += " AND b.vehicle_id = ?"
            params.append(filters['vehicle_id'])
            
        if 'min_amount' in filters:
            query += " AND ic.claim_amount >= ?"
            params.append(filters['min_amount'])
            
        if 'max_amount' in filters:
            query += " AND ic.claim_amount <= ?"
            params.append(filters['max_amount'])
            
        if 'date_from' in filters:
            query += " AND ic.incident_date >= ?"
            params.append(filters['date_from'])
            
        if 'date_to' in filters:
            query += " AND ic.incident_date <= ?"
            params.append(filters['date_to'])
            
        if 'search' in filters and filters['search']:
            search_term = f"%{filters['search']}%"
            query += " AND (ic.description LIKE ? OR u.full_name LIKE ? OR v.brand LIKE ? OR v.model LIKE ?)"
            params.extend([search_term, search_term, search_term, search_term])
            
        # Add sorting
        valid_sort_fields = {
            'created_at', 'incident_date', 'claim_date', 'claim_amount', 
            'status', 'updated_at'
        }
        
        if sort_by in valid_sort_fields:
            query += f" ORDER BY ic.{sort_by} {sort_order}"
        else:
            query += f" ORDER BY ic.created_at DESC"
            
        # Add limit and offset
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        claims = self.db.execute_query(query, params=params, fetchall=True)
        
        if not claims:
            return []
            
        # Convert to list of dictionaries
        columns = [
            'id', 'booking_id', 'user_id', 'incident_date', 'claim_date',
            'description', 'damage_type', 'claim_amount', 'status',
            'admin_notes', 'processed_by', 'processed_date', 'evidence_files',
            'created_at', 'updated_at', 'user_name', 'vehicle_brand',
            'vehicle_model', 'vehicle_year'
        ]
        
        result = []
        for claim in claims:
            claim_dict = {columns[i]: claim[i] for i in range(min(len(columns), len(claim)))}
            result.append(claim_dict)
            
        return result
    
    def process_claim(self, claim_id, admin_id, new_status, admin_notes=None):
        """Process an insurance claim"""
        # Verify claim exists and is pending
        claim = self.db.execute_query(
            "SELECT status, user_id FROM insurance_claims WHERE id = ?",
            params=(claim_id,),
            fetchone=True
        )
        
        if not claim:
            return False, "Claim not found"
            
        current_status, user_id = claim
        
        if current_status != 'pending':
            return False, f"Claim has already been processed as '{current_status}'"
            
        # Validate new status
        valid_statuses = ['approved', 'partially_approved', 'rejected']
        if new_status not in valid_statuses:
            return False, f"Invalid status: {new_status}"
            
        # Process the claim
        processed_date = datetime.now().isoformat()
        
        update_result = self.db.execute_query(
            '''
            UPDATE insurance_claims 
            SET status = ?,
                admin_notes = ?,
                processed_by = ?,
                processed_date = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''',
            params=(new_status, admin_notes, admin_id, processed_date, claim_id),
            commit=True
        )
        
        if update_result is None:
            return False, "Failed to update claim"
            
        # Create notification for user
        notification_manager = NotificationManager(self.db)
        
        status_message = {
            'approved': "Your insurance claim has been approved.",
            'partially_approved': "Your insurance claim has been partially approved.",
            'rejected': "Your insurance claim has been rejected."
        }
        
        notification_manager.create_notification(
            user_id,
            f"Claim {new_status.replace('_', ' ').title()}",
            status_message.get(new_status, f"Your claim status is now: {new_status}") + 
            (f" Note: {admin_notes}" if admin_notes else ""),
            f"claim_{new_status}",
            link=f"?page=claim_details&id={claim_id}",
            action_text="View Claim Details"
        )
        
        return True, f"Claim has been {new_status}"
    
    def add_evidence(self, claim_id, file_data, file_type='image/jpeg'):
        """Add evidence to an existing claim"""
        # Verify claim exists and is still pending
        claim = self.db.execute_query(
            "SELECT status FROM insurance_claims WHERE id = ?",
            params=(claim_id,),
            fetchone=True
        )
        
        if not claim:
            return False, "Claim not found"
            
        if claim[0] != 'pending':
            return False, "Cannot add evidence to a processed claim"
            
        # Add the evidence
        evidence_id = str(uuid.uuid4())
        
        result = self.db.execute_query(
            '''
            INSERT INTO claim_evidence (
                id, claim_id, file_data, file_type, created_at
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''',
            params=(evidence_id, claim_id, file_data, file_type),
            commit=True
        )
        
        if result is None:
            return False, "Failed to add evidence"
            
        # Update claim's updated_at timestamp
        self.db.execute_query(
            "UPDATE insurance_claims SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            params=(claim_id,),
            commit=True
        )
        
        return True, "Evidence added successfully"
    
    def get_claim_statistics(self, admin_id=None, period='all'):
        """Get statistics about insurance claims"""
        # Base query
        base_query = '''
            SELECT status, COUNT(*) as count, SUM(claim_amount) as total_value
            FROM insurance_claims
            WHERE 1=1
        '''
        
        params = []
        
        # Add admin filter if provided
        if admin_id:
            base_query += " AND processed_by = ?"
            params.append(admin_id)
            
        # Add time period filter
        if period != 'all':
            if period == 'today':
                base_query += " AND DATE(created_at) = DATE('now')"
            elif period == 'week':
                base_query += " AND created_at >= datetime('now', '-7 days')"
            elif period == 'month':
                base_query += " AND created_at >= datetime('now', '-1 month')"
            elif period == 'year':
                base_query += " AND created_at >= datetime('now', '-1 year')"
                
        # Group by status
        base_query += " GROUP BY status"
        
        results = self.db.execute_query(base_query, params=params, fetchall=True)
        
        if not results:
            return {
                'total_claims': 0,
                'pending_claims': 0,
                'approved_claims': 0,
                'partially_approved_claims': 0,
                'rejected_claims': 0,
                'total_claimed_amount': 0,
                'approved_amount': 0
            }
            
        # Process results
        stats = {
            'total_claims': 0,
            'pending_claims': 0,
            'approved_claims': 0,
            'partially_approved_claims': 0,
            'rejected_claims': 0,
            'total_claimed_amount': 0,
            'approved_amount': 0
        }
        
        for status, count, value in results:
            if value is None:
                value = 0
                
            stats['total_claims'] += count
            stats['total_claimed_amount'] += value
            
            if status == 'pending':
                stats['pending_claims'] = count
            elif status == 'approved':
                stats['approved_claims'] = count
                stats['approved_amount'] += value
            elif status == 'partially_approved':
                stats['partially_approved_claims'] = count
                stats['approved_amount'] += value * 0.5  # Estimate 50% approval for partial claims
            elif status == 'rejected':
                stats['rejected_claims'] = count
                
        return stats

class AnalyticsManager:
    """Class for tracking and retrieving analytics data"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        
    def track_event(self, event_type, user_id=None, event_data=None, device_info=None, ip_address=None):
        """Track an analytics event"""
        event_id = str(uuid.uuid4())
        
        # Convert event_data to JSON if it's a dict
        if isinstance(event_data, dict):
            event_data = json.dumps(event_data)
            
        # Convert device_info to JSON if it's a dict
        if isinstance(device_info, dict):
            device_info = json.dumps(device_info)
        
        result = self.db.execute_query(
            '''
            INSERT INTO analytics_events (
                id, user_id, event_type, event_data, 
                device_info, ip_address, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''',
            params=(
                event_id, user_id, event_type, 
                event_data, device_info, ip_address
            ),
            commit=True
        )
        
        return result is not None
    
    def get_event_counts(self, event_type=None, user_id=None, from_date=None, to_date=None):
        """Get count of events by type"""
        query = "SELECT event_type, COUNT(*) FROM analytics_events WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
            
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
            
        if from_date:
            query += " AND timestamp >= ?"
            params.append(from_date)
            
        if to_date:
            query += " AND timestamp <= ?"
            params.append(to_date)
            
        query += " GROUP BY event_type ORDER BY COUNT(*) DESC"
        
        results = self.db.execute_query(query, params=params, fetchall=True)
        
        if not results:
            return {}
            
        return {event: count for event, count in results}
    
    def get_user_counts(self, period='day', from_date=None, to_date=None):
        """Get user counts over time"""
        # Define period format
        period_format = '%Y-%m-%d'
        if period == 'month':
            period_format = '%Y-%m'
        elif period == 'year':
            period_format = '%Y'
        elif period == 'hour':
            period_format = '%Y-%m-%d %H:00'
            
        query = f'''
            SELECT 
                strftime('{period_format}', created_at) as period,
                COUNT(*) as count
            FROM users
            WHERE 1=1
        '''
        
        params = []
        
        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date)
            
        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date)
            
        query += " GROUP BY period ORDER BY period"
        
        results = self.db.execute_query(query, params=params, fetchall=True)
        
        if not results:
            return {}
            
        return {period: count for period, count in results}
    
    def get_vehicle_stats(self, period='day', category=None, location=None):
        """Get vehicle listing and view statistics"""
        # Define period format
        period_format = '%Y-%m-%d'
        if period == 'month':
            period_format = '%Y-%m'
        elif period == 'year':
            period_format = '%Y'
            
        # Build query for new listings
        listings_query = f'''
            SELECT 
                strftime('{period_format}', created_at) as period,
                COUNT(*) as count
            FROM vehicles
            WHERE 1=1
        '''
        
        listings_params = []
        
        if category:
            listings_query += " AND category = ?"
            listings_params.append(category)
            
        if location:
            listings_query += " AND location = ?"
            listings_params.append(location)
            
        listings_query += " GROUP BY period ORDER BY period"
        
        listings_results = self.db.execute_query(listings_query, params=listings_params, fetchall=True)
        
        # Build query for views (from analytics events)
        views_query = f'''
            SELECT 
                strftime('{period_format}', timestamp) as period,
                COUNT(*) as count
            FROM analytics_events
            WHERE event_type = 'vehicle_view'
        '''
        
        views_params = []
        
        if category or location:
            views_query += " AND event_data LIKE ?"
            
            filter_parts = []
            if category:
                filter_parts.append(f'"category":"{category}"')
            if location:
                filter_parts.append(f'"location":"{location}"')
                
            filter_pattern = '%' + '%'.join(filter_parts) + '%'
            views_params.append(filter_pattern)
            
        views_query += " GROUP BY period ORDER BY period"
        
        views_results = self.db.execute_query(views_query, params=views_params, fetchall=True)
        
        # Combine results
        stats = {
            'listings': {period: count for period, count in listings_results} if listings_results else {},
            'views': {period: count for period, count in views_results} if views_results else {}
        }
        
        return stats
    
    def get_booking_stats(self, period='day', user_type=None, user_id=None):
        """Get booking statistics over time"""
        # Define period format
        period_format = '%Y-%m-%d'
        if period == 'month':
            period_format = '%Y-%m'
        elif period == 'year':
            period_format = '%Y'
            
        # Base query
        query = f'''
            SELECT 
                strftime('{period_format}', created_at) as period,
                COUNT(*) as count,
                SUM(total_amount) as value
            FROM bookings
            WHERE 1=1
        '''
        
        params = []
        
        # Filter by user role
        if user_type == 'renter' and user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        elif user_type == 'owner' and user_id:
            query += " AND vehicle_id IN (SELECT id FROM vehicles WHERE owner_id = ?)"
            params.append(user_id)
            
        query += " GROUP BY period ORDER BY period"
        
        results = self.db.execute_query(query, params=params, fetchall=True)
        
        if not results:
            return {}
            
        stats = {}
        for period, count, value in results:
            stats[period] = {
                'count': count,
                'value': value if value is not None else 0
            }
            
        return stats
    
    def get_popular_locations(self, limit=5):
        """Get most popular locations based on bookings"""
        query = '''
            SELECT 
                b.pickup_location,
                COUNT(*) as booking_count
            FROM bookings b
            WHERE b.status IN ('confirmed', 'completed')
            GROUP BY b.pickup_location
            ORDER BY booking_count DESC
            LIMIT ?
        '''
        
        results = self.db.execute_query(query, params=(limit,), fetchall=True)
        
        if not results:
            return []
            
        return [{'location': location, 'count': count} for location, count in results]
    
    def get_popular_vehicles(self, limit=5, period=None):
        """Get most popular vehicles based on bookings"""
        query = '''
            SELECT 
                v.id,
                v.brand,
                v.model,
                v.year,
                v.category,
                COUNT(b.id) as booking_count,
                SUM(b.total_amount) as revenue,
                (SELECT image_data FROM vehicle_images 
                 WHERE vehicle_id = v.id AND is_primary = TRUE 
                 LIMIT 1) as image
            FROM vehicles v
            JOIN bookings b ON v.id = b.vehicle_id
            WHERE b.status IN ('confirmed', 'completed')
        '''
        
        params = []
        
        if period:
            if period == 'week':
                query += " AND b.created_at >= datetime('now', '-7 days')"
            elif period == 'month':
                query += " AND b.created_at >= datetime('now', '-1 month')"
            elif period == 'year':
                query += " AND b.created_at >= datetime('now', '-1 year')"
                
        query += '''
            GROUP BY v.id
            ORDER BY booking_count DESC, revenue DESC
            LIMIT ?
        '''
        
        params.append(limit)
        
        results = self.db.execute_query(query, params=params, fetchall=True)
        
        if not results:
            return []
            
        popular = []
        for vehicle_id, brand, model, year, category, booking_count, revenue, image in results:
            popular.append({
                'id': vehicle_id,
                'brand': brand,
                'model': model,
                'year': year,
                'category': category,
                'booking_count': booking_count,
                'revenue': revenue if revenue is not None else 0,
                'image': image
            })
            
        return popular
    
    def get_user_growth(self, period='month', months=12):
        """Get user growth over time"""
        # For month period, get data for last X months
        if period == 'month':
            query = '''
                SELECT 
                    strftime('%Y-%m', created_at) as month,
                    COUNT(*) as new_users
                FROM users
                WHERE created_at >= datetime('now', ?)
                GROUP BY month
                ORDER BY month
            '''
            
            date_param = f'-{months} months'
            results = self.db.execute_query(query, params=(date_param,), fetchall=True)
            
            if not results:
                return []
                
            # Fill in missing months with zeros
            all_months = []
            today = datetime.now()
            for i in range(months-1, -1, -1):
                month_date = today - relativedelta(months=i)
                month_str = month_date.strftime('%Y-%m')
                all_months.append(month_str)
                
            growth_data = {month: 0 for month in all_months}
            
            for month, count in results:
                if month in growth_data:
                    growth_data[month] = count
                    
            return [{'period': month, 'count': growth_data[month]} for month in all_months]
            
        # For day period, get data for last X days
        elif period == 'day':
            days = months * 30  # Approximate, just to reuse the parameter
            query = '''
                SELECT 
                    DATE(created_at) as day,
                    COUNT(*) as new_users
                FROM users
                WHERE created_at >= datetime('now', ?)
                GROUP BY day
                ORDER BY day
            '''
            
            date_param = f'-{days} days'
            results = self.db.execute_query(query, params=(date_param,), fetchall=True)
            
            if not results:
                return []
                
            # Fill in missing days with zeros
            all_days = []
            today = datetime.now()
            for i in range(days-1, -1, -1):
                day_date = today - timedelta(days=i)
                day_str = day_date.strftime('%Y-%m-%d')
                all_days.append(day_str)
                
            growth_data = {day: 0 for day in all_days}
            
            for day, count in results:
                if day in growth_data:
                    growth_data[day] = count
                    
            return [{'period': day, 'count': growth_data[day]} for day in all_days]
        
        return []
    
    def get_revenue_data(self, period='month', months=12, user_id=None, is_owner=False):
        """Get revenue data over time"""
        # Base query
        if is_owner:
            base_query = '''
                SELECT 
                    strftime(?, created_at) as period,
                    SUM(b.total_amount) as revenue,
                    COUNT(*) as bookings
                FROM bookings b
                JOIN vehicles v ON b.vehicle_id = v.id
                WHERE v.owner_id = ?
                  AND b.status IN ('confirmed', 'completed')
                  AND b.created_at >= datetime('now', ?)
            '''
            group_params = []
            
            if period == 'month':
                period_format = '%Y-%m'
                date_param = f'-{months} months'
            elif period == 'day':
                period_format = '%Y-%m-%d'
                date_param = f'-{months*30} days'  # Approximate
            else:
                period_format = '%Y'
                date_param = f'-{months} months'
                
            group_params = [period_format, user_id, date_param]
            
        else:
            base_query = '''
                SELECT 
                    strftime(?, created_at) as period,
                    SUM(total_amount) as revenue,
                    COUNT(*) as bookings
                FROM bookings
                WHERE status IN ('confirmed', 'completed')
                  AND created_at >= datetime('now', ?)
            '''
            
            group_params = []
            
            if period == 'month':
                period_format = '%Y-%m'
                date_param = f'-{months} months'
            elif period == 'day':
                period_format = '%Y-%m-%d'
                date_param = f'-{months*30} days'  # Approximate
            else:
                period_format = '%Y'
                date_param = f'-{months} months'
                
            group_params = [period_format, date_param]
            
            if user_id:
                base_query += " AND user_id = ?"
                group_params.append(user_id)
                
        base_query += " GROUP BY period ORDER BY period"
        
        results = self.db.execute_query(base_query, params=group_params, fetchall=True)
        
        if not results:
            return []
            
        # Generate all periods for consistent data
        all_periods = []
        today = datetime.now()
        
        if period == 'month':
            for i in range(months-1, -1, -1):
                period_date = today - relativedelta(months=i)
                period_str = period_date.strftime('%Y-%m')
                all_periods.append(period_str)
        elif period == 'day':
            days = months * 30  # Approximate
            for i in range(days-1, -1, -1):
                period_date = today - timedelta(days=i)
                period_str = period_date.strftime('%Y-%m-%d')
                all_periods.append(period_str)
        else:  # year
            for i in range(months//12, 0, -1):
                period_date = today - relativedelta(years=i)
                period_str = period_date.strftime('%Y')
                all_periods.append(period_str)
                
        # Fill in data
        revenue_data = {p: {'revenue': 0, 'bookings': 0} for p in all_periods}
        
        for period_str, revenue, bookings in results:
            if period_str in revenue_data:
                revenue_data[period_str] = {
                    'revenue': revenue if revenue is not None else 0,
                    'bookings': bookings
                }
                
        return [
            {
                'period': period_str,
                'revenue': revenue_data[period_str]['revenue'],
                'bookings': revenue_data[period_str]['bookings']
            }
            for period_str in all_periods
        ]

# Application Routes
class RouteManager:
    """Manager for page routing and state management"""
    
    def __init__(self):
        self.routes = {
            'welcome': self.welcome_page,
            'login': self.login_page,
            'signup': self.signup_page,
            'browse_vehicles': self.browse_vehicles_page,
            'vehicle_details': self.vehicle_details_page,
            'book_vehicle': self.book_vehicle_page,
            'my_bookings': self.my_bookings_page,
            'my_vehicles': self.my_vehicles_page,
            'list_vehicle': self.list_vehicle_page,
            'owner_bookings': self.owner_bookings_page,
            'profile': self.profile_page,
            'subscription': self.subscription_page,
            'insurance_claims': self.insurance_claims_page,
            'claim_details': self.claim_details_page,
            'wishlist': self.wishlist_page,
            'notifications': self.notifications_page,
            'admin_dashboard': self.admin_dashboard_page,
            'admin_vehicles': self.admin_vehicles_page,
            'admin_bookings': self.admin_bookings_page,
            'admin_users': self.admin_users_page,
            'admin_claims': self.admin_claims_page,
            'admin_analytics': self.admin_analytics_page,
            'about': self.about_page,
            'contact': self.contact_page,
            'faq': self.faq_page,
            'terms': self.terms_page,
            'privacy': self.privacy_page,
            'not_found': self.not_found_page
        }
        self.default_route = 'welcome'
        
    def get_current_route(self):
        """Get current route from URL parameters or session state"""
        # Check URL parameters first
        params = st.experimental_get_query_params()
        page = params.get('page', [None])[0]
        
        # If no page in URL, check session state
        if page is None and 'current_page' in st.session_state:
            page = st.session_state.current_page
            
        # Validate route exists
        if page not in self.routes:
            page = self.default_route
            
        # Store in session state
        st.session_state.current_page = page
        
        return page
    
    def navigate_to(self, route, **params):
        """Navigate to a route with optional parameters"""
        if route not in self.routes:
            route = self.default_route
            
        # Store in session state
        st.session_state.current_page = route
        
        # Update URL parameters
        url_params = {'page': route}
        for key, value in params.items():
            url_params[key] = value
            
        st.experimental_set_query_params(**url_params)
        
    def render_current_page(self, app_context):
        """Render the current page based on route"""
        current_route = self.get_current_route()
        
        # Check authentication for protected routes
        protected_routes = [
            'my_bookings', 'my_vehicles', 'list_vehicle', 'owner_bookings',
            'profile', 'subscription', 'insurance_claims', 'claim_details',
            'wishlist', 'notifications', 'book_vehicle'
        ]
        
        admin_routes = [
            'admin_dashboard', 'admin_vehicles', 'admin_bookings',
            'admin_users', 'admin_claims', 'admin_analytics'
        ]
        
        if current_route in protected_routes and not app_context.is_logged_in():
            # Redirect to login
            st.warning("Please log in to access this page")
            self.navigate_to('login', next=current_route)
            self.login_page(app_context)
            return
            
        if current_route in admin_routes and not app_context.is_admin():
            # Redirect to unauthorized
            st.error("You don't have permission to access this page")
            self.navigate_to('welcome')
            self.welcome_page(app_context)
            return
            
        # Render the page
        self.routes[current_route](app_context)
    
    # Individual page handlers
    def welcome_page(self, app_context):
        """Render welcome/home page"""
        ui = app_context.ui
        db = app_context.db_manager
        vehicle_manager = app_context.get_vehicle_manager()
        analytics = app_context.get_analytics_manager()
        
        # Track page view
        if app_context.is_logged_in():
            analytics.track_event(
                'page_view',
                user_id=app_context.get_user_id(),
                event_data={'page': 'welcome'}
            )
        
        # Header section
        st.markdown("""
        <div style="text-align: center; padding: 2rem 1rem 4rem 1rem; background: linear-gradient(135deg, #0A2647, #2C74B3); color: white; border-radius: 10px; margin-bottom: 2rem;">
            <h1 style="font-size: 3.5rem; margin-bottom: 1rem;">Experience Luxury on Wheels</h1>
            <p style="font-size: 1.2rem; max-width: 700px; margin: 0 auto 2rem auto;">
                Discover our exclusive collection of premium vehicles. From iconic sports cars to luxury SUVs,
                find your perfect ride for any occasion.
            </p>
            <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 2rem;">
                <a href="?page=browse_vehicles" class="stButton" style="background-color: white; color: #0A2647; padding: 0.75rem 2rem; border-radius: 50px; text-decoration: none; font-weight: 600; transition: all 0.3s ease;">
                    Explore Vehicles
                </a>
                <a href="?page=about" class="stButton" style="background-color: transparent; border: 2px solid white; color: white; padding: 0.75rem 2rem; border-radius: 50px; text-decoration: none; font-weight: 600; transition: all 0.3s ease;">
                    Learn More
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Featured vehicles section
        st.markdown("""
        <h2 style="text-align: center; margin-bottom: 2rem;">Featured Vehicles</h2>
        """, unsafe_allow_html=True)
        
        # Get featured vehicles
        featured_vehicles = vehicle_manager.get_vehicles(
            filters={'status': 'approved', 'featured_first': True},
            limit=6
        )
        
        if featured_vehicles:
            # Display in 3 columns
            cols = st.columns(3)
            for i, vehicle in enumerate(featured_vehicles):
                with cols[i % 3]:
                    st.markdown(
                        ui.vehicle_card(vehicle),
                        unsafe_allow_html=True
                    )
        else:
            st.info("No featured vehicles available at the moment.")
            
        # How it works section
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 3rem 2rem; border-radius: 10px; margin: 3rem 0;">
            <h2 style="text-align: center; margin-bottom: 3rem;">How It Works</h2>
            
            <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 2rem; text-align: center;">
                <div style="flex: 1; min-width: 250px; max-width: 350px;">
                    <div style="background-color: #0A2647; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.5rem auto;">
                        <span style="font-size: 2rem; color: white;">1</span>
                    </div>
                    <h3>Search & Compare</h3>
                    <p>Browse our extensive collection of luxury vehicles and find your perfect match.</p>
                </div>
                
                <div style="flex: 1; min-width: 250px; max-width: 350px;">
                    <div style="background-color: #0A2647; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.5rem auto;">
                        <span style="font-size: 2rem; color: white;">2</span>
                    </div>
                    <h3>Book Instantly</h3>
                    <p>Confirm your booking in just a few clicks with our secure and seamless booking system.</p>
                </div>
                
                <div style="flex: 1; min-width: 250px; max-width: 350px;">
                    <div style="background-color: #0A2647; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.5rem auto;">
                        <span style="font-size: 2rem; color: white;">3</span>
                    </div>
                    <h3>Drive & Enjoy</h3>
                    <p>Pick up your vehicle and enjoy the premium driving experience you deserve.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Popular locations
        popular_locations = analytics.get_popular_locations(limit=5)
        
        if popular_locations:
            st.markdown("""
            <h2 style="text-align: center; margin: 3rem 0 2rem 0;">Popular Locations</h2>
            """, unsafe_allow_html=True)
            
            # Display locations as cards
            location_cols = st.columns(len(popular_locations))
            for i, location in enumerate(popular_locations):
                with location_cols[i]:
                    st.markdown(f"""
                    <div style="background-color: white; padding: 1.5rem; border-radius: 10px; text-align: center; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;">
                        <h3 style="margin-bottom: 1rem;">{location['location']}</h3>
                        <p style="color: #666;">{location['count']} bookings</p>
                        <a href="?page=browse_vehicles&location={location['location']}" style="display: inline-block; margin-top: 1rem; text-decoration: none; color: #0A2647; font-weight: 600;">
                            Explore vehicles →
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                    
        # Testimonials section
        st.markdown("""
        <div style="margin: 4rem 0;">
            <h2 style="text-align: center; margin-bottom: 3rem;">What Our Customers Say</h2>
            
            <div style="display: flex; flex-wrap: wrap; gap: 2rem; justify-content: center;">
                <div style="flex: 1; min-width: 300px; max-width: 400px; background-color: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <div style="color: #FFD700; font-size: 1.5rem; margin-bottom: 1rem;">★★★★★</div>
                    <p style="font-style: italic; margin-bottom: 1.5rem;">
                        "The entire experience was flawless. The Ferrari I rented was immaculate, and the service was exceptional.
                        Will definitely be using LuxeWheels again for my next trip!"
                    </p>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 50px; height: 50px; border-radius: 50%; background-color: #DDD; margin-right: 1rem;"></div>
                        <div>
                            <strong>Sarah Johnson</strong>
                            <p style="font-size: 0.875rem; color: #666; margin: 0;">Dubai</p>
                        </div>
                    </div>
                </div>
                
                <div style="flex: 1; min-width: 300px; max-width: 400px; background-color: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <div style="color: #FFD700; font-size: 1.5rem; margin-bottom: 1rem;">★★★★★</div>
                    <p style="font-style: italic; margin-bottom: 1.5rem;">
                        "Outstanding selection of luxury vehicles. The Bentley Continental was perfect for our wedding day.
                        The staff went above and beyond to ensure everything was perfect."
                    </p>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 50px; height: 50px; border-radius: 50%; background-color: #DDD; margin-right: 1rem;"></div>
                        <div>
                            <strong>Mohammed Al-Farsi</strong>
                            <p style="font-size: 0.875rem; color: #666; margin: 0;">Abu Dhabi</p>
                        </div>
                    </div>
                </div>
                
                <div style="flex: 1; min-width: 300px; max-width: 400px; background-color: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <div style="color: #FFD700; font-size: 1.5rem; margin-bottom: 1rem;">★★★★★</div>
                    <p style="font-style: italic; margin-bottom: 1.5rem;">
                        "As a car enthusiast, I appreciate the immaculate condition of their vehicles. 
                        The Lamborghini Huracan was a dream to drive and the pickup/return process was seamless."
                    </p>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 50px; height: 50px; border-radius: 50%; background-color: #DDD; margin-right: 1rem;"></div>
                        <div>
                            <strong>James Wilson</strong>
                            <p style="font-size: 0.875rem; color: #666; margin: 0;">New York</p>
                        </div>
                    </div

                    </div>
            
        """, unsafe_allow_html=True)
        
        # App benefits section
        st.markdown("""
        <div style="background: linear-gradient(135deg, #144272, #0A2647); color: white; padding: 4rem 2rem; border-radius: 10px; margin: 4rem 0;">
            <h2 style="text-align: center; margin-bottom: 3rem; color: white;">Why Choose LuxeWheels</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem;">
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🛡️</div>
                    <h3 style="color: white; margin-bottom: 1rem;">Premium Insurance</h3>
                    <p>Comprehensive coverage for peace of mind during your luxury experience.</p>
                </div>
                
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">✨</div>
                    <h3 style="color: white; margin-bottom: 1rem;">Immaculate Vehicles</h3>
                    <p>Every vehicle is thoroughly inspected and detailed before each rental.</p>
                </div>
                
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🔒</div>
                    <h3 style="color: white; margin-bottom: 1rem;">Secure Booking</h3>
                    <p>State-of-the-art encryption and secure payment processing.</p>
                </div>
                
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🌟</div>
                    <h3 style="color: white; margin-bottom: 1rem;">VIP Experience</h3>
                    <p>Personalized service and exclusive benefits for our members.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Call to action
        st.markdown("""
        <div style="text-align: center; margin: 5rem 0 3rem 0;">
            <h2 style="margin-bottom: 1.5rem;">Ready to Experience Luxury?</h2>
            <p style="max-width: 600px; margin: 0 auto 2rem auto; color: #666;">
                Join thousands of satisfied customers who have elevated their journeys with our premium vehicles.
            </p>
            <a href="?page=signup" class="stButton" style="display: inline-block; background-color: #0A2647; color: white; padding: 1rem 3rem; border-radius: 50px; text-decoration: none; font-weight: 600; transition: all 0.3s ease; font-size: 1.2rem;">
                Join Now
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    def login_page(self, app_context):
        """Render login page"""
        ui = app_context.ui
        auth_manager = app_context.get_auth_manager()
        analytics = app_context.get_analytics_manager()
        
        # Get next page from URL parameters if available
        params = st.experimental_get_query_params()
        next_page = params.get('next', ['browse_vehicles'])[0]
        
        ui.header("Welcome Back", "Sign in to your LuxeWheels account")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="background-color: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            """, unsafe_allow_html=True)
            
            # Login form
            with st.form("login_form"):
                email = st.text_input("Email Address")
                password = st.text_input("Password", type="password")
                remember_me = st.checkbox("Remember me")
                
                submit_button = st.form_submit_button("Sign In")
                
                if submit_button:
                    if not email or not password:
                        st.error("Please enter both email and password")
                    else:
                        success, result = auth_manager.login_user(email, password)
                        
                        if success:
                            # Set session state
                            st.session_state.user_id = result['id']
                            st.session_state.user_role = result['role']
                            st.session_state.is_logged_in = True
                            
                            # Track login event
                            analytics.track_event(
                                'user_login',
                                user_id=result['id']
                            )
                            
                            # Redirect to next page
                            st.success("Login successful! Redirecting...")
                            self.navigate_to(next_page)
                            st.rerun()
                        else:
                            st.error(result)
            
            # Additional options
            st.markdown("""
            <div style="display: flex; justify-content: space-between; margin-top: 1rem;">
                <a href="?page=reset_password" style="color: #0A2647; text-decoration: none;">Forgot password?</a>
                <a href="?page=signup" style="color: #0A2647; text-decoration: none;">Don't have an account? Sign up</a>
            </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Demo credentials in development
            if os.environ.get('ENVIRONMENT') == 'development':
                st.markdown("""
                <div style="margin-top: 2rem; padding: 1rem; background-color: #E0F7FA; border-radius: 10px; border-left: 4px solid #00BCD4;">
                    <h4 style="margin-top: 0;">Demo Credentials</h4>
                    <p><strong>Admin:</strong> admin@luxewheels.com / admin@LuxeWheels2025</p>
                    <p><strong>User:</strong> demo@luxewheels.com / Demo123!</p>
                </div>
                """, unsafe_allow_html=True)
    
    def signup_page(self, app_context):
        """Render signup page"""
        ui = app_context.ui
        auth_manager = app_context.get_auth_manager()
        image_handler = ImageHandler()
        analytics = app_context.get_analytics_manager()
        
        ui.header("Create an Account", "Join LuxeWheels for access to premium vehicles")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="background-color: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            """, unsafe_allow_html=True)
            
            # Signup form
            with st.form("signup_form"):
                # Personal information
                st.subheader("Personal Information")
                full_name = st.text_input("Full Name")
                email = st.text_input("Email Address")
                phone = st.text_input("Phone Number")
                
                # Account credentials
                st.subheader("Account Credentials")
                password = st.text_input("Password", type="password", 
                                        help="Must be at least 8 characters with a mix of letters, numbers, and symbols")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                # Profile picture (optional)
                st.subheader("Profile Picture (Optional)")
                profile_pic = st.file_uploader("Upload a profile picture", type=["jpg", "jpeg", "png"])
                
                profile_image_data = None
                if profile_pic:
                    # Preview the image
                    image = Image.open(profile_pic)
                    st.image(image, width=150)
                    
                    # Validate and process image
                    is_valid, message = image_handler.validate_image(profile_pic)
                    if is_valid:
                        profile_image_data = image_handler.save_uploaded_image(profile_pic)
                    else:
                        st.error(message)
                
                # Terms and privacy
                agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
                
                submit_button = st.form_submit_button("Create Account")
                
                if submit_button:
                    # Validate inputs
                    if not all([full_name, email, phone, password, confirm_password]):
                        st.error("Please fill in all required fields")
                    elif not agree_terms:
                        st.error("You must agree to the Terms of Service and Privacy Policy")
                    elif password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters")
                    else:
                        # Create user
                        success, result = auth_manager.create_user(
                            full_name=full_name,
                            email=email,
                            phone=phone,
                            password=password,
                            profile_image=profile_image_data
                        )
                        
                        if success:
                            # Track signup event
                            analytics.track_event(
                                'user_signup',
                                user_id=result
                            )
                            
                            # Show success message and redirect
                            st.success("Account created successfully! Please log in.")
                            self.navigate_to('login')
                            st.rerun()
                        else:
                            st.error(result)
            
            # Login link
            st.markdown("""
            <div style="text-align: center; margin-top: 1rem;">
                <p>Already have an account? <a href="?page=login" style="color: #0A2647; text-decoration: none;">Sign in</a></p>
            </div>
            </div>
            """, unsafe_allow_html=True)
    
    def browse_vehicles_page(self, app_context):
        """Render vehicle browsing page"""
        ui = app_context.ui
        vehicle_manager = app_context.get_vehicle_manager()
        analytics = app_context.get_analytics_manager()
        
        # Track page view
        if app_context.is_logged_in():
            analytics.track_event(
                'page_view',
                user_id=app_context.get_user_id(),
                event_data={'page': 'browse_vehicles'}
            )
        
        # Get filter parameters from URL
        params = st.experimental_get_query_params()
        
        url_category = params.get('category', [None])[0]
        url_location = params.get('location', [None])[0]
        url_search = params.get('search', [None])[0]
        
        ui.header("Explore Our Fleet", "Discover and book the perfect luxury vehicle")
        
        # Filters section
        with st.container():
            st.markdown("""
            <div class="filter-panel">
                <h3 style="margin-top: 0;">Find Your Perfect Vehicle</h3>
            """, unsafe_allow_html=True)
            
            # Initialize filter state
            if 'filter_state' not in st.session_state:
                st.session_state.filter_state = {
                    'search': url_search or '',
                    'category': url_category or 'All',
                    'location': url_location or 'All',
                    'price_range': [0, 5000],
                    'date_range': None
                }
            
            # Search and filters
            col1, col2 = st.columns([3, 1])
            
            with col1:
                search = st.text_input("Search vehicles", 
                                      value=st.session_state.filter_state['search'],
                                      placeholder="e.g., Ferrari, Lamborghini, SUV...")
                st.session_state.filter_state['search'] = search
            
            with col2:
                sort_options = {
                    'newest': 'Newest First',
                    'price_low': 'Price: Low to High',
                    'price_high': 'Price: High to Low',
                    'rating': 'Highest Rated'
                }
                sort_by = st.selectbox("Sort by", options=list(sort_options.keys()),
                                     format_func=lambda x: sort_options[x])
            
            # Get category and location options
            categories = ['All'] + vehicle_manager.get_vehicle_categories()
            locations = ['All'] + vehicle_manager.get_vehicle_locations()
            
            # Price range
            price_range = vehicle_manager.get_price_range()
            min_price, max_price = price_range['min'], price_range['max']
            
            # Set a reasonable step
            price_step = max(10, (max_price - min_price) // 100)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                category = st.selectbox("Category", 
                                       options=categories,
                                       index=categories.index(st.session_state.filter_state['category']) 
                                       if st.session_state.filter_state['category'] in categories 
                                       else 0)
                st.session_state.filter_state['category'] = category
                
            with col2:
                location = st.selectbox("Location", 
                                       options=locations,
                                       index=locations.index(st.session_state.filter_state['location'])
                                       if st.session_state.filter_state['location'] in locations
                                       else 0)
                st.session_state.filter_state['location'] = location
                
            with col3:
                date_range = st.date_input("Rental Dates (Optional)", 
                                          value=st.session_state.filter_state['date_range'],
                                          min_value=datetime.now().date(),
                                          help="Select your desired rental start and end dates")
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    st.session_state.filter_state['date_range'] = date_range
                else:
                    st.session_state.filter_state['date_range'] = None
            
            # Price range slider
            price_range = st.slider("Price Range (AED per day)", 
                                  min_value=int(min_price),
                                  max_value=int(max_price),
                                  value=st.session_state.filter_state['price_range'],
                                  step=price_step)
            st.session_state.filter_state['price_range'] = price_range
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Build filter dictionary for query
        filters = {}
        
        if st.session_state.filter_state['search']:
            filters['search'] = st.session_state.filter_state['search']
            
        if st.session_state.filter_state['category'] != 'All':
            filters['category'] = st.session_state.filter_state['category']
            
        if st.session_state.filter_state['location'] != 'All':
            filters['location'] = st.session_state.filter_state['location']
            
        if st.session_state.filter_state['price_range']:
            filters['min_price'] = st.session_state.filter_state['price_range'][0]
            filters['max_price'] = st.session_state.filter_state['price_range'][1]
            
        if st.session_state.filter_state['date_range']:
            start_date, end_date = st.session_state.filter_state['date_range']
            filters['available_from'] = start_date.isoformat()
            filters['available_until'] = end_date.isoformat()
            
        # Default filter: only show approved vehicles
        filters['status'] = 'approved'
        
        # Determine sort parameters
        sort_mapping = {
            'newest': ('created_at', 'DESC'),
            'price_low': ('daily_rate', 'ASC'),
            'price_high': ('daily_rate', 'DESC'),
            'rating': ('average_rating', 'DESC')
        }
        
        sort_field, sort_order = sort_mapping.get(sort_by, ('created_at', 'DESC'))
        
        # Pagination
        page = st.session_state.get('vehicles_page', 1)
        per_page = 9
        offset = (page - 1) * per_page
        
        # Get vehicles
        vehicles = vehicle_manager.get_vehicles(
            filters=filters,
            sort_by=sort_field,
            sort_order=sort_order,
            limit=per_page,
            offset=offset
        )
        
        # Get total count for pagination
        total_count_filters = filters.copy()
        if 'limit' in total_count_filters:
            del total_count_filters['limit']
        if 'offset' in total_count_filters:
            del total_count_filters['offset']
            
        total_vehicles = len(vehicle_manager.get_vehicles(
            filters=total_count_filters,
            limit=1000  # Using a high limit as a workaround
        ))
        
        total_pages = max(1, (total_vehicles + per_page - 1) // per_page)
        
        # Display results
        if not vehicles:
            st.info("No vehicles match your criteria. Try adjusting your filters.")
        else:
            st.markdown(f"""
            <div style="margin: 2rem 0 1rem 0;">
                <p>{total_vehicles} vehicles found</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display in grid
            rows = (len(vehicles) + 2) // 3  # Ceiling division
            
            for row in range(rows):
                cols = st.columns(3)
                for col in range(3):
                    idx = row * 3 + col
                    if idx < len(vehicles):
                        with cols[col]:
                            st.markdown(
                                ui.vehicle_card(vehicles[idx]),
                                unsafe_allow_html=True
                            )
            
            # Pagination controls
            if total_pages > 1:
                st.markdown("<div style='display: flex; justify-content: center; margin-top: 2rem;'>", unsafe_allow_html=True)
                
                cols = st.columns([1, 1, 3, 1, 1])
                
                with cols[0]:
                    if page > 1:
                        if st.button("← First"):
                            st.session_state.vehicles_page = 1
                            st.rerun()
                            
                with cols[1]:
                    if page > 1:
                        if st.button("< Previous"):
                            st.session_state.vehicles_page = page - 1
                            st.rerun()
                            
                with cols[2]:
                    st.markdown(f"""
                    <div style='text-align: center; padding: 0.5rem;'>
                        Page {page} of {total_pages}
                    </div>
                    """, unsafe_allow_html=True)
                    
                with cols[3]:
                    if page < total_pages:
                        if st.button("Next >"):
                            st.session_state.vehicles_page = page + 1
                            st.rerun()
                            
                with cols[4]:
                    if page < total_pages:
                        if st.button("Last →"):
                            st.session_state.vehicles_page = total_pages
                            st.rerun()
                            
                st.markdown("</div>", unsafe_allow_html=True)
    
    def vehicle_details_page(self, app_context):
        """Render vehicle details page"""
        ui = app_context.ui
        vehicle_manager = app_context.get_vehicle_manager()
        booking_manager = app_context.get_booking_manager()
        analytics = app_context.get_analytics_manager()
        is_logged_in = app_context.is_logged_in()
        
        # Get vehicle ID from URL
        params = st.experimental_get_query_params()
        vehicle_id = params.get('id', [None])[0]
        
        if not vehicle_id:
            st.error("Vehicle ID is required")
            self.navigate_to('browse_vehicles')
            return
            
        # Get vehicle details
        vehicle = vehicle_manager.get_vehicle(vehicle_id)
        
        if not vehicle:
            st.error("Vehicle not found")
            self.navigate_to('browse_vehicles')
            return
            
        # Increment view count if user is logged in
        if is_logged_in:
            vehicle_manager.increment_views(vehicle_id)
            
            # Track view event
            analytics.track_event(
                'vehicle_view',
                user_id=app_context.get_user_id(),
                event_data={
                    'vehicle_id': vehicle_id,
                    'brand': vehicle['brand'],
                    'model': vehicle['model'],
                    'category': vehicle['category'],
                    'price': vehicle['daily_rate'],
                    'location': vehicle['location']
                }
            )
        
        # Check if vehicle is in user's wishlist
        in_wishlist = False
        if is_logged_in:
            in_wishlist = vehicle_manager.is_in_wishlist(
                app_context.get_user_id(), 
                vehicle_id
            )
        
        # Back button
        if st.button("← Back to Browse"):
            self.navigate_to('browse_vehicles')
            return
        
        # Vehicle details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Image gallery
            if vehicle['images']:
                # Extract image data
                image_data = [img['data'] for img in vehicle['images']]
                
                # Create image gallery
                st.markdown(
                    ImageHandler.render_image_gallery(image_data),
                    unsafe_allow_html=True
                )
            else:
                st.image("https://via.placeholder.com/800x400?text=No+Image+Available")
                
            # Description
            st.markdown(f"""
            <div style="background-color: white; padding: 1.5rem; border-radius: 10px; margin-top: 2rem;">
                <h3>Description</h3>
                <p>{vehicle['description'] or 'No description available.'}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Specifications
            try:
                specs = json.loads(vehicle['specifications']) if isinstance(vehicle['specifications'], str) else vehicle['specifications']
            except:
                specs = {}
                
            st.markdown(f"""
            <div style="background-color: white; padding: 1.5rem; border-radius: 10px; margin-top: 1.5rem;">
                <h3>Specifications</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
            """, unsafe_allow_html=True)
            
            # Display specs
            specs_list = []
            
            if 'engine' in specs:
                specs_list.append(f"<div><strong>Engine:</strong> {specs['engine']}</div>")
            if 'transmission' in specs:
                specs_list.append(f"<div><strong>Transmission:</strong> {specs['transmission']}</div>")
            if 'mileage' in specs:
                specs_list.append(f"<div><strong>Mileage:</strong> {specs['mileage']} km</div>")
            if 'year' in vehicle:
                specs_list.append(f"<div><strong>Year:</strong> {vehicle['year']}</div>")
            if 'category' in vehicle:
                specs_list.append(f"<div><strong>Category:</strong> {vehicle['category']}</div>")
                
            # Add features if available
            if 'features' in specs and isinstance(specs['features'], dict):
                for feature, value in specs['features'].items():
                    if value:
                        feature_name = feature.replace('_', ' ').title()
                        specs_list.append(f"<div><strong>{feature_name}:</strong> Yes</div>")
                        
            # If no specs are available
            if not specs_list:
                specs_list.append("<div>No detailed specifications available.</div>")
                
            st.markdown("".join(specs_list), unsafe_allow_html=True)
            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Owner information
            st.markdown(f"""
            <div style="background-color: white; padding: 1.5rem; border-radius: 10px; margin-top: 1.5rem;">
                <h3>Owner Information</h3>
                <p><strong>Name:</strong> {vehicle['owner_name']}</p>
                <p><strong>Contact:</strong> {vehicle['owner_email']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Reviews
            st.markdown(f"""
            <div style="background-color: white; padding: 1.5rem; border-radius: 10px; margin-top: 1.5rem; margin-bottom: 2rem;">
                <h3>Reviews</h3>
                <p>Coming soon...</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Booking card
            st.markdown(f"""
            <div style="background-color: white; padding: 1.5rem; border-radius: 10px; position: sticky; top: 2rem;">
                <h2>{vehicle['brand']} {vehicle['model']}</h2>
                <h3 style="color: #0A2647; font-size: 1.8rem; margin: 1rem 0;">
                    AED {vehicle['daily_rate']:,.2f}<span style="font-size: 1rem; color: #666;"> / day</span>
                </h3>
                
                <div style="margin: 1.5rem 0;">
                    <p><strong>Location:</strong> {vehicle['location']}</p>
                    <p><strong>Year:</strong> {vehicle['year']}</p>
                    <p><strong>Available:</strong> {vehicle['available_from'] or 'Now'}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Booking button
            if is_logged_in:
                # Check if user is not the owner
                is_owner = app_context.get_user_id() == vehicle['owner_id']
                
                if is_owner:
                    st.markdown("""
                    <div class="message-box info-box">
                        <p>This is your listed vehicle.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Manage This Listing"):
                        self.navigate_to('my_vehicles', edit_id=vehicle_id)
                        return
                else:
                    if st.button("Book Now", key="book_now_btn", type="primary"):
                        self.navigate_to('book_vehicle', id=vehicle_id)
                        return
                    
                    # Wishlist button
                    if in_wishlist:
                        if st.button("❤️ Remove from Wishlist"):
                            vehicle_manager.remove_from_wishlist(
                                app_context.get_user_id(),
                                vehicle_id
                            )
                            st.success("Removed from wishlist")
                            time.sleep(1)
                            st.rerun()
                    else:
                        if st.button("🤍 Add to Wishlist"):
                            vehicle_manager.add_to_wishlist(
                                app_context.get_user_id(),
                                vehicle_id
                            )
                            st.success("Added to wishlist")
                            time.sleep(1)
                            st.rerun()
            else:
                if st.button("Sign In to Book", key="signin_to_book"):
                    self.navigate_to('login', next=f'vehicle_details&id={vehicle_id}')
                    return
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Similar vehicles
            similar_vehicles = vehicle_manager.get_vehicles(
                filters={
                    'category': vehicle['category'],
                    'status': 'approved',
                    'min_price': max(0, vehicle['daily_rate'] * 0.7),  # 30% cheaper
                    'max_price': vehicle['daily_rate'] * 1.3  # 30% more expensive
                },
                limit=3
            )
            
            # Remove current vehicle from similar vehicles
            similar_vehicles = [v for v in similar_vehicles if v['id'] != vehicle_id]
            
            if similar_vehicles:
                st.markdown(f"""
                <div style="background-color: white; padding: 1.5rem; border-radius: 10px; margin-top: 1.5rem;">
                    <h3>Similar Vehicles</h3>
                """, unsafe_allow_html=True)
                
                for similar in similar_vehicles:
                    st.markdown(
                        ui.vehicle_card(similar, show_buttons=False) + 
                        f"""
                        <div style="text-align: center; margin-top: 0.5rem;">
                            <a href="?page=vehicle_details&id={similar['id']}" style="color: #0A2647; text-decoration: none; font-weight: 600;">
                                View Details
                            </a>
                        </div>
                        <hr style="margin: 1rem 0;">
                        """,
                        unsafe_allow_html=True
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)
    def book_vehicle_page(self, app_context):
        """Render vehicle booking page"""
        ui = app_context.ui
        vehicle_manager = app_context.get_vehicle_manager()
        booking_manager = app_context.get_booking_manager()
        subscription_manager = app_context.get_subscription_manager()
        
        # Ensure user is logged in
        if not app_context.is_logged_in():
            st.warning("Please log in to book a vehicle")
            self.navigate_to('login', next='browse_vehicles')
            return
            
        # Get vehicle ID from URL
        params = st.experimental_get_query_params()
        vehicle_id = params.get('id', [None])[0]
        
        if not vehicle_id:
            st.error("Vehicle ID is required")
            self.navigate_to('browse_vehicles')
            return
            
        # Get vehicle details
        vehicle = vehicle_manager.get_vehicle(vehicle_id)
        
        if not vehicle:
            st.error("Vehicle not found")
            self.navigate_to('browse_vehicles')
            return
            
        # Check if user is not the owner
        is_owner = app_context.get_user_id() == vehicle['owner_id']
        if is_owner:
            st.error("You cannot book your own vehicle")
            self.navigate_to('vehicle_details', id=vehicle_id)
            return
            
        # Get user subscription for benefits
        user_subscription = subscription_manager.get_user_subscription(app_context.get_user_id())
        
        ui.header(f"Book {vehicle['brand']} {vehicle['model']}", "Complete your booking details")
        
        # Display vehicle summary
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Display vehicle image
            if vehicle['primary_image']:
                st.image(f"data:image/jpeg;base64,{vehicle['primary_image']}")
            else:
                st.image("https://via.placeholder.com/300x200?text=No+Image")
                
        with col2:
            st.markdown(f"""
            <div style="padding: 1rem; background-color: white; border-radius: 10px;">
                <h2>{vehicle['brand']} {vehicle['model']} ({vehicle['year']})</h2>
                <p><strong>Category:</strong> {vehicle['category']}</p>
                <p><strong>Location:</strong> {vehicle['location']}</p>
                <p><strong>Daily Rate:</strong> AED {vehicle['daily_rate']:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Booking form
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        
        with st.form("booking_form"):
            st.subheader("Rental Dates")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    min_value=datetime.now().date(),
                    help="The date you want to pick up the vehicle"
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    min_value=start_date,
                    help="The date you plan to return the vehicle"
                )
                
            # Calculate rental duration
            if start_date and end_date:
                rental_days = (end_date - start_date).days + 1
                if rental_days < 1:
                    st.error("End date must be after start date")
                    
            # Location information
            st.subheader("Pickup and Return")
            
            locations = vehicle_manager.get_vehicle_locations()
            
            col1, col2 = st.columns(2)
            with col1:
                pickup_location = st.selectbox(
                    "Pickup Location",
                    options=locations,
                    index=locations.index(vehicle['location']) if vehicle['location'] in locations else 0
                )
            with col2:
                return_location = st.selectbox(
                    "Return Location",
                    options=locations,
                    index=locations.index(vehicle['location']) if vehicle['location'] in locations else 0
                )
                
            # Additional services 
            st.subheader("Additional Services")
            
            col1, col2 = st.columns(2)
            with col1:
                has_insurance = st.checkbox(
                    "Insurance Coverage",
                    help="Comprehensive insurance coverage with minimal deductible"
                )
                
                delivery_options = [
                    "None",
                    "Standard (AED 100)",
                    "Premium Door-to-Door (AED 250)"
                ]
                delivery_option = st.selectbox(
                    "Delivery Option",
                    options=delivery_options
                )
            
            with col2:
                has_driver = st.checkbox(
                    "Professional Driver",
                    help="Experienced chauffeur service (AED 150/day)"
                )
                
                special_requests = st.text_area(
                    "Special Requests",
                    placeholder="Any special requests or instructions..."
                )
                
            # Promo code
            promo_code = st.text_input("Promo Code (Optional)")
            
            # Calculate pricing
            if start_date and end_date and rental_days > 0:
                # Base pricing
                base_price = vehicle['daily_rate'] * rental_days
                
                # Additional services
                insurance_price = 0
                if has_insurance:
                    insurance_price = base_price * 0.10  # 10% of base price
                    
                driver_price = 0
                if has_driver:
                    driver_price = 150 * rental_days  # AED 150 per day
                    
                delivery_price = 0
                if delivery_option == "Standard (AED 100)":
                    delivery_price = 100
                elif delivery_option == "Premium Door-to-Door (AED 250)":
                    delivery_price = 250
                    
                # Subscription discounts
                discount_percent = 0
                if user_subscription['type'] == 'premium':
                    discount_percent = 10
                elif user_subscription['type'] == 'elite':
                    discount_percent = 20
                    
                subscription_discount = 0
                if discount_percent > 0:
                    subscription_discount = (base_price * discount_percent) / 100
                    
                # Calculate totals
                subtotal = base_price + insurance_price + driver_price + delivery_price
                discount = subscription_discount
                tax = (subtotal - discount) * 0.05  # 5% VAT
                total = subtotal - discount + tax
                
                # Display pricing breakdown
                st.subheader("Price Breakdown")
                
                pricing_table = f"""
                <table style="width:100%; border-collapse: collapse;">
                    <tr>
                        <td>Base Price ({rental_days} days @ AED {vehicle['daily_rate']:,.2f})</td>
                        <td style="text-align:right;">AED {base_price:,.2f}</td>
                    </tr>
                """
                
                if has_insurance:
                    pricing_table += f"""
                    <tr>
                        <td>Insurance Coverage</td>
                        <td style="text-align:right;">AED {insurance_price:,.2f}</td>
                    </tr>
                    """
                    
                if has_driver:
                    pricing_table += f"""
                    <tr>
                        <td>Professional Driver ({rental_days} days)</td>
                        <td style="text-align:right;">AED {driver_price:,.2f}</td>
                    </tr>
                    """
                    
                if delivery_price > 0:
                    pricing_table += f"""
                    <tr>
                        <td>Delivery Service</td>
                        <td style="text-align:right;">AED {delivery_price:,.2f}</td>
                    </tr>
                    """
                    
                pricing_table += f"""
                    <tr>
                        <td><strong>Subtotal</strong></td>
                        <td style="text-align:right;"><strong>AED {subtotal:,.2f}</strong></td>
                    </tr>
                """
                
                if discount > 0:
                    pricing_table += f"""
                    <tr style="color: green;">
                        <td>{user_subscription['type'].capitalize()} Membership Discount ({discount_percent}%)</td>
                        <td style="text-align:right;">- AED {discount:,.2f}</td>
                    </tr>
                    """
                    
                pricing_table += f"""
                    <tr>
                        <td>VAT (5%)</td>
                        <td style="text-align:right;">AED {tax:,.2f}</td>
                    </tr>
                    <tr style="font-weight: bold; font-size: 1.2em;">
                        <td>Total</td>
                        <td style="text-align:right;">AED {total:,.2f}</td>
                    </tr>
                </table>
                """
                
                st.markdown(pricing_table, unsafe_allow_html=True)
                
                # Payment note
                st.info("You'll be charged a 15% deposit (AED {:.2f}) to confirm your booking. The remaining balance will be due at pickup.".format(total * 0.15))
                
            # Submit button
            submit_button = st.form_submit_button("Confirm Booking")
            
            if submit_button:
                if not (start_date and end_date and rental_days > 0):
                    st.error("Please select valid dates")
                else:
                    # Process delivery option
                    final_delivery_option = None
                    if delivery_option == "Standard (AED 100)":
                        final_delivery_option = "standard"
                    elif delivery_option == "Premium Door-to-Door (AED 250)":
                        final_delivery_option = "premium"
                        
                    # Create booking
                    success, message, booking_id = booking_manager.create_booking(
                        user_id=app_context.get_user_id(),
                        vehicle_id=vehicle_id,
                        start_date=start_date.isoformat(),
                        end_date=end_date.isoformat(),
                        pickup_location=pickup_location,
                        return_location=return_location,
                        has_insurance=has_insurance,
                        has_driver=has_driver,
                        delivery_option=final_delivery_option,
                        special_requests=special_requests,
                        discount_code=promo_code if promo_code else None
                    )
                    
                    if success:
                        st.success("Booking created successfully!")
                        time.sleep(1)
                        self.navigate_to('my_bookings')
                        st.rerun()
                    else:
                        st.error(message)
                        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Cancellation policy
        st.markdown("""
        <div class="container">
            <h3>Cancellation Policy</h3>
            <p>
                • Free cancellation up to 48 hours before pickup<br>
                • 50% refund for cancellations between 24-48 hours before pickup<br>
                • No refund for cancellations less than 24 hours before pickup
            </p>
            <p>
                <strong>Premium and Elite members:</strong> Enjoy more flexible cancellation terms.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def my_bookings_page(self, app_context):
        """Render user's bookings page"""
        ui = app_context.ui
        booking_manager = app_context.get_booking_manager()
        
        # Ensure user is logged in
        if not app_context.is_logged_in():
            st.warning("Please log in to view your bookings")
            self.navigate_to('login', next='my_bookings')
            return
            
        user_id = app_context.get_user_id()
        
        ui.header("My Bookings", "Manage your vehicle rentals")
        
        # Booking filters
        st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Status",
                options=["All", "Pending", "Confirmed", "Completed", "Canceled", "Rejected"]
            )
            
        with col2:
            date_range = st.date_input(
                "Date Range (Optional)",
                value=None,
                help="Filter bookings by date range"
            )
            
        with col3:
            search = st.text_input(
                "Search",
                placeholder="Search by vehicle, booking ID..."
            )
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Build filters
        filters = {'user_id': user_id}
        
        if status_filter != "All":
            filters['status'] = status_filter.lower()
            
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            filters['date_from'] = start_date.isoformat()
            filters['date_to'] = end_date.isoformat()
            
        if search:
            filters['search'] = search
            
        # Get bookings
        bookings = booking_manager.get_bookings(filters=filters)
        
        if not bookings:
            st.info("No bookings found matching your criteria.")
            
            # Prompt to browse vehicles
            st.markdown("""
            <div style="text-align: center; margin-top: 3rem;">
                <p>Ready to experience luxury on wheels?</p>
                <a href="?page=browse_vehicles" class="stButton" style="display: inline-block; background-color: #0A2647; color: white; padding: 0.75rem 2rem; border-radius: 50px; text-decoration: none; font-weight: 600; margin-top: 1rem;">
                    Browse Vehicles
                </a>
            </div>
            """, unsafe_allow_html=True)
            return
            
        # Display bookings
        for booking in bookings:
            with st.container():
                st.markdown(f"""
                <div class="container" style="margin-bottom: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3 style="margin: 0;">{booking['vehicle_brand']} {booking['vehicle_model']} ({booking['vehicle_year']})</h3>
                        <span class="status-badge status-{booking['status'].lower()}">
                            {booking['status'].upper()}
                        </span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Booking details
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    <p><strong>Booking ID:</strong> {booking['id']}</p>
                    <p><strong>Dates:</strong> {booking['start_date']} to {booking['end_date']} ({booking['duration_days']} days)</p>
                    <p><strong>Pickup Location:</strong> {booking['pickup_location']}</p>
                    <p><strong>Total Amount:</strong> AED {booking['total_amount']:,.2f}</p>
                    <p><strong>Payment Status:</strong> {booking['payment_status'].replace('_', ' ').title()}</p>
                    """, unsafe_allow_html=True)
                    
                    # Display additional services if any
                    services = []
                    if booking['has_insurance']:
                        services.append("Insurance")
                    if booking['has_driver']:
                        services.append("Professional Driver")
                    if booking['delivery_option']:
                        services.append(f"Delivery ({booking['delivery_option'].title()})")
                        
                    if services:
                        services_str = ", ".join(services)
                        st.markdown(f"<p><strong>Additional Services:</strong> {services_str}</p>", unsafe_allow_html=True)
                        
                with col2:
                    # Vehicle image
                    if booking['vehicle_image']:
                        st.image(f"data:image/jpeg;base64,{booking['vehicle_image']}", use_column_width=True)
                    else:
                        st.image("https://via.placeholder.com/200?text=No+Image", use_column_width=True)
                        
                # Action buttons based on status
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("View Details", key=f"details_{booking['id']}"):
                        self.navigate_to('booking_details', id=booking['id'])
                        
                with col2:
                    # Show cancel button for pending/confirmed bookings
                    if booking['status'] in ['pending', 'confirmed']:
                        if st.button("Cancel Booking", key=f"cancel_{booking['id']}"):
                            st.session_state.cancel_booking_id = booking['id']
                            st.session_state.show_cancel_modal = True
                            
                with col3:
                    # Show payment button if partially paid or unpaid
                    if booking['payment_status'] in ['unpaid', 'partially_paid'] and booking['status'] not in ['canceled', 'rejected']:
                        if st.button("Make Payment", key=f"pay_{booking['id']}"):
                            st.session_state.payment_booking_id = booking['id']
                            st.session_state.show_payment_modal = True
                            
                st.markdown("</div>", unsafe_allow_html=True)
                
        # Cancel booking modal
        if st.session_state.get('show_cancel_modal', False):
            booking_id = st.session_state.cancel_booking_id
            
            st.markdown("""
            <div class="modal-backdrop">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Cancel Booking</h2>
                        <button class="modal-close" onclick="hideCancelModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to cancel this booking? Please provide a reason:</p>
                    </div>
            """, unsafe_allow_html=True)
            
            reason = st.text_area("Cancellation Reason", key="cancel_reason")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("No, Keep Booking"):
                    st.session_state.show_cancel_modal = False
                    st.rerun()
                    
            with col2:
                if st.button("Yes, Cancel Booking"):
                    # Process cancellation
                    success, message = booking_manager.cancel_booking(
                        booking_id,
                        user_id,
                        reason
                    )
                    
                    if success:
                        st.success(message)
                        st.session_state.show_cancel_modal = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
                        
            st.markdown("""
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # Payment modal
        if st.session_state.get('show_payment_modal', False):
            booking_id = st.session_state.payment_booking_id
            
            # Get booking details
            booking = booking_manager.get_booking(booking_id)
            
            if booking:
                remaining_balance = booking['total_amount'] - booking['paid_amount']
                
                st.markdown(f"""
                <div class="modal-backdrop">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h2>Make Payment</h2>
                            <button class="modal-close" onclick="hidePaymentModal()">&times;</button>
                        </div>
                        <div class="modal-body">
                            <p><strong>Booking:</strong> {booking['vehicle_brand']} {booking['vehicle_model']}</p>
                            <p><strong>Total Amount:</strong> AED {booking['total_amount']:,.2f}</p>
                            <p><strong>Paid Amount:</strong> AED {booking['paid_amount']:,.2f}</p>
                            <p><strong>Remaining Balance:</strong> AED {remaining_balance:,.2f}</p>
                        </div>
                """, unsafe_allow_html=True)
                
                payment_options = ["Full Amount", "Deposit Only (15%)", "Custom Amount"]
                payment_option = st.radio("Payment Option", payment_options)
                
                if payment_option == "Full Amount":
                    payment_amount = remaining_balance
                elif payment_option == "Deposit Only (15%)":
                    payment_amount = booking['total_amount'] * 0.15
                    # If already paid more than deposit, show error
                    if booking['paid_amount'] >= payment_amount:
                        st.error("You've already paid more than the deposit amount")
                        payment_amount = 0
                else:
                    payment_amount = st.number_input(
                        "Enter Amount",
                        min_value=0.0,
                        max_value=float(remaining_balance),
                        step=100.0
                    )
                
                payment_methods = ["Credit Card", "Debit Card", "Apple Pay", "Google Pay"]
                payment_method = st.selectbox("Payment Method", payment_methods)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Cancel"):
                        st.session_state.show_payment_modal = False
                        st.rerun()
                        
                with col2:
                    pay_button = st.button("Make Payment")
                    if pay_button and payment_amount > 0:
                        # Process payment
                        success, message, transaction_id = booking_manager.process_payment(
                            booking_id,
                            payment_amount,
                            payment_method
                        )
                        
                        if success:
                            st.success(f"Payment of AED {payment_amount:,.2f} processed successfully")
                            st.session_state.show_payment_modal = False
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                            
                st.markdown("""
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    def booking_details_page(self, app_context):
        """Render booking details page"""
        ui = app_context.ui
        booking_manager = app_context.get_booking_manager()
        
        # Ensure user is logged in
        if not app_context.is_logged_in():
            st.warning("Please log in to view booking details")
            self.navigate_to('login', next='my_bookings')
            return
            
        # Get booking ID from URL
        params = st.experimental_get_query_params()
        booking_id = params.get('id', [None])[0]
        
        if not booking_id:
            st.error("Booking ID is required")
            self.navigate_to('my_bookings')
            return
            
        # Get booking details
        booking = booking_manager.get_booking(booking_id)
        
        if not booking:
            st.error("Booking not found")
            self.navigate_to('my_bookings')
            return
            
        # Check if user has access to this booking
        user_id = app_context.get_user_id()
        is_owner = booking['owner_id'] == user_id
        is_renter = booking['user_id'] == user_id
        
        if not (is_owner or is_renter or app_context.is_admin()):
            st.error("You don't have permission to view this booking")
            self.navigate_to('my_bookings')
            return
            
        # Back button
        if is_renter:
            if st.button("← Back to My Bookings"):
                self.navigate_to('my_bookings')
                return
        elif is_owner:
            if st.button("← Back to Owner Bookings"):
                self.navigate_to('owner_bookings')
                return
        else:
            if st.button("← Back to Admin Bookings"):
                self.navigate_to('admin_bookings')
                return
                
        ui.header(f"Booking Details", f"Booking ID: {booking_id}")
        
        # Main booking information
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div class="container">
                <h2>{booking['vehicle_brand']} {booking['vehicle_model']} ({booking['vehicle_year']})</h2>
                <div style="display: flex; align-items: center; margin: 1rem 0;">
                    <span class="status-badge status-{booking['status'].lower()}" style="margin-right: 1rem;">
                        {booking['status'].upper()}
                    </span>
                    <span style="color: #666;">Created on {booking['created_at']}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Booking dates and location
            st.markdown(f"""
                <div style="margin: 1.5rem 0;">
                    <h3>Rental Information</h3>
                    <p><strong>Rental Period:</strong> {booking['start_date']} to {booking['end_date']} ({booking['duration_days']} days)</p>
                    <p><strong>Pickup Location:</strong> {booking['pickup_location']}</p>
                    <p><strong>Return Location:</strong> {booking['return_location']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Price breakdown
            st.markdown(f"""
                <div style="margin: 1.5rem 0;">
                    <h3>Price Breakdown</h3>
                    <table style="width:100%; border-collapse: collapse;">
                        <tr>
                            <td>Base Amount</td>
                            <td style="text-align:right;">AED {(booking['total_amount'] - booking['insurance_amount'] - booking['driver_amount'] - booking['delivery_amount'] + booking['discount_amount']):,.2f}</td>
                        </tr>
            """, unsafe_allow_html=True)
            
            if booking['insurance_amount'] > 0:
                st.markdown(f"""
                    <tr>
                        <td>Insurance</td>
                        <td style="text-align:right;">AED {booking['insurance_amount']:,.2f}</td>
                    </tr>
                """, unsafe_allow_html=True)
                
            if booking['driver_amount'] > 0:
                st.markdown(f"""
                    <tr>
                        <td>Professional Driver</td>
                        <td style="text-align:right;">AED {booking['driver_amount']:,.2f}</td>
                    </tr>
                """, unsafe_allow_html=True)
                
            if booking['delivery_amount'] > 0:
                st.markdown(f"""
                    <tr>
                        <td>Delivery Service</td>
                        <td style="text-align:right;">AED {booking['delivery_amount']:,.2f}</td>
                    </tr>
                """, unsafe_allow_html=True)
                
            if booking['vip_services_amount'] > 0:
                st.markdown(f"""
                    <tr>
                        <td>VIP Services</td>
                        <td style="text-align:right;">AED {booking['vip_services_amount']:,.2f}</td>
                    </tr>
                """, unsafe_allow_html=True)
                
            if booking['discount_amount'] > 0:
                st.markdown(f"""
                    <tr style="color: green;">
                        <td>Discount</td>
                        <td style="text-align:right;">- AED {booking['discount_amount']:,.2f}</td>
                    </tr>
                """, unsafe_allow_html=True)
                
            if booking['tax_amount'] > 0:
                st.markdown(f"""
                    <tr>
                        <td>Tax (5% VAT)</td>
                        <td style="text-align:right;">AED {booking['tax_amount']:,.2f}</td>
                    </tr>
                """, unsafe_allow_html=True)
                
            st.markdown(f"""
                        <tr style="font-weight: bold;">
                            <td>Total</td>
                            <td style="text-align:right;">AED {booking['total_amount']:,.2f}</td>
                        </tr>
                        <tr>
                            <td>Paid Amount</td>
                            <td style="text-align:right;">AED {booking['paid_amount']:,.2f}</td>
                        </tr>
                        <tr style="font-weight: bold; color: {booking['paid_amount'] >= booking['total_amount'] and '#28a745' or '#dc3545'};">
                            <td>Balance Due</td>
                            <td style="text-align:right;">AED {max(0, booking['total_amount'] - booking['paid_amount']):,.2f}</td>
                        </tr>
                    </table>
                </div>
            """, unsafe_allow_html=True)
            
            # Customer/Owner information depending on who's viewing
            if is_owner or app_context.is_admin():
                st.markdown(f"""
                    <div style="margin: 1.5rem 0;">
                        <h3>Customer Information</h3>
                        <p><strong>Name:</strong> {booking['user_name']}</p>
                        <p><strong>Email:</strong> {booking['user_email']}</p>
                    </div>
                """, unsafe_allow_html=True)
            elif is_renter:
                st.markdown(f"""
                    <div style="margin: 1.5rem 0;">
                        <h3>Owner Information</h3>
                        <p><strong>Contact:</strong> {booking['owner_id']}</p>
                    </div>
                """, unsafe_allow_html=True)
            # Additional services
                services = []
                if booking['has_insurance']:
                    services.append("Insurance Coverage")
                if booking['has_driver']:
                    services.append("Professional Driver")
                if booking['delivery_option']:
                    services.append(f"Delivery Service ({booking['delivery_option'].title()})")
                    
                if services:
                    st.markdown(f"""
                        <div style="margin: 1.5rem 0;">
                            <h3>Additional Services</h3>
                            <ul>
                                {"".join([f"<li>{service}</li>" for service in services])}
                            </ul>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Special requests
                if booking['special_requests']:
                    st.markdown(f"""
                        <div style="margin: 1.5rem 0;">
                            <h3>Special Requests</h3>
                            <p>{booking['special_requests']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                # Display cancellation reason if applicable
                if booking['status'] == 'canceled' and booking['cancellation_reason']:
                    st.markdown(f"""
                        <div style="margin: 1.5rem 0; background-color: #FFEBEE; padding: 1rem; border-radius: 10px; border-left: 4px solid #C62828;">
                            <h3>Cancellation Reason</h3>
                            <p>{booking['cancellation_reason']}</p>
                            <p style="color: #666; margin-top: 0.5rem;">Canceled on {booking['cancellation_date']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown("</div>", unsafe_allow_html=True)
            
        with col2:
            # Vehicle image
            if booking['vehicle_image']:
                st.image(f"data:image/jpeg;base64,{booking['vehicle_image']}", caption=f"{booking['vehicle_brand']} {booking['vehicle_model']}")
            else:
                st.image("https://via.placeholder.com/300x200?text=No+Image", caption=f"{booking['vehicle_brand']} {booking['vehicle_model']}")
                
            # Booking timeline
            st.markdown("""
            <div class="container">
                <h3>Booking Timeline</h3>
            """, unsafe_allow_html=True)
            
            timeline = booking_manager.get_booking_timeline(booking_id)
            
            if timeline:
                st.markdown('<div class="booking-timeline">', unsafe_allow_html=True)
                
                for event in timeline:
                    st.markdown(f"""
                        <div class="booking-timeline-item {event['status']}">
                            <div class="booking-timeline-date">{event['date']}</div>
                            <div class="booking-timeline-title">{event['title']}</div>
                            <div>{event['description']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No timeline events available")
                
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Action buttons
            st.markdown("""
            <div class="container" style="margin-top: 1.5rem;">
                <h3>Actions</h3>
            """, unsafe_allow_html=True)
            
            # Different actions based on user role and booking status
            if is_renter:
                # Renter actions
                if booking['status'] == 'pending':
                    if st.button("Cancel Booking"):
                        st.session_state.cancel_booking_id = booking_id
                        st.session_state.show_cancel_modal = True
                        
                elif booking['status'] == 'confirmed':
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Cancel Booking"):
                            st.session_state.cancel_booking_id = booking_id
                            st.session_state.show_cancel_modal = True
                            
                    with col2:
                        if booking['has_insurance']:
                            if st.button("Submit Insurance Claim"):
                                self.navigate_to('claim_details', booking_id=booking_id)
                                
                elif booking['status'] == 'completed':
                    if booking['has_insurance']:
                        if st.button("Submit Insurance Claim"):
                            self.navigate_to('claim_details', booking_id=booking_id)
                            
                # Payment button if balance due
                if booking['paid_amount'] < booking['total_amount'] and booking['status'] not in ['canceled', 'rejected']:
                    if st.button("Make Payment"):
                        st.session_state.payment_booking_id = booking_id
                        st.session_state.show_payment_modal = True
                        
            elif is_owner:
                # Owner actions
                if booking['status'] == 'pending':
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Approve Booking"):
                            success, message = booking_manager.update_booking_status(
                                booking_id,
                                'confirmed'
                            )
                            
                            if success:
                                st.success(message)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(message)
                                
                    with col2:
                        if st.button("Reject Booking"):
                            st.session_state.reject_booking_id = booking_id
                            st.session_state.show_reject_modal = True
                            
                elif booking['status'] == 'confirmed':
                    if st.button("Mark as Completed"):
                        success, message = booking_manager.update_booking_status(
                            booking_id,
                            'completed'
                        )
                        
                        if success:
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
            
            # Admin actions (available to admins regardless of booking status)
            if app_context.is_admin():
                st.markdown("<h4>Admin Actions</h4>", unsafe_allow_html=True)
                
                status_options = {
                    'pending': ['confirmed', 'rejected', 'canceled'],
                    'confirmed': ['completed', 'canceled'],
                    'completed': [],
                    'rejected': [],
                    'canceled': []
                }
                
                available_statuses = status_options.get(booking['status'], [])
                
                if available_statuses:
                    new_status = st.selectbox(
                        "Change Status",
                        options=available_statuses,
                        format_func=lambda x: x.capitalize()
                    )
                    
                    notes = st.text_area("Admin Notes")
                    
                    if st.button("Update Status"):
                        success, message = booking_manager.update_booking_status(
                            booking_id,
                            new_status,
                            notes
                        )
                        
                        if success:
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.info(f"No status changes available from '{booking['status']}'")
                    
            st.markdown("</div>", unsafe_allow_html=True)
            
        # Cancel booking modal
        if st.session_state.get('show_cancel_modal', False):
            booking_id = st.session_state.cancel_booking_id
            
            st.markdown("""
            <div class="modal-backdrop">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Cancel Booking</h2>
                        <button class="modal-close" onclick="hideCancelModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to cancel this booking? Please provide a reason:</p>
                    </div>
            """, unsafe_allow_html=True)
            
            reason = st.text_area("Cancellation Reason", key="cancel_reason")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("No, Keep Booking"):
                    st.session_state.show_cancel_modal = False
                    st.rerun()
                    
            with col2:
                if st.button("Yes, Cancel Booking"):
                    # Process cancellation
                    success, message = booking_manager.cancel_booking(
                        booking_id,
                        user_id,
                        reason
                    )
                    
                    if success:
                        st.success(message)
                        st.session_state.show_cancel_modal = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
                        
            st.markdown("""
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # Reject booking modal
        if st.session_state.get('show_reject_modal', False):
            booking_id = st.session_state.reject_booking_id
            
            st.markdown("""
            <div class="modal-backdrop">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Reject Booking</h2>
                        <button class="modal-close" onclick="hideRejectModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to reject this booking? Please provide a reason:</p>
                    </div>
            """, unsafe_allow_html=True)
            
            reason = st.text_area("Rejection Reason", key="reject_reason")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("No, Keep Pending"):
                    st.session_state.show_reject_modal = False
                    st.rerun()
                    
            with col2:
                if st.button("Yes, Reject Booking"):
                    # Process rejection
                    success, message = booking_manager.update_booking_status(
                        booking_id,
                        'rejected',
                        reason
                    )
                    
                    if success:
                        st.success(message)
                        st.session_state.show_reject_modal = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
                        
            st.markdown("""
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # Payment modal
        if st.session_state.get('show_payment_modal', False):
            booking_id = st.session_state.payment_booking_id
            
            # Get booking details
            booking = booking_manager.get_booking(booking_id)
            
            if booking:
                remaining_balance = booking['total_amount'] - booking['paid_amount']
                
                st.markdown(f"""
                <div class="modal-backdrop">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h2>Make Payment</h2>
                            <button class="modal-close" onclick="hidePaymentModal()">&times;</button>
                        </div>
                        <div class="modal-body">
                            <p><strong>Booking:</strong> {booking['vehicle_brand']} {booking['vehicle_model']}</p>
                            <p><strong>Total Amount:</strong> AED {booking['total_amount']:,.2f}</p>
                            <p><strong>Paid Amount:</strong> AED {booking['paid_amount']:,.2f}</p>
                            <p><strong>Remaining Balance:</strong> AED {remaining_balance:,.2f}</p>
                        </div>
                """, unsafe_allow_html=True)
                
                payment_options = ["Full Amount", "Deposit Only (15%)", "Custom Amount"]
                payment_option = st.radio("Payment Option", payment_options)
                
                if payment_option == "Full Amount":
                    payment_amount = remaining_balance
                elif payment_option == "Deposit Only (15%)":
                    payment_amount = booking['total_amount'] * 0.15
                    # If already paid more than deposit, show error
                    if booking['paid_amount'] >= payment_amount:
                        st.error("You've already paid more than the deposit amount")
                        payment_amount = 0
                else:
                    payment_amount = st.number_input(
                        "Enter Amount",
                        min_value=0.0,
                        max_value=float(remaining_balance),
                        step=100.0
                    )
                
                payment_methods = ["Credit Card", "Debit Card", "Apple Pay", "Google Pay"]
                payment_method = st.selectbox("Payment Method", payment_methods)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Cancel"):
                        st.session_state.show_payment_modal = False
                        st.rerun()
                        
                with col2:
                    pay_button = st.button("Make Payment")
                    if pay_button and payment_amount > 0:
                        # Process payment
                        success, message, transaction_id = booking_manager.process_payment(
                            booking_id,
                            payment_amount,
                            payment_method
                        )
                        
                        if success:
                            st.success(f"Payment of AED {payment_amount:,.2f} processed successfully")
                            st.session_state.show_payment_modal = False
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                            
                st.markdown("""
                    </div>
                </div>
                """, unsafe_allow_html=True)

# Application Context
class ApplicationContext:
    """Main application context providing access to all managers and state"""
    
    def __init__(self):
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # Initialize UI components
        self.ui = UIComponents()
        
        # Set up session state for login info
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
            
        if 'user_role' not in st.session_state:
            st.session_state.user_role = None
            
        if 'is_logged_in' not in st.session_state:
            st.session_state.is_logged_in = False
    
    def get_auth_manager(self):
        """Get authentication manager instance"""
        return AuthManager(self.db_manager)
    
    def get_vehicle_manager(self):
        """Get vehicle manager instance"""
        return VehicleManager(self.db_manager)
    
    def get_booking_manager(self):
        """Get booking manager instance"""
        return BookingManager(self.db_manager)
        
    def get_subscription_manager(self):
        """Get subscription manager instance"""
        return SubscriptionManager(self.db_manager)
        
    def get_notification_manager(self):
        """Get notification manager instance"""
        return NotificationManager(self.db_manager)
        
    def get_insurance_claim_manager(self):
        """Get insurance claim manager instance"""
        return InsuranceClaimManager(self.db_manager)
        
    def get_analytics_manager(self):
        """Get analytics manager instance"""
        return AnalyticsManager(self.db_manager)
    
    def is_logged_in(self):
        """Check if user is logged in"""
        return st.session_state.is_logged_in
    
    def get_user_id(self):
        """Get current user ID"""
        return st.session_state.user_id
    
    def get_user_role(self):
        """Get current user role"""
        return st.session_state.user_role
    
    def is_admin(self):
        """Check if current user is admin"""
        return self.is_logged_in() and self.get_user_role() == 'admin'
    
    def logout(self):
        """Log out current user"""
        st.session_state.user_id = None
        st.session_state.user_role = None
        st.session_state.is_logged_in = False

# Main application
def main():
    # Create context and router
    app_context = ApplicationContext()
    router = RouteManager()
    
    # Inject JavaScript for modals and other interactive elements
    st.markdown("""
    <script>
        function hidePaymentModal() {
            window.parent.postMessage({
                type: 'streamlit:setSessionState',
                state: { show_payment_modal: false }
            }, '*');
        }
        
        function hideCancelModal() {
            window.parent.postMessage({
                type: 'streamlit:setSessionState',
                state: { show_cancel_modal: false }
            }, '*');
        }
        
        function hideRejectModal() {
            window.parent.postMessage({
                type: 'streamlit:setSessionState',
                state: { show_reject_modal: false }
            }, '*');
        }
        
        function addToWishlist(vehicleId) {
            window.parent.postMessage({
                type: 'streamlit:setSessionState',
                state: { 
                    add_to_wishlist: true,
                    wishlist_vehicle_id: vehicleId
                }
            }, '*');
        }
        
        function subscribePlan(planType) {
            window.parent.postMessage({
                type: 'streamlit:setSessionState',
                state: { 
                    subscribe_plan: true,
                    plan_type: planType
                }
            }, '*');
        }
    </script>
    """, unsafe_allow_html=True)
    
    # Show app header for logged-in users
    if app_context.is_logged_in():
        # Get user information
        auth_manager = app_context.get_auth_manager()
        notification_manager = app_context.get_notification_manager()
        
        user_info = auth_manager.get_user_info(app_context.get_user_id())
        unread_count = notification_manager.get_unread_count(app_context.get_user_id())
        
        # Construct header
        st.markdown(f"""
        <div class="app-header">
            <div class="app-header-logo">
                LuxeWheels
            </div>
            <div class="app-header-nav">
                <a href="?page=browse_vehicles" style="color: white; text-decoration: none;">Browse</a>
                <a href="?page=my_bookings" style="color: white; text-decoration: none;">My Bookings</a>
        """, unsafe_allow_html=True)
        
        # Show vehicle management for hosts
        if user_info and user_info[5] != 'admin':
            st.markdown(f"""
                <a href="?page=my_vehicles" style="color: white; text-decoration: none;">My Vehicles</a>
            """, unsafe_allow_html=True)
            
        # Admin panel link for admins
        if app_context.is_admin():
            st.markdown(f"""
                <a href="?page=admin_dashboard" style="color: white; text-decoration: none; font-weight: bold;">Admin Panel</a>
            """, unsafe_allow_html=True)
            
        # Notifications icon
        if unread_count > 0:
            st.markdown(f"""
                <a href="?page=notifications" class="notification-dot" style="color: white; text-decoration: none;">
                    🔔 ({unread_count})
                </a>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <a href="?page=notifications" style="color: white; text-decoration: none;">
                    🔔
                </a>
            """, unsafe_allow_html=True)
            
        # User profile dropdown
        full_name = user_info[1] if user_info else ""
        profile_pic = user_info[6] if user_info and user_info[6] else None
        
        st.markdown("""
                <div class="profile-menu">
        """, unsafe_allow_html=True)
        
        if profile_pic:
            st.markdown(f"""
                    <div style="display: flex; align-items: center; cursor: pointer;">
                        <img src="data:image/jpeg;base64,{profile_pic}" style="width: 35px; height: 35px; border-radius: 50%; object-fit: cover; margin-right: 8px;">
                        <span style="color: white;">{full_name}</span>
                    </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                    <div style="display: flex; align-items: center; cursor: pointer;">
                        <div style="width: 35px; height: 35px; border-radius: 50%; background-color: #144272; display: flex; align-items: center; justify-content: center; margin-right: 8px;">
                            <span style="color: white;">{full_name[0] if full_name else "U"}</span>
                        </div>
                        <span style="color: white;">{full_name}</span>
                    </div>
            """, unsafe_allow_html=True)
            
        st.markdown(f"""
                    <div class="profile-menu-content">
                        <a href="?page=profile" class="profile-menu-item">My Profile</a>
                        <a href="?page=subscription" class="profile-menu-item">Subscription</a>
                        <a href="?page=wishlist" class="profile-menu-item">Wishlist</a>
                        <a href="?page=insurance_claims" class="profile-menu-item">Insurance Claims</a>
                        <hr style="margin: 0.5rem 0; border: none; border-top: 1px solid #eee;">
                        <a href="#" class="profile-menu-item" onclick="logout()">Logout</a>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function logout() {
                window.parent.postMessage({
                    type: 'streamlit:setSessionState',
                    state: { 
                        is_logged_in: false,
                        user_id: null,
                        user_role: null,
                        current_page: 'welcome'
                    }
                }, '*');
            }
        </script>
        """, unsafe_allow_html=True)
    
    # Render current page
    router.render_current_page(app_context)
    
    # App footer
    st.markdown("""
    <div class="app-footer">
        <div style="display: flex; flex-wrap: wrap; justify-content: space-between; max-width: 1200px; margin: 0 auto;">
            <div style="flex: 1; min-width: 200px; margin-bottom: 2rem;">
                <h3>LuxeWheels</h3>
                <p>Experience luxury on wheels.</p>
                <p>© 2025 LuxeWheels. All rights reserved.</p>
            </div>
            
            <div style="flex: 1; min-width: 200px; margin-bottom: 2rem;">
                <h4>Explore</h4>
                <ul style="list-style: none; padding-left: 0;">
                    <li><a href="?page=browse_vehicles" style="color: inherit; text-decoration: none;">Browse Vehicles</a></li>
                    <li><a href="?page=about" style="color: inherit; text-decoration: none;">About Us</a></li>
                    <li><a href="?page=faq" style="color: inherit; text-decoration: none;">FAQ</a></li>
                    <li><a href="?page=contact" style="color: inherit; text-decoration: none;">Contact</a></li>
                </ul>
            </div>
            
            <div style="flex: 1; min-width: 200px; margin-bottom: 2rem;">
                <h4>Support</h4>
                <ul style="list-style: none; padding-left: 0;">
                    <li><a href="?page=terms" style="color: inherit; text-decoration: none;">Terms of Service</a></li>
                    <li><a href="?page=privacy" style="color: inherit; text-decoration: none;">Privacy Policy</a></li>
                    <li><a href="?page=help" style="color: inherit; text-decoration: none;">Help Center</a></li>
                </ul>
            </div>
            
            <div style="flex: 1; min-width: 200px; margin-bottom: 2rem;">
                <h4>Connect</h4>
                <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                    <a href="#" style="color: inherit; text-decoration: none; font-size: 1.5rem;">📱</a>
                    <a href="#" style="color: inherit; text-decoration: none; font-size: 1.5rem;">📘</a>
                    <a href="#" style="color: inherit; text-decoration: none; font-size: 1.5rem;">📸</a>
                    <a href="#" style="color: inherit; text-decoration: none; font-size: 1.5rem;">📺</a>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Handle wishlist additions (from JavaScript)
    if st.session_state.get('add_to_wishlist', False) and st.session_state.get('wishlist_vehicle_id'):
        if app_context.is_logged_in():
            vehicle_manager = app_context.get_vehicle_manager()
            vehicle_manager.add_to_wishlist(
                app_context.get_user_id(),
                st.session_state.wishlist_vehicle_id
            )
            
        # Reset state
        st.session_state.add_to_wishlist = False
        st.session_state.wishlist_vehicle_id = None
        st.rerun()
        
    # Handle subscription plan selection (from JavaScript)
    if st.session_state.get('subscribe_plan', False) and st.session_state.get('plan_type'):
        if app_context.is_logged_in():
            # Show subscription confirmation modal
            st.markdown(f"""
            <div class="modal-backdrop">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Confirm Subscription</h2>
                        <button class="modal-close" onclick="hideSubscribeModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p>You are about to subscribe to the <strong>{st.session_state.plan_type.capitalize()}</strong> plan.</p>
            """, unsafe_allow_html=True)
            
            # Show plan details
            subscription_manager = app_context.get_subscription_manager()
            plans = subscription_manager.get_subscription_plans()
            
            selected_plan = None
            for plan in plans:
                if plan['type'] == st.session_state.plan_type:
                    selected_plan = plan
                    break
                    
            if selected_plan:
                st.markdown(f"""
                    <div style="margin: 1rem 0;">
                        <p><strong>Price:</strong> AED {selected_plan['price']:.2f}/{selected_plan['period']}</p>
                        <h4>Features:</h4>
                        <ul>
                            {"".join([f"<li>{feature}</li>" for feature in selected_plan['features']])}
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
                
                duration = st.selectbox("Subscription Duration", [1, 3, 6, 12], key="subscription_duration")
                payment_method = st.selectbox("Payment Method", ["Credit Card", "Debit Card", "Apple Pay"])
                auto_renew = st.checkbox("Auto-renew subscription", value=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Cancel"):
                        st.session_state.subscribe_plan = False
                        st.session_state.plan_type = None
                        st.rerun()
                        
                with col2:
                    if st.button("Confirm Subscription"):
                        success, message = subscription_manager.subscribe_user(
                            app_context.get_user_id(),
                            st.session_state.plan_type,
                            duration_months=duration,
                            payment_method=payment_method.lower().replace(' ', '_'),
                            auto_renew=auto_renew
                        )
                        
                        if success:
                            st.success(message)
                            st.session_state.subscribe_plan = False
                            st.session_state.plan_type = None
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
            
            st.markdown("""
                </div>
            </div>
            
            <script>
                function hideSubscribeModal() {
                    window.parent.postMessage({
                        type: 'streamlit:setSessionState',
                        state: { 
                            subscribe_plan: false,
                            plan_type: null
                        }
                    }, '*');
                }
            </script>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.code(str(e), language="python")    
