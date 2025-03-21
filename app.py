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
import random
import plotly.express as px
import plotly.graph_objects as go

# Page config with favicon and improved layout
st.set_page_config(
    page_title="Luxury Car Rentals",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced custom CSS with modern design principles
st.markdown("""
    <style>
        /* Root Variables for Theming - Modern Color Palette */
        :root {
            --primary-color: #2E1A47;
            --primary-light: #4B2D6F;
            --secondary-color: #8E4162;
            --accent-color: #FFD369;
            --background-color: #F9F9F9;
            --card-color: #FFFFFF;
            --text-color: #333333;
            --text-light: #777777;
            --success-color: #28a745;
            --warning-color: #FFC107;
            --danger-color: #dc3545;
            --info-color: #17a2b8;
            --border-radius: 10px;
            --box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            --hover-transform: translateY(-5px);
        }

        /* Global Styles with Modern Typography */
        .stApp {
            background-color: var(--background-color);
            font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
            color: var(--text-color);
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Poppins', 'Segoe UI', Roboto, sans-serif;
            font-weight: 600;
            color: var(--primary-color);
        }
        
        h1 {
            font-size: 2.5rem;
            letter-spacing: -0.5px;
            margin-bottom: 1.5rem;
            text-align: center;
            position: relative;
        }
        
        h1:after {
            content: "";
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 80px;
            height: 3px;
            background-color: var(--accent-color);
            border-radius: 10px;
        }
        
        h2 {
            font-size: 1.8rem;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
        
        h3 {
            font-size: 1.4rem;
            margin-top: 1.2rem;
            margin-bottom: 0.8rem;
        }
        
        p {
            line-height: 1.6;
            margin-bottom: 1rem;
        }

        /* Button Styling with hover effects */
        .stButton>button {
            width: 100%;
            border-radius: var(--border-radius);
            height: 2.8em;
            background-color: var(--primary-color);
            color: white;
            border: none;
            margin: 5px 0;
            transition: all 0.3s ease;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: var(--box-shadow);
        }
        
        .stButton>button:hover {
            background-color: var(--primary-light);
            transform: var(--hover-transform);
            box-shadow: 0 6px 15px rgba(0,0,0,0.2);
        }
        
        /* Secondary Button Style */
        .secondary-btn .stButton>button {
            background-color: transparent;
            border: 2px solid var(--primary-color);
            color: var(--primary-color);
        }
        
        .secondary-btn .stButton>button:hover {
            background-color: var(--primary-color);
            color: white;
        }
        
        /* Accent Button Style */
        .accent-btn .stButton>button {
            background-color: var(--accent-color);
            color: var(--primary-color);
        }
        
        .accent-btn .stButton>button:hover {
            background-color: #F9C846;
        }
        
        /* Input Styling */
        input[type="text"], input[type="password"], textarea, .stTextInput>div>div>input, .stNumberInput>div>div>input, .stDateInput>div>div>input, .stTextArea>div>div>textarea {
            border-radius: var(--border-radius);
            padding: 10px 12px;
            border: 1px solid #E0E0E0;
            background-color: #F5F7F9;
            transition: all 0.3s ease;
            font-size: 1rem;
        }
        
        .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus, .stDateInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
            border-color: var(--primary-light);
            box-shadow: 0 0 0 2px rgba(75, 45, 111, 0.2);
            background-color: #FFFFFF;
        }

        /* Select Box Styling */
        .stSelectbox>div>div {
            border-radius: var(--border-radius);
            padding: 2px;
        }

        /* Card Styling with enhanced shadows and hover effects */
        .card {
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            box-shadow: var(--box-shadow);
            margin: 1rem 0;
            transition: all 0.3s ease;
            border: 1px solid rgba(0,0,0,0.05);
            overflow: hidden;
        }
        
        .card:hover {
            transform: var(--hover-transform);
            box-shadow: 0 12px 20px rgba(0,0,0,0.15);
        }
        
        /* Car card with improved layout */
        .car-card {
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            overflow: hidden;
            box-shadow: var(--box-shadow);
            margin: 1rem 0;
            transition: all 0.3s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
            position: relative;
        }
        
        .car-card:hover {
            transform: var(--hover-transform);
            box-shadow: 0 15px 30px rgba(0,0,0,0.15);
        }
        
        .car-card .car-image {
            width: 100%;
            height: 220px;
            object-fit: cover;
        }
        
        .car-card .car-content {
            padding: 1.2rem;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }
        
        .car-card .car-title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--primary-color);
        }
        
        .car-card .car-price {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--secondary-color);
            margin-bottom: 0.8rem;
        }
        
        .car-card .car-location {
            font-size: 0.9rem;
            color: var(--text-light);
            margin-bottom: 0.8rem;
        }
        
        .car-card .car-specs {
            display: flex;
            justify-content: space-between;
            padding-top: 0.8rem;
            border-top: 1px solid #EEE;
            margin-top: auto;
        }
        
        .car-card .spec-item {
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            color: var(--text-light);
        }
        
        .car-card .category-badge {
            position: absolute;
            top: 12px;
            right: 12px;
            padding: 5px 12px;
            background-color: var(--primary-color);
            color: white;
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: 20px;
            letter-spacing: 0.5px;
        }
        
        /* Status Badge with Improved Design */
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
            background-color: var(--warning-color);
            color: #333;
        }
        
        .status-badge.approved, .status-badge.confirmed {
            background-color: var(--success-color);
            color: white;
        }
        
        .status-badge.rejected {
            background-color: var(--danger-color);
            color: white;
        }
        
        /* Profile Section */
        .profile-section {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 1.5rem;
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            margin-bottom: 2rem;
        }
        
        .profile-picture {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid var(--primary-color);
            margin-bottom: 1rem;
        }
        
        .profile-name {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 0.3rem;
            color: var(--primary-color);
        }
        
        .profile-role {
            font-size: 0.9rem;
            color: var(--text-light);
            text-transform: capitalize;
            margin-bottom: 1rem;
        }
        
        /* Navigation Sidebar Styling */
        .nav-item {
            padding: 0.8rem 1rem;
            border-radius: var(--border-radius);
            margin-bottom: 0.5rem;
            transition: all 0.2s ease;
            cursor: pointer;
            display: flex;
            align-items: center;
        }
        
        .nav-item:hover {
            background-color: rgba(142, 65, 98, 0.1);
        }
        
        .nav-item.active {
            background-color: var(--primary-light);
            color: white;
        }
        
        .nav-item-icon {
            margin-right: 10px;
            width: 20px;
            text-align: center;
        }
        
        /* Subscription Cards with Improved Design */
        .subscription-card {
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            padding: 2rem;
            box-shadow: var(--box-shadow);
            margin: 1rem 0;
            height: 100%;
            display: flex;
            flex-direction: column;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .subscription-card:hover {
            transform: var(--hover-transform);
            box-shadow: 0 15px 30px rgba(0,0,0,0.2);
        }
        
        .subscription-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 6px;
            background-color: #E0E0E0;
        }
        
        .subscription-card.premium::before {
            background-color: var(--primary-color);
        }
        
        .subscription-card.elite::before {
            background-color: var(--accent-color);
        }
        
        .subscription-card h3 {
            text-align: center;
            margin-bottom: 1rem;
            color: var(--primary-color);
            font-size: 1.6rem;
        }
        
        .subscription-card .popular-tag {
            position: absolute;
            top: 15px;
            right: -35px;
            background-color: var(--accent-color);
            color: var(--primary-color);
            font-weight: 600;
            padding: 5px 40px;
            font-size: 0.8rem;
            transform: rotate(45deg);
        }
        
        .subscription-price {
            font-size: 2.5rem;
            text-align: center;
            margin: 1.5rem 0;
            font-weight: bold;
            color: var(--primary-color);
            display: flex;
            justify-content: center;
            align-items: baseline;
        }
        
        .subscription-price .currency {
            font-size: 1rem;
            margin-right: 5px;
            font-weight: normal;
            color: var(--text-light);
        }
        
        .subscription-price .period {
            font-size: 1rem;
            margin-left: 5px;
            font-weight: normal;
            color: var(--text-light);
        }
        
        .subscription-features {
            flex-grow: 1;
            margin-bottom: 1.5rem;
        }
        
        .subscription-features ul {
            list-style-type: none;
            padding-left: 0;
            margin-bottom: 1.5rem;
        }
        
        .subscription-features li {
            padding: 0.7rem 0;
            border-bottom: 1px solid #eee;
            display: flex;
            align-items: center;
        }
        
        .subscription-features li:before {
            content: "✓";
            margin-right: 0.8rem;
            color: var(--success-color);
            font-weight: bold;
        }
        
        /* Feature Comparisons */
        .feature-comparison {
            margin: 2rem 0;
        }
        
        .feature-row {
            display: flex;
            border-bottom: 1px solid #EEE;
            padding: 0.8rem 0;
        }
        
        .feature-name {
            flex: 1;
            font-weight: 500;
        }
        
        .feature-value {
            flex: 1;
            text-align: center;
        }
        
        /* Insurance Claim Card */
        .insurance-claim-card {
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            box-shadow: var(--box-shadow);
            margin: 1.5rem 0;
            transition: all 0.3s ease;
        }
        
        .insurance-claim-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 20px rgba(0,0,0,0.15);
        }
        
        /* Image Gallery with Enhanced Layout */
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
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            aspect-ratio: 16/9;
            object-fit: cover;
        }
        
        .image-gallery img:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        }
        
        /* Form Styling */
        .form-container {
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            padding: 2rem;
            box-shadow: var(--box-shadow);
            max-width: 800px;
            margin: 0 auto;
        }
        
        .form-section {
            margin-bottom: 2rem;
        }
        
        .form-section-title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--accent-color);
            color: var(--primary-color);
        }
        
        /* Notification Styling */
        .notification-item {
            padding: 1rem;
            border-radius: var(--border-radius);
            margin-bottom: 1rem;
            background-color: var(--card-color);
            box-shadow: var(--box-shadow);
            border-left: 4px solid var(--primary-color);
            transition: all 0.3s ease;
        }
        
        .notification-item:hover {
            transform: translateX(5px);
        }
        
        .notification-item.unread {
            border-left-color: var(--accent-color);
            background-color: rgba(255, 211, 105, 0.1);
        }
        
        .notification-message {
            font-size: 1rem;
            margin-bottom: 0.3rem;
        }
        
        .notification-time {
            font-size: 0.8rem;
            color: var(--text-light);
        }
        
        /* Message Styling */
        .success-message {
            background-color: #E8F5E9;
            color: #2E7D32;
            padding: 1rem;
            border-radius: var(--border-radius);
            margin: 1rem 0;
            border-left: 4px solid #2E7D32;
        }
        
        .error-message {
            background-color: #FFEBEE;
            color: #C62828;
            padding: 1rem;
            border-radius: var(--border-radius);
            margin: 1rem 0;
            border-left: 4px solid #C62828;
        }
        
        .info-message {
            background-color: #E3F2FD;
            color: #1565C0;
            padding: 1rem;
            border-radius: var(--border-radius);
            margin: 1rem 0;
            border-left: 4px solid #1565C0;
        }
        
        /* Admin Review Card */
        .admin-review-card {
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            box-shadow: var(--box-shadow);
            margin: 1.5rem 0;
        }
        
        /* Booking Details */
        .booking-details {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .booking-detail-item {
            background-color: rgba(75, 45, 111, 0.05);
            padding: 0.8rem 1rem;
            border-radius: var(--border-radius);
            flex: 1 0 200px;
        }
        
        .booking-detail-label {
            font-size: 0.8rem;
            color: var(--text-light);
            margin-bottom: 0.3rem;
        }
        
        .booking-detail-value {
            font-size: 1rem;
            font-weight: 500;
        }
        
        /* Price Breakdown */
        .price-breakdown {
            background-color: #F8F9FA;
            border-radius: var(--border-radius);
            padding: 1.2rem;
            margin: 1rem 0;
        }
        
        .price-item {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid #EEE;
        }
        
        .price-item:last-child {
            border-bottom: none;
        }
        
        .price-total {
            font-weight: 700;
            color: var(--primary-color);
            font-size: 1.2rem;
            margin-top: 0.5rem;
            padding-top: 0.5rem;
            border-top: 2px solid #DDD;
        }
        
        /* Welcome Page Animation */
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        
        .welcome-title {
            animation: fadeIn 1s ease-out;
        }
        
        .welcome-subtitle {
            animation: fadeIn 1s ease-out 0.3s forwards;
            opacity: 0;
        }
        
        .welcome-cta {
            animation: fadeIn 1s ease-out 0.6s forwards;
            opacity: 0;
        }
        
        /* Sidebar Improvements */
        .css-1544g2n {
            padding: 2rem 1rem;
        }
        
        /* Floating Action Button */
        .floating-button {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background-color: var(--accent-color);
            color: var(--primary-color);
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .floating-button:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 16px rgba(0,0,0,0.25);
        }
        
        /* Dashboard Cards */
        .dashboard-card {
            background-color: white;
            border-radius: var(--border-radius);
            padding: 1.5rem;
            box-shadow: var(--box-shadow);
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        
        .dashboard-card-title {
            font-size: 1.1rem;
            color: var(--text-light);
            margin-bottom: 1rem;
        }
        
        .dashboard-card-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .dashboard-card-change {
            font-size: 0.9rem;
            display: flex;
            align-items: center;
        }
        
        .dashboard-card-change.positive {
            color: var(--success-color);
        }
        
        .dashboard-card-change.negative {
            color: var(--danger-color);
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
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'filter_category' not in st.session_state:
    st.session_state.filter_category = "All"


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

        # Create reviews table for user reviews of car rentals
        c.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY,
                booking_id INTEGER NOT NULL,
                user_email TEXT NOT NULL,
                car_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (booking_id) REFERENCES bookings (id),
                FOREIGN KEY (user_email) REFERENCES users (email),
                FOREIGN KEY (car_id) REFERENCES car_listings (id)
            )
        ''')
        # Ensure comprehensive indexes
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_listings_status ON car_listings(listing_status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_listings_category ON car_listings(category)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(booking_status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_email, read)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_claims_status ON insurance_claims(claim_status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscription_history(user_email)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_reviews_car_id ON reviews(car_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_reviews_booking_id ON reviews(booking_id)')

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
                
        # If database is new or no listings exist, add sample data
        c.execute('SELECT COUNT(*) FROM car_listings')
        if not db_exists or c.fetchone()[0] == 0:
            add_sample_data(c)

        conn.commit()
        print("Database initialized successfully")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        st.error(f"Database error: {e}")
        raise
    finally:
         if conn:
              conn.close()


# Add sample data for better demonstration
def add_sample_data(c):
    # Sample luxury cars data
    sample_cars = [
        {
            "model": "Lamborghini Huracan EVO",
            "year": 2023,
            "price": 2500,
            "location": "Dubai Marina",
            "description": "Experience the ultimate driving thrill with the Lamborghini Huracan EVO. This supercar features a 5.2L V10 engine producing 640 hp, capable of 0-60 mph in just 2.9 seconds.",
            "category": "Sports",
            "specs": json.dumps({
                "engine": "5.2L V10 640 hp",
                "mileage": 1200,
                "transmission": "7-speed dual-clutch",
                "features": {
                    "leather_seats": True,
                    "bluetooth": True,
                    "parking_sensors": True,
                    "cruise_control": True,
                    "sunroof": False,
                    "navigation": True
                }
            }),
            "owner_email": "admin@luxuryrentals.com",
            "status": "approved"
        },
        {
            "model": "Ferrari 488 Spider",
            "year": 2022,
            "price": 2200,
            "location": "Downtown Dubai",
            "description": "The Ferrari 488 Spider combines open-top driving pleasure with the exceptional performance of the 488 GTB. Feel the wind in your hair as you experience Italian engineering at its finest.",
            "category": "Convertible",
            "specs": json.dumps({
                "engine": "3.9L V8 Twin-Turbo 670 hp",
                "mileage": 3500,
                "transmission": "7-speed dual-clutch",
                "features": {
                    "leather_seats": True,
                    "bluetooth": True,
                    "parking_sensors": True,
                    "cruise_control": True,
                    "sunroof": False,
                    "navigation": True
                }
            }),
            "owner_email": "admin@luxuryrentals.com",
            "status": "approved"
        },
        {
            "model": "Rolls-Royce Ghost",
            "year": 2023,
            "price": 3000,
            "location": "Palm Jumeirah",
            "description": "The epitome of luxury, the Rolls-Royce Ghost offers unparalleled comfort and refinement. Experience the magic carpet ride and make a statement wherever you go.",
            "category": "Luxury",
            "specs": json.dumps({
                "engine": "6.75L V12 563 hp",
                "mileage": 2000,
                "transmission": "8-speed automatic",
                "features": {
                    "leather_seats": True,
                    "bluetooth": True,
                    "parking_sensors": True,
                    "cruise_control": True,
                    "sunroof": True,
                    "navigation": True
                }
            }),
            "owner_email": "admin@luxuryrentals.com",
            "status": "approved"
        },
        {
            "model": "Tesla Model S Plaid",
            "year": 2023,
            "price": 1800,
            "location": "Dubai Hills",
            "description": "Experience the future of driving with the Tesla Model S Plaid. With a range of over 500 km and a 0-60 mph time of under 2 seconds, this electric marvel combines sustainability with performance.",
            "category": "Electric",
            "specs": json.dumps({
                "engine": "Tri-motor electric 1020 hp",
                "mileage": 5000,
                "transmission": "Single-speed",
                "features": {
                    "leather_seats": True,
                    "bluetooth": True,
                    "parking_sensors": True,
                    "cruise_control": True,
                    "sunroof": True,
                    "navigation": True
                }
            }),
            "owner_email": "admin@luxuryrentals.com",
            "status": "approved"
        },
        {
            "model": "Bentley Bentayga",
            "year": 2023,
            "price": 2300,
            "location": "Business Bay",
            "description": "The Bentley Bentayga combines luxury with SUV practicality. Perfect for those who want to make a statement while enjoying the spaciousness and commanding view of an SUV.",
            "category": "SUV",
            "specs": json.dumps({
                "engine": "4.0L V8 Twin-Turbo 542 hp",
                "mileage": 3000,
                "transmission": "8-speed automatic",
                "features": {
                    "leather_seats": True,
                    "bluetooth": True,
                    "parking_sensors": True,
                    "cruise_control": True,
                    "sunroof": True,
                    "navigation": True
                }
            }),
            "owner_email": "admin@luxuryrentals.com",
            "status": "approved"
        },
        {
            "model": "Mercedes-Benz S-Class",
            "year": 2023,
            "price": 1500,
            "location": "JBR",
            "description": "The Mercedes-Benz S-Class is the benchmark for luxury sedans. With its elegant design, advanced technology, and exceptional comfort, it offers a premium driving experience.",
            "category": "Sedan",
            "specs": json.dumps({
                "engine": "4.0L V8 496 hp",
                "mileage": 4000,
                "transmission": "9-speed automatic",
                "features": {
                    "leather_seats": True,
                    "bluetooth": True,
                    "parking_sensors": True,
                    "cruise_control": True,
                    "sunroof": True,
                    "navigation": True
                }
            }),
            "owner_email": "admin@luxuryrentals.com",
            "status": "approved"
        }
    ]
    
    # Insert sample cars
    for car in sample_cars:
        c.execute('''
            INSERT INTO car_listings 
            (owner_email, model, year, price, location, description, 
            category, specs, listing_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            car["owner_email"], car["model"], car["year"], car["price"], 
            car["location"], car["description"], car["category"], 
            car["specs"], car["status"]
        ))
        
        # Get the ID of the inserted car
        car_id = c.lastrowid
        
        # Generate a placeholder image for the car based on its model name
        # In a real implementation, you'd have actual car images
        color = generate_color_from_string(car["model"])
        img_data = generate_placeholder_car_image(car["model"], color)
        
        # Insert the image
        c.execute('''
            INSERT INTO listing_images 
            (listing_id, image_data, is_primary)
            VALUES (?, ?, ?)
        ''', (car_id, img_data, True))


# Generate a consistent color from a string
def generate_color_from_string(input_string):
    # Use the hash of the string to generate a consistent color
    hash_value = hash(input_string) % 0xFFFFFF
    return f"#{hash_value:06x}"


# Generate a placeholder image for cars
def generate_placeholder_car_image(model_name, color="#4B2D6F"):
    """Generate a placeholder image with car name and color"""
    try:
        width, height = 800, 500
        image = Image.new('RGB', (width, height), color=color)
        
        # Create a drawing context
        draw = ImageDraw.Draw(image)
        
        # Draw a car silhouette or pattern
        for i in range(20):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            draw.line((x1, y1, x2, y2), fill="#FFFFFF", width=1)
        
        # Convert to base64
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        return base64.b64encode(img_byte_arr).decode()
    except Exception as e:
        print(f"Error generating placeholder image: {e}")
        # Return a fallback base64 string for a simple colored square
        return "iVBORw0KGgoAAAANSUhEUgAAAyAAAAJYAQAAAAADLl5zAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AcxV9TxQ8qInYQcchQnSyIijhKFYtgobQVWnUwufQLmjQkKS6OgmvBwY/FqoOLs64OroIg+AHi6OSk6CIl/i8ptIjx4Lgf7+497t4BQr3MNKtrHNB020wl4mImuyoGXhFACD0YRlhmljEnSUl4jq97+Ph6F+NZ3uf+HP1qzmKATySeZYZpE28QT2/aBud94jArySrxOfGYSRckfuS64vEb54LLAs+MmOnUPHGYWCx0sNLBrGhqxFPEUVXTKV/IeKxy3uKslausdU/+wlBOX1nmOs1hJLCIJUgQoaCKEsqwEaNVJ8VCivbjHv4Rx58il0yuUhg5FlCBBrnpwf/gd7dmYXLCTQrFgcCLbX+MAMFdoFGz7e9j226cAP5n4Epr+St1YOaT9FpLixwBfdvAxXVLk/eAyx1g4EmXDMmR/DSFQh54P6NvygD9t0Bwzetb6x5nD0CaZpW8AQ4OgdECZa97vLuvu7f/nnH7+wEXMnLAu2FvCAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+UBCRURGQdLvncAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAAAMElEQVRo3u3BAQEAAACCIP+vbkhAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAF8GrskAAZSobVkAAAAASUVORK5CYII="


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
        'All',
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


# Enhanced Page Components
def welcome_page():
    st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem;">
            <h1 class="welcome-title">🏎️ Luxury Car Rentals</h1>
            <p class="welcome-subtitle" style="font-size: 1.5rem; color: #555; margin-bottom: 2rem;">Experience Luxury on Wheels in Dubai</p>
            <p class="welcome-subtitle" style="font-size: 1rem; color: #28a745; margin-bottom: 2.5rem;">Committed to SDGs 11, 12 & 13: Building sustainable mobility solutions</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Featured cars - horizontal scrolling
    st.markdown("<h2 style='text-align: center; margin-bottom: 1.5rem;'>Featured Luxury Collection</h2>", unsafe_allow_html=True)
    
    # Get featured cars
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    c.execute('''
        SELECT cl.*, li.image_data 
        FROM car_listings cl
        LEFT JOIN listing_images li ON cl.id = li.listing_id AND li.is_primary = TRUE
        WHERE cl.listing_status = 'approved'
        ORDER BY cl.created_at DESC
        LIMIT 3
    ''')
    featured_cars = c.fetchall()
    conn.close()
    
    if featured_cars:
        cols = st.columns(3)
        for i, car in enumerate(featured_cars):
            with cols[i]:
                car_id, owner_email, model, year, price, location, description, category, specs, status, created_at, image = car
                
                st.markdown(f"""
                    <div class="car-card">
                        <img src="data:image/jpeg;base64,{image}" class="car-image" alt="{model}">
                        <span class="category-badge">{category}</span>
                        <div class="car-content">
                            <div class="car-title">{model} ({year})</div>
                            <div class="car-price">{format_currency(price)}/day</div>
                            <div class="car-location">📍 {location}</div>
                            <div class="car-specs">
                """, unsafe_allow_html=True)
                
                # Parse specs
                try:
                    car_specs = json.loads(specs)
                    st.markdown(f"""
                                <span class="spec-item">🏎️ {car_specs['engine'][:15]}...</span>
                                <span class="spec-item">⚙️ {car_specs['transmission']}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                except:
                    st.markdown("""
                                <span class="spec-item">🏎️ Premium Engine</span>
                                <span class="spec-item">⚙️ Automatic</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Add View Details button below the card
                if st.button(f'View Details', key=f'view_{car_id}'):
                    st.session_state.selected_car = {
                        'id': car_id,
                        'model': model,
                        'year': year,
                        'price': price,
                        'location': location,
                        'description': description,
                        'category': category,
                        'specs': specs,
                        'image': image,
                        'owner_email': owner_email
                    }
                    st.session_state.current_page = 'car_details'
                    st.rerun()
    
    # Action buttons with better layout
    st.markdown("<div class='welcome-cta' style='margin-top: 3rem;'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button('Login', key='welcome_login', use_container_width=True):
                st.session_state.current_page = 'login'
            
            if st.button('Browse Cars', key='welcome_browse', use_container_width=True):
                st.session_state.current_page = 'browse_cars'
        
        with col_b:
            if st.button('Create Account', key='welcome_signup', use_container_width=True):
                st.session_state.current_page = 'signup'
            
            if st.button('About Us', key='welcome_about', use_container_width=True):
                st.session_state.current_page = 'about_us'
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # App features section
    st.markdown("<h2 style='text-align: center; margin: 3rem 0 2rem;'>Why Choose Luxury Car Rentals</h2>", unsafe_allow_html=True)
    
    features_col1, features_col2, features_col3 = st.columns(3)
    
    with features_col1:
        st.markdown("""
            <div class="card">
                <h3 style="text-align: center;">🏆 Premium Selection</h3>
                <p>Access to the finest luxury and sports cars in Dubai. From Lamborghinis to Rolls Royces, we've got your dream car ready.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with features_col2:
        st.markdown("""
            <div class="card">
                <h3 style="text-align: center;">🛡️ Comprehensive Insurance</h3>
                <p>Drive with peace of mind with our premium insurance options and 24/7 roadside assistance for all rentals.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with features_col3:
        st.markdown("""
            <div class="card">
                <h3 style="text-align: center;">🌱 Eco-Conscious</h3>
                <p>Dedicated to sustainable luxury with our growing electric vehicle fleet and carbon offset program for every rental.</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Testimonials
    st.markdown("<h2 style='text-align: center; margin: 3rem 0 2rem;'>What Our Customers Say</h2>", unsafe_allow_html=True)
    
    testimonials_col1, testimonials_col2, testimonials_col3 = st.columns(3)
    
    with testimonials_col1:
        st.markdown("""
            <div class="card">
                <p style="font-style: italic;">"The Ferrari 488 Spider was immaculate and the delivery service was right on time. Perfect way to experience Dubai in style."</p>
                <p style="text-align: right; font-weight: bold;">- James K. ⭐⭐⭐⭐⭐</p>
            </div>
        """, unsafe_allow_html=True)
    
    with testimonials_col2:
        st.markdown("""
            <div class="card">
                <p style="font-style: italic;">"As a car enthusiast, I appreciate how well-maintained these exotic cars are. The Lamborghini Huracan was a dream to drive along Jumeirah Beach."</p>
                <p style="text-align: right; font-weight: bold;">- Sarah M. ⭐⭐⭐⭐⭐</p>
            </div>
        """, unsafe_allow_html=True)
    
    with testimonials_col3:
        st.markdown("""
            <div class="card">
                <p style="font-style: italic;">"The VIP service is worth every dirham. Having the car delivered to my hotel with a full walkthrough made the experience seamless."</p>
                <p style="text-align: right; font-weight: bold;">- Ahmed R. ⭐⭐⭐⭐⭐</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
        <div style="background-color: #2E1A47; color: white; padding: 2rem 0; margin-top: 4rem; text-align: center;">
            <p>© 2025 Luxury Car Rentals | Dubai, UAE</p>
            <p>Email: info@luxurycarrentals.ae | Phone: +971 4 123 4567</p>
        </div>
    """, unsafe_allow_html=True)

def login_page():
    st.markdown("""
        <div style="max-width: 500px; margin: 0 auto; padding: 2rem;">
            <h1 style="text-align: center; margin-bottom: 2rem;">Welcome Back</h1>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        with st.form("login_form"):
            email = st.text_input('Email')
            password = st.text_input('Password', type='password')
            login_button = st.form_submit_button('Login')
            
            if login_button:
                # Special case for admin
                if email == "admin@luxuryrentals.com" and password == "admin123":
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.current_page = 'admin_dashboard'
                    st.success('Admin login successful!')
                    st.rerun()
                # Regular user authentication    
                elif verify_user(email, password):
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    
                    # Get user role
                    role = get_user_role(email)
                    
                    if role == 'admin':
                        st.session_state.current_page = 'admin_dashboard'
                        st.success('Admin login successful!')
                    else:
                        st.session_state.current_page = 'browse_cars'
                        st.success('Login successful!')
                    
                    st.rerun()
                else:
                    st.error('Invalid credentials')
        
        st.markdown("<div style='text-align: center; margin-top: 1rem;'>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button('Forgot Password?', key='forgot_password'):
                st.session_state.current_page = 'reset_password'
        with col_b:
            if st.button('Create Account', key='to_signup'):
                st.session_state.current_page = 'signup'
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Back button
    with st.container():
        st.markdown("""
            <div style="position: fixed; top: 1rem; left: 1rem;">
                <a href="#" onclick="window.history.back(); return false;" style="text-decoration: none; color: #555; display: flex; align-items: center;">
                    <span style="font-size: 1.5rem; margin-right: 0.5rem;">←</span> Back
                </a>
            </div>
        """, unsafe_allow_html=True)
        if st.button('← Back to Welcome', key='login_back'):
            st.session_state.current_page = 'welcome'

def signup_page():
    st.markdown("""
        <div style="max-width: 600px; margin: 0 auto; padding: 2rem;">
            <h1 style="text-align: center; margin-bottom: 2rem;">Create Your Account</h1>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        with st.form("signup_form"):
            full_name = st.text_input('Full Name*')
            email = st.text_input('Email*')
            phone = st.text_input('Phone Number*')
            password = st.text_input('Password*', type='password')
            confirm_password = st.text_input('Confirm Password*', type='password')
            
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
            
            # Terms and privacy
            agree = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            submitted = st.form_submit_button("Create Account")
            
            if submitted:
                if password != confirm_password:
                    st.error('Passwords do not match')
                elif not all([full_name, email, phone, password, agree]):
                    st.error('Please fill in all required fields and accept the terms')
                else:
                    if create_user(full_name, email, phone, password, profile_pic_data):
                        st.success('Account created successfully!')
                        # Show animation and redirect
                        st.markdown("""
                            <div style="text-align: center; margin-top: 2rem;">
                                <div class="success-message">
                                    Account created successfully! Redirecting to login...
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        time.sleep(2)
                        st.session_state.current_page = 'login'
                        st.rerun()
                    else:
                        st.error('Email already exists')
        
        st.markdown("<div style='text-align: center; margin-top: 1rem;'>", unsafe_allow_html=True)
        if st.button('Already have an account? Login here', key='to_login'):
            st.session_state.current_page = 'login'
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Back button
    with st.container():
        if st.button('← Back to Welcome', key='signup_back'):
            st.session_state.current_page = 'welcome'

def browse_cars_page():
    st.markdown("<h1>Explore Our Luxury Fleet</h1>", unsafe_allow_html=True)
    
    # Enhanced search and filter section
    st.markdown("<div class='card' style='padding: 1.5rem; margin-bottom: 2rem;'>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search = st.text_input('Search for your dream car', value=st.session_state.search_query, placeholder='e.g., "Lamborghini", "Electric", "SUV"')
        st.session_state.search_query = search
    
    with col2:
        sort_by = st.selectbox('Sort by', ['Newest', 'Price: Low to High', 'Price: High to Low'])
    
    # Category filters with better UI
    st.markdown("<h3 style='margin-top: 1rem; margin-bottom: 0.5rem;'>Categories</h3>", unsafe_allow_html=True)
    
    categories = get_car_categories()
    cols = st.columns(len(categories))
    
    selected_category = None
    for i, category in enumerate(categories):
        with cols[i]:
            if st.button(f'{category}', key=f'cat_{category}', use_container_width=True):
                selected_category = category
                st.session_state.filter_category = category
    
    if selected_category is None:
        selected_category = st.session_state.filter_category
    
    # Price range slider
    price_range = st.slider('Price Range (AED/day)', 500, 5000, (500, 5000))
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Display cars with improved UI
    display_cars(search, selected_category, price_range, sort_by)
    
    # Floating action button for listing a car (shown only for logged-in users)
    if st.session_state.logged_in:
        st.markdown("""
            <div class="floating-button" onclick="document.getElementById('list_car_btn').click();">
                +
            </div>
        """, unsafe_allow_html=True)
        
        if st.button('List Your Car', key='list_car_btn'):
            st.session_state.current_page = 'list_your_car'
            st.rerun()
        

def display_cars(search="", category="All", price_range=(500, 5000), sort_by="Newest"):
    # Connect to database and fetch cars
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Base query for approved listings with primary images
    query = '''
        SELECT cl.*, li.image_data 
        FROM car_listings cl
        LEFT JOIN listing_images li ON cl.id = li.listing_id AND li.is_primary = TRUE
        WHERE cl.listing_status = 'approved'
    '''
    
    params = []
    
    # Add category filter if not "All"
    if category != "All":
        query += " AND cl.category = ?"
        params.append(category)
    
    # Add price range filter
    query += " AND cl.price BETWEEN ? AND ?"
    params.extend([price_range[0], price_range[1]])
    
    # Add search filter
    if search:
        query += " AND (cl.model LIKE ? OR cl.description LIKE ? OR cl.category LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])
    
    # Add sorting
    if sort_by == "Price: Low to High":
        query += " ORDER BY cl.price ASC"
    elif sort_by == "Price: High to Low":
        query += " ORDER BY cl.price DESC"
    else:  # Newest
        query += " ORDER BY cl.created_at DESC"
    
    c.execute(query, params)
    cars = c.fetchall()
    
    # Get average ratings for each car
    car_ratings = {}
    for car in cars:
        car_id = car[0]
        c.execute('''
            SELECT AVG(rating), COUNT(rating)
            FROM reviews
            WHERE car_id = ?
        ''', (car_id,))
        rating_data = c.fetchone()
        avg_rating = round(rating_data[0], 1) if rating_data[0] else 0
        num_ratings = rating_data[1] if rating_data[1] else 0
        car_ratings[car_id] = (avg_rating, num_ratings)
    
    conn.close()
    
    if not cars:
        st.info("No cars found matching your criteria.")
        return
    
    # Display cars in a grid
    cols = st.columns(3)
    for idx, car in enumerate(cars):
        car_id, owner_email, model, year, price, location, description, category, specs, status, created_at, image = car
        with cols[idx % 3]:
            avg_rating, num_ratings = car_ratings.get(car_id, (0, 0))
            rating_stars = "⭐" * int(avg_rating) + "☆" * (5 - int(avg_rating))
            
            st.markdown(f"""
                <div class="car-card">
                    <img src="data:image/jpeg;base64,{image}" class="car-image" alt="{model}">
                    <span class="category-badge">{category}</span>
                    <div class="car-content">
                        <div class="car-title">{model} ({year})</div>
                        <div class="car-price">{format_currency(price)}/day</div>
                        <div class="car-location">📍 {location}</div>
                        <div style="font-size: 0.9rem; margin: 0.5rem 0;">
                            {rating_stars} <span style="color: #666;">({num_ratings} reviews)</span>
                        </div>
                        <div class="car-specs">
            """, unsafe_allow_html=True)
            
            # Parse specs
            try:
                car_specs = json.loads(specs)
                st.markdown(f"""
                            <span class="spec-item">🏎️ {car_specs['engine'][:15]}...</span>
                            <span class="spec-item">⚙️ {car_specs['transmission']}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except:
                st.markdown("""
                            <span class="spec-item">🏎️ Premium Engine</span>
                            <span class="spec-item">⚙️ Automatic</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # View Details button
            if st.button('View Details', key=f'view_{car_id}'):
                st.session_state.selected_car = {
                    'id': car_id,
                    'model': model,
                    'year': year,
                    'price': price,
                    'location': location,
                    'description': description,
                    'category': category,
                    'specs': specs,
                    'image': image,
                    'owner_email': owner_email
                }
                st.session_state.current_page = 'car_details'
                st.rerun()
        
        # Create a new row after every 3 cars
        if (idx + 1) % 3 == 0 and idx + 1 < len(cars):
            st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

def show_car_details(car):
    # Connect to database
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Fetch additional images for this car
    c.execute('SELECT image_data FROM listing_images WHERE listing_id = ?', (car['id'],))
    images = c.fetchall()
    
    # Get average rating for this car
    c.execute('''
        SELECT AVG(rating), COUNT(rating)
        FROM reviews
        WHERE car_id = ?
    ''', (car['id'],))
    rating_data = c.fetchone()
    avg_rating = round(rating_data[0], 1) if rating_data[0] else 0
    num_ratings = rating_data[1] if rating_data[1] else 0
    
    # Get car features
    try:
        specs = json.loads(car['specs']) if isinstance(car['specs'], str) else car['specs']
    except json.JSONDecodeError:
        specs = {}
    
    # Create a back button that preserves filters
    if st.button('← Back to Browse', key='back_to_browse'):
        st.session_state.current_page = 'browse_cars'
        st.session_state.selected_car = None
        st.rerun()
    
    # Main content
    st.markdown(f"<h1>{car['model']} ({car['year']})</h1>", unsafe_allow_html=True)
    
    # Image gallery in a carousel-like layout
    if images:
        st.markdown("<div class='image-gallery'>", unsafe_allow_html=True)
        for img_data, in images:
            st.markdown(f"""
                <img src="data:image/jpeg;base64,{img_data}" alt="{car['model']}" />
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Price and ratings
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"""
            <div style="font-size: 2rem; font-weight: 700; color: var(--primary-color); margin-bottom: 1rem;">
                {format_currency(car['price'])}<span style="font-size: 1rem; font-weight: normal; color: var(--text-light);"> / day</span>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        rating_stars = "⭐" * int(avg_rating) + "☆" * (5 - int(avg_rating))
        st.markdown(f"""
            <div style="font-size: 1.2rem; margin-bottom: 1rem;">
                {rating_stars} <span style="color: var(--text-light); font-size: 1rem;">({num_ratings} reviews)</span>
            </div>
            <div style="font-size: 1.1rem; color: var(--text-light);">
                📍 {car['location']}
            </div>
        """, unsafe_allow_html=True)
    
    # Car description 
    st.markdown(f"""
        <div class="card" style="margin: 1.5rem 0;">
            <h3>Description</h3>
            <p>{car['description']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Car specifications
    st.markdown("""
        <div class="card" style="margin: 1.5rem 0;">
            <h3>Specifications</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
    """, unsafe_allow_html=True)
    
    # Engine
    st.markdown(f"""
        <div style="display: flex; align-items: center;">
            <div style="width: 40px; height: 40px; background-color: rgba(75, 45, 111, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 1rem;">
                <span style="font-size: 1.2rem;">🏎️</span>
            </div>
            <div>
                <div style="font-size: 0.9rem; color: var(--text-light);">Engine</div>
                <div style="font-weight: 500;">{specs.get('engine', 'Premium Engine')}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Transmission
    st.markdown(f"""
        <div style="display: flex; align-items: center;">
            <div style="width: 40px; height: 40px; background-color: rgba(75, 45, 111, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 1rem;">
                <span style="font-size: 1.2rem;">⚙️</span>
            </div>
            <div>
                <div style="font-size: 0.9rem; color: var(--text-light);">Transmission</div>
                <div style="font-weight: 500;">{specs.get('transmission', 'Automatic')}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Mileage
    st.markdown(f"""
        <div style="display: flex; align-items: center;">
            <div style="width: 40px; height: 40px; background-color: rgba(75, 45, 111, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 1rem;">
                <span style="font-size: 1.2rem;">📊</span>
            </div>
            <div>
                <div style="font-size: 0.9rem; color: var(--text-light);">Mileage</div>
                <div style="font-weight: 500;">{specs.get('mileage', 'Low')} km</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Category
    st.markdown(f"""
        <div style="display: flex; align-items: center;">
            <div style="width: 40px; height: 40px; background-color: rgba(75, 45, 111, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 1rem;">
                <span style="font-size: 1.2rem;">🚗</span>
            </div>
            <div>
                <div style="font-size: 0.9rem; color: var(--text-light);">Category</div>
                <div style="font-weight: 500;">{car['category']}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Features
    if 'features' in specs:
        features = specs['features']
        st.markdown("""
            <div class="card" style="margin: 1.5rem 0;">
                <h3>Features</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
        """, unsafe_allow_html=True)
        
        feature_icons = {
            'leather_seats': '🪑',
            'bluetooth': '🔊',
            'parking_sensors': '📡',
            'cruise_control': '🎮',
            'sunroof': '☀️',
            'navigation': '🗺️'
        }
        
        for feature, has_feature in features.items():
            if has_feature:
                icon = feature_icons.get(feature, '✓')
                feature_name = feature.replace('_', ' ').title()
                st.markdown(f"""
                    <div style="display: flex; align-items: center;">
                        <div style="width: 30px; text-align: center; margin-right: 1rem;">
                            <span style="font-size: 1.2rem;">{icon}</span>
                        </div>
                        <div style="font-weight: 500;">{feature_name}</div>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Reviews section
    st.markdown("""
        <div class="card" style="margin: 1.5rem 0;">
            <h3>Customer Reviews</h3>
    """, unsafe_allow_html=True)
    
    # Fetch reviews
    c.execute('''
        SELECT r.*, u.full_name, u.profile_picture
        FROM reviews r
        JOIN users u ON r.user_email = u.email
        WHERE r.car_id = ?
        ORDER BY r.created_at DESC
        LIMIT 5
    ''', (car['id'],))
    
    reviews = c.fetchall()
    
    if reviews:
        for review in reviews:
            review_id, booking_id, user_email, car_id, rating, comment, created_at, user_name, profile_pic = review
            rating_stars = "⭐" * rating
            
            profile_img = f"data:image/jpeg;base64,{profile_pic}" if profile_pic else "https://ui-avatars.com/api/?name={user_name}&background=random"
            
            st.markdown(f"""
                <div style="padding: 1rem 0; border-bottom: 1px solid #eee;">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <img src="{profile_img}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; margin-right: 1rem;" />
                        <div>
                            <div style="font-weight: 500;">{user_name}</div>
                            <div style="font-size: 0.8rem; color: var(--text-light);">{created_at[:10]}</div>
                        </div>
                    </div>
                    <div style="margin-bottom: 0.5rem;">{rating_stars}</div>
                    <p>{comment}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <p style="color: var(--text-light);">No reviews yet for this car.</p>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Booking button (only show if logged in)
    # Booking button (only show if logged in)
    if st.session_state.logged_in:
        if st.button('Book Now', key='book_now_btn'):
            st.session_state.current_page = 'book_car'
            st.rerun()
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button('Login to Book', key='login_to_book'):
                st.session_state.current_page = 'login'
                st.rerun()
        with col2:
            if st.button('Create Account', key='create_to_book'):
                st.session_state.current_page = 'signup'
                st.rerun()
    
    conn.close()

def book_car_page():
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
    
    # Back button
    if st.button('← Back to Car Details', key='back_to_car'):
        st.session_state.current_page = 'car_details'
        st.rerun()
    
    # Header
    st.markdown(f"<h1>Book {car['model']} ({car['year']})</h1>", unsafe_allow_html=True)
    
    # Car image and basic info
    col1, col2 = st.columns([2, 3])
    with col1:
        st.image(f"data:image/jpeg;base64,{car['image']}", caption=f"{car['model']} ({car['year']})")
    
    with col2:
        st.markdown(f"""
            <div style="padding: 1rem; background-color: rgba(75, 45, 111, 0.05); border-radius: 10px;">
                <div style="font-size: 1.5rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--primary-color);">{car['model']} ({car['year']})</div>
                <div style="font-size: 1.2rem; margin-bottom: 0.5rem; color: var(--secondary-color);">{format_currency(car['price'])}/day</div>
                <div style="font-size: 1rem; color: var(--text-light);">📍 {car['location']}</div>
            </div>
        """, unsafe_allow_html=True)
    
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
    
    # Show subscription benefits if applicable
    if subscription_type != 'free_renter':
        benefits = get_subscription_benefits(subscription_type)
        st.markdown(f"""
            <div style="background-color: rgba(255, 211, 105, 0.2); padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid var(--accent-color);">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.2rem; margin-right: 0.5rem;">🏆</span>
                    <span style="font-weight: 600; color: var(--primary-color);">{subscription_type.replace('_', ' ').title()} Subscription Benefits</span>
                </div>
                <ul style="margin: 0.5rem 0 0 1.5rem; padding: 0;">
                    <li>Enjoy a {discount_percentage}% discount on this rental</li>
                    <li>{benefits['damage_waiver']}</li>
                    <li>{benefits['cancellations']}</li>
                    <li>{benefits['roadside_assistance']}</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    # Enhanced booking form with better UX
    with st.form("booking_form"):
        st.markdown("<h3>Booking Details</h3>", unsafe_allow_html=True)
        
        # Date selection with improved layout
        col1, col2 = st.columns(2)
        with col1:
            pickup_date = st.date_input("Pickup Date", min_value=datetime.now().date())
        with col2:
            return_date = st.date_input("Return Date", min_value=pickup_date)
        
        # Location with description
        st.markdown("""
            <div style="margin-bottom: 0.5rem; font-size: 0.9rem; color: var(--text-light);">
                Select where you'd like to pick up the vehicle
            </div>
        """, unsafe_allow_html=True)
        location = st.selectbox("Pickup Location", get_location_options())
        
        # Additional Services with descriptions and visual improvements
        st.markdown("<h3>Additional Services</h3>", unsafe_allow_html=True)
        
        # Insurance
        insurance_col1, insurance_col2 = st.columns([5, 1])
        with insurance_col1:
            st.markdown(f"""
                <div style="font-weight: 500;">Insurance Protection</div>
                <div style="font-size: 0.9rem; color: var(--text-light);">
                    Comprehensive coverage for accidents, theft, and damages
                </div>
            """, unsafe_allow_html=True)
        with insurance_col2:
            insurance = st.checkbox(f"{format_currency(service_prices['insurance'])}/day", key="insurance_checkbox")
        
        # Driver
        driver_col1, driver_col2 = st.columns([5, 1])
        with driver_col1:
            st.markdown(f"""
                <div style="font-weight: 500;">Professional Driver</div>
                <div style="font-size: 0.9rem; color: var(--text-light);">
                    Experienced chauffeur familiar with Dubai's roads
                </div>
            """, unsafe_allow_html=True)
        with driver_col2:
            driver = st.checkbox(f"{format_currency(service_prices['driver'])}/day", key="driver_checkbox")
        
        # Delivery
        delivery_col1, delivery_col2 = st.columns([5, 1])
        with delivery_col1:
            st.markdown(f"""
                <div style="font-weight: 500;">Delivery Service</div>
                <div style="font-size: 0.9rem; color: var(--text-light);">
                    Car delivery and pickup at your location
                </div>
            """, unsafe_allow_html=True)
        with delivery_col2:
            delivery = st.checkbox(f"{format_currency(service_prices['delivery'])}", key="delivery_checkbox")
        
        # VIP Service
        vip_col1, vip_col2 = st.columns([5, 1])
        with vip_col1:
            st.markdown(f"""
                <div style="font-weight: 500;">VIP Experience</div>
                <div style="font-size: 0.9rem; color: var(--text-light);">
                    Priority service, complimentary refreshments, and premium customer support
                </div>
            """, unsafe_allow_html=True)
        with vip_col2:
            vip_service = st.checkbox(f"{format_currency(service_prices['vip_service'])}", key="vip_checkbox")
        
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
        
        # Display price breakdown in a more visually appealing format
        st.markdown("<h3>Price Breakdown</h3>", unsafe_allow_html=True)
        
        st.markdown("""
            <div class="price-breakdown">
        """, unsafe_allow_html=True)
        
        # Base rental
        st.markdown(f"""
            <div class="price-item">
                <span>Base Rental ({rental_days} {'day' if rental_days == 1 else 'days'})</span>
                <span>{format_currency(base_price)}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Additional services
        if insurance:
            st.markdown(f"""
                <div class="price-item">
                    <span>Insurance</span>
                    <span>{format_currency(insurance_price)}</span>
                </div>
            """, unsafe_allow_html=True)
        
        if driver:
            st.markdown(f"""
                <div class="price-item">
                    <span>Professional Driver</span>
                    <span>{format_currency(driver_price)}</span>
                </div>
            """, unsafe_allow_html=True)
        
        if delivery:
            st.markdown(f"""
                <div class="price-item">
                    <span>Delivery Service</span>
                    <span>{format_currency(delivery_price)}</span>
                </div>
            """, unsafe_allow_html=True)
        
        if vip_service:
            st.markdown(f"""
                <div class="price-item">
                    <span>VIP Experience</span>
                    <span>{format_currency(vip_service_price)}</span>
                </div>
            """, unsafe_allow_html=True)
        
        # Subtotal
        st.markdown(f"""
            <div class="price-item">
                <span><strong>Subtotal</strong></span>
                <span><strong>{format_currency(subtotal)}</strong></span>
            </div>
        """, unsafe_allow_html=True)
        
        # Discount
        if discount_amount > 0:
            st.markdown(f"""
                <div class="price-item" style="color: var(--success-color);">
                    <span>{subscription_type.replace('_', ' ').title()} Discount ({discount_percentage}%)</span>
                    <span>-{format_currency(discount_amount)}</span>
                </div>
            """, unsafe_allow_html=True)
        
        # Total
        st.markdown(f"""
            <div class="price-total">
                <span>Total</span>
                <span>{format_currency(total_price)}</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Payment method
        st.markdown("<h3>Payment Method</h3>", unsafe_allow_html=True)
        payment_method = st.radio(
            "Select your payment method",
            ["Credit Card", "Debit Card", "PayPal", "Apple Pay"],
            horizontal=True
        )
        
        # Terms and conditions
        agree = st.checkbox("I agree to the Terms and Conditions")
        
        # Submit booking
        submit = st.form_submit_button("Confirm Booking")
        
        if submit:
            if not agree:
                st.error("Please agree to the Terms and Conditions")
            else:
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
                    
                    # Show success message with animation
                    st.success("Booking confirmed successfully!")
                    st.balloons()
                    
                    # Add delay for better user experience
                    time.sleep(2)
                    
                    # Reset selected car and move to my bookings
                    st.session_state.selected_car = None
                    st.session_state.current_page = 'my_bookings'
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"An error occurred while booking: {str(e)}")
                finally:
                    if 'conn' in locals():
                        conn.close()

def admin_dashboard():
    """Enhanced admin dashboard with analytics and overview"""
    st.markdown("<h1>Admin Dashboard</h1>", unsafe_allow_html=True)
    
    # Key metrics in cards
    col1, col2, col3, col4 = st.columns(4)
    
    # Connect to database
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Total active listings
    c.execute('''
        SELECT COUNT(*) FROM car_listings 
        WHERE listing_status = 'approved'
    ''')
    active_listings = c.fetchone()[0]
    
    # Total bookings (last 30 days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    c.execute('''
        SELECT COUNT(*) FROM bookings
        WHERE created_at >= ?
    ''', (thirty_days_ago,))
    recent_bookings = c.fetchone()[0]
    
    # Total revenue (last 30 days)
    c.execute('''
        SELECT SUM(total_price) FROM bookings
        WHERE created_at >= ?
    ''', (thirty_days_ago,))
    recent_revenue = c.fetchone()[0] or 0
    
    # Pending approvals
    c.execute('''
        SELECT COUNT(*) FROM car_listings 
        WHERE listing_status = 'pending'
    ''')
    pending_approvals = c.fetchone()[0]
    
    # Display metrics with icons
    with col1:
        st.markdown("""
            <div class="dashboard-card">
                <div class="dashboard-card-title">Active Listings</div>
                <div class="dashboard-card-value">{}</div>
                <div class="dashboard-card-change positive">↑ 12% from last month</div>
            </div>
        """.format(active_listings), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="dashboard-card">
                <div class="dashboard-card-title">Bookings (30 days)</div>
                <div class="dashboard-card-value">{}</div>
                <div class="dashboard-card-change positive">↑ 8% from last month</div>
            </div>
        """.format(recent_bookings), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="dashboard-card">
                <div class="dashboard-card-title">Revenue (30 days)</div>
                <div class="dashboard-card-value">{}</div>
                <div class="dashboard-card-change positive">↑ 15% from last month</div>
            </div>
        """.format(format_currency(recent_revenue)), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="dashboard-card">
                <div class="dashboard-card-title">Pending Approvals</div>
                <div class="dashboard-card-value">{}</div>
                <div class="dashboard-card-change">Requires attention</div>
            </div>
        """.format(pending_approvals), unsafe_allow_html=True)
    
    # Tabs for different admin sections
    admin_tabs = st.tabs([
        "Overview", 
        "Pending Listings", 
        "Manage Bookings", 
        "Insurance Claims", 
        "User Management"
    ])
    
    with admin_tabs[0]:
        show_admin_overview(c)
    
    with admin_tabs[1]:
        show_pending_listings(c)
    
    with admin_tabs[2]:
        show_admin_bookings(c)
    
    with admin_tabs[3]:
        show_admin_insurance_claims(c)
    
    with admin_tabs[4]:
        show_user_management(c)
    
    conn.close()

def show_admin_overview(c):
    """Admin dashboard overview tab with charts and analytics"""
    st.markdown("<h2>Business Overview</h2>", unsafe_allow_html=True)
    
    # Get booking data for the past 90 days
    ninety_days_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    c.execute('''
        SELECT strftime('%Y-%m-%d', created_at) as date, COUNT(*) as count, SUM(total_price) as revenue
        FROM bookings
        WHERE created_at >= ?
        GROUP BY strftime('%Y-%m-%d', created_at)
        ORDER BY date
    ''', (ninety_days_ago,))
    
    booking_data = c.fetchall()
    
    # Convert to DataFrame for easier plotting
    if booking_data:
        df_bookings = pd.DataFrame(booking_data, columns=['date', 'count', 'revenue'])
        df_bookings['date'] = pd.to_datetime(df_bookings['date'])
        
        # Fill in missing dates with zeros
        date_range = pd.date_range(start=df_bookings['date'].min(), end=df_bookings['date'].max())
        df_filled = pd.DataFrame({'date': date_range})
        df_bookings = pd.merge(df_filled, df_bookings, on='date', how='left').fillna(0)
        
        # Calculate 7-day rolling average
        df_bookings['bookings_7d_avg'] = df_bookings['count'].rolling(7).mean()
        df_bookings['revenue_7d_avg'] = df_bookings['revenue'].rolling(7).mean()
        
        # Booking trends
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<h3>Booking Trends</h3>", unsafe_allow_html=True)
            fig_bookings = px.line(
                df_bookings, 
                x='date', 
                y=['count', 'bookings_7d_avg'], 
                labels={'value': 'Bookings', 'date': 'Date', 'variable': 'Metric'},
                title='Daily Bookings with 7-Day Average',
                color_discrete_map={'count': '#6A0DAD', 'bookings_7d_avg': '#4B0082'}
            )
            fig_bookings.update_layout(
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=400
            )
            st.plotly_chart(fig_bookings, use_container_width=True)
        
        with col2:
            st.markdown("<h3>Revenue Trends</h3>", unsafe_allow_html=True)
            fig_revenue = px.line(
                df_bookings, 
                x='date', 
                y=['revenue', 'revenue_7d_avg'], 
                labels={'value': 'Revenue (AED)', 'date': 'Date', 'variable': 'Metric'},
                title='Daily Revenue with 7-Day Average',
                color_discrete_map={'revenue': '#FFD369', 'revenue_7d_avg': '#FFA500'}
            )
            fig_revenue.update_layout(
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=400
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Get category distribution
    c.execute('''
        SELECT cl.category, COUNT(*) as count
        FROM bookings b
        JOIN car_listings cl ON b.car_id = cl.id
        WHERE b.created_at >= ?
        GROUP BY cl.category
        ORDER BY count DESC
    ''', (ninety_days_ago,))
    
    category_data = c.fetchall()
    
    # Location distribution
    c.execute('''
        SELECT location, COUNT(*) as count
        FROM bookings
        WHERE created_at >= ?
        GROUP BY location
        ORDER BY count DESC
    ''', (ninety_days_ago,))
    
    location_data = c.fetchall()
    
    # Display in columns
    if category_data and location_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<h3>Popular Car Categories</h3>", unsafe_allow_html=True)
            df_categories = pd.DataFrame(category_data, columns=['category', 'count'])
            fig_categories = px.pie(
                df_categories, 
                names='category', 
                values='count',
                title='Bookings by Car Category',
                color_discrete_sequence=px.colors.sequential.Agsunset
            )
            fig_categories.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_categories, use_container_width=True)
        
        with col2:
            st.markdown("<h3>Popular Locations</h3>", unsafe_allow_html=True)
            df_locations = pd.DataFrame(location_data, columns=['location', 'count'])
            fig_locations = px.bar(
                df_locations, 
                x='location', 
                y='count',
                title='Bookings by Location',
                color='count',
                color_continuous_scale=px.colors.sequential.Agsunset
            )
            fig_locations.update_layout(xaxis_title='Location', yaxis_title='Number of Bookings')
            st.plotly_chart(fig_locations, use_container_width=True)
    
    # Latest activity section
    st.markdown("<h3>Recent Activity</h3>", unsafe_allow_html=True)
    
    # Get latest bookings
    c.execute('''
        SELECT b.id, u.full_name, cl.model, cl.year, b.pickup_date, b.return_date, b.total_price, b.created_at
        FROM bookings b
        JOIN users u ON b.user_email = u.email
        JOIN car_listings cl ON b.car_id = cl.id
        ORDER BY b.created_at DESC
        LIMIT 5
    ''')
    
    recent_bookings = c.fetchall()
    
    if recent_bookings:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h4>Latest Bookings</h4>", unsafe_allow_html=True)
        
        for booking in recent_bookings:
            booking_id, user_name, car_model, car_year, pickup_date, return_date, total_price, created_at = booking
            st.markdown(f"""
                <div style="padding: 0.8rem 0; border-bottom: 1px solid #eee;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>#{booking_id}</strong> - {user_name} booked {car_model} ({car_year})
                        </div>
                        <div style="color: var(--secondary-color); font-weight: 600;">
                            {format_currency(total_price)}
                        </div>
                    </div>
                    <div style="font-size: 0.9rem; color: var(--text-light); margin-top: 0.3rem;">
                        {pickup_date} to {return_date} • Booked on {created_at[:10]}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

def show_pending_listings(c):
    """Enhanced pending listings tab with better UI"""
    st.markdown("<h2>Pending Listings</h2>", unsafe_allow_html=True)
    
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
        return
    
    # Display each listing in a card
    for listing in pending_listings:
        listing_id = listing[0]
        
        # Get images for this listing
        c.execute('SELECT image_data FROM listing_images WHERE listing_id = ?', (listing_id,))
        images = c.fetchall()
        
        with st.container():
            st.markdown(f"""
                <div class="admin-review-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3 style="margin: 0;">{listing[2]} ({listing[3]})</h3>
                        <span class="status-badge pending">PENDING</span>
                    </div>
                    <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                        <div style="flex: 1;">
                            <p><strong>Owner:</strong> {listing[11]} ({listing[12]})</p>
                            <p><strong>Phone:</strong> {listing[13]}</p>
                            <p><strong>Price:</strong> {format_currency(listing[4])}/day</p>
                            <p><strong>Location:</strong> {listing[5]}</p>
                            <p><strong>Category:</strong> {listing[7]}</p>
                        </div>
                        <div style="flex: 2;">
                            <p><strong>Description:</strong> {listing[6]}</p>
                            <p><strong>Submitted:</strong> {listing[10]}</p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Display images in a grid
            if images:
                st.markdown("<div class='image-gallery'>", unsafe_allow_html=True)
                for img_data, in images:
                    st.markdown(f"""
                        <img src="data:image/jpeg;base64,{img_data}" alt="Car Image">
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Review form with better UI
            col1, col2 = st.columns([3, 1])
            
            with col1:
                review_comment = st.text_area(f"Review Comment for Listing #{listing_id}", key=f"comment_{listing_id}")
            
            with col2:
                st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)
                approve_col, reject_col = st.columns(2)
                
                with approve_col:
                    if st.button("✅ Approve", key=f"approve_{listing_id}"):
                        process_listing_review(listing_id, 'approved', review_comment)
                        st.success(f"Listing #{listing_id} approved!")
                        st.rerun()
                
                with reject_col:
                    if st.button("❌ Reject", key=f"reject_{listing_id}"):
                        process_listing_review(listing_id, 'rejected', review_comment)
                        st.success(f"Listing #{listing_id} rejected!")
                        st.rerun()
            
            st.markdown("<hr>", unsafe_allow_html=True)

def process_listing_review(listing_id, status, comment):
    """Process a listing review (approve/reject)"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Get the owner email
        c.execute('SELECT owner_email FROM car_listings WHERE id = ?', (listing_id,))
        owner_email = c.fetchone()[0]
        
        # Update listing status
        c.execute('''
            UPDATE car_listings 
            SET listing_status = ? 
            WHERE id = ?
        ''', (status, listing_id))
        
        # Add admin review
        c.execute('''
            INSERT INTO admin_reviews 
            (listing_id, admin_email, comment, review_status)
            VALUES (?, ?, ?, ?)
        ''', (
            listing_id,
            st.session_state.user_email,
            comment,
            status
        ))
        
        # Create notification for owner
        create_notification(
            owner_email,
            f"Your listing for car ID #{listing_id} has been {status}. {comment if comment else ''}",
            f'listing_{status}'
        )
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error processing listing review: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def show_admin_bookings(c):
    """Admin bookings management tab"""
    st.markdown("<h2>Manage Bookings</h2>", unsafe_allow_html=True)
    
    # Filters for bookings
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status", 
            ["All", "Pending", "Confirmed", "Rejected", "Completed"]
        )
    
    with col2:
        # Get date range for filter
        date_range = st.date_input(
            "Date Range",
            value=(
                datetime.now().date() - timedelta(days=30),
                datetime.now().date()
            ),
            max_value=datetime.now().date()
        )
    
    with col3:
        search_query = st.text_input("Search by User or Car", placeholder="Enter email or car model")
    
    # Build query based on filters
    query = '''
        SELECT b.*, u.full_name as user_name, cl.model, cl.year, cl.category
        FROM bookings b
        JOIN users u ON b.user_email = u.email
        JOIN car_listings cl ON b.car_id = cl.id
        WHERE 1=1
    '''
    params = []
    
    # Add status filter
    if status_filter != "All":
        query += " AND b.booking_status = ?"
        params.append(status_filter.lower())
    
    # Add date range filter
    if len(date_range) == 2:
        start_date, end_date = date_range
        query += " AND b.created_at BETWEEN ? AND ?"
        params.extend([start_date.strftime('%Y-%m-%d'), (end_date + timedelta(days=1)).strftime('%Y-%m-%d')])
    
    # Add search filter
    if search_query:
        query += " AND (u.email LIKE ? OR u.full_name LIKE ? OR cl.model LIKE ?)"
        search_param = f"%{search_query}%"
        params.extend([search_param, search_param, search_param])
    
    # Add ordering
    query += " ORDER BY b.created_at DESC"
    
    # Execute query
    c.execute(query, params)
    bookings = c.fetchall()
    
    if not bookings:
        st.info("No bookings found matching the criteria.")
        return
    
    # Display bookings in a table with expandable rows
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    # Table header
    st.markdown("""
        <div style="display: grid; grid-template-columns: 0.7fr 1.5fr 1.5fr 1fr 1fr 1fr; font-weight: bold; padding: 0.8rem 0; border-bottom: 2px solid #ddd;">
            <div>ID</div>
            <div>User</div>
            <div>Car</div>
            <div>Dates</div>
            <div>Amount</div>
            <div>Status</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Table rows
    for booking in bookings:
        booking_id = booking[0]
        user_email = booking[1]
        car_id = booking[2]
        pickup_date = booking[3]
        return_date = booking[4]
        location = booking[5]
        total_price = booking[6]
        booking_status = booking[11]
        user_name = booking[17]
        car_model = booking[18]
        car_year = booking[19]
        car_category = booking[20]
        
        # Status class for color coding
        status_class = booking_status.lower()
        
        # Row
        st.markdown(f"""
            <div style="display: grid; grid-template-columns: 0.7fr 1.5fr 1.5fr 1fr 1fr 1fr; padding: 1rem 0; border-bottom: 1px solid #eee; align-items: center;"
                 onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'"
                 style="cursor: pointer;">
                <div>#{booking_id}</div>
                <div>{user_name}<br><span style="font-size: 0.8rem; color: #666;">{user_email}</span></div>
                <div>{car_model} ({car_year})<br><span style="font-size: 0.8rem; color: #666;">{car_category}</span></div>
                <div>{pickup_date}<br>to {return_date}</div>
                <div>{format_currency(total_price)}</div>
                <div><span class="status-badge {status_class}">{booking_status.upper()}</span></div>
            </div>
            <div style="display: none; padding: 1rem; background-color: #f9f9f9; border-radius: 0.5rem; margin: 0.5rem 0 1rem;">
                <h4>Booking Details</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div>
                        <p><strong>Location:</strong> {location}</p>
                        <p><strong>Insurance:</strong> {'Yes' if booking[7] else 'No'}</p>
                        <p><strong>Driver:</strong> {'Yes' if booking[8] else 'No'}</p>
                    </div>
                    <div>
                        <p><strong>Delivery:</strong> {'Yes' if booking[9] else 'No'}</p>
                        <p><strong>VIP Service:</strong> {'Yes' if booking[10] else 'No'}</p>
                        <p><strong>Created:</strong> {booking[12][:16]}</p>
                    </div>
                </div>
        """, unsafe_allow_html=True)
        
        # Show action buttons for pending bookings
        if booking_status.lower() == 'pending':
            st.markdown("""
                <div style="margin-top: 1rem;">
                    <h4>Actions</h4>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("Confirm", key=f"confirm_{booking_id}"):
                    update_booking_status(booking_id, 'confirmed')
                    st.success(f"Booking #{booking_id} confirmed!")
                    st.rerun()
            
            with col2:
                if st.button("Reject", key=f"reject_{booking_id}"):
                    update_booking_status(booking_id, 'rejected')
                    st.success(f"Booking #{booking_id} rejected!")
                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def update_booking_status(booking_id, new_status):
    """Update booking status and send notification"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Get the user email 
        c.execute('SELECT user_email, car_id FROM bookings WHERE id = ?', (booking_id,))
        user_email, car_id = c.fetchone()
        
        # Get car details
        c.execute('SELECT model, year FROM car_listings WHERE id = ?', (car_id,))
        car_model, car_year = c.fetchone()
        
        # Update booking status
        c.execute('''
            UPDATE bookings 
            SET booking_status = ? 
            WHERE id = ?
        ''', (new_status, booking_id))
        
        # Create notification
        create_notification(
            user_email,
            f"Your booking #{booking_id} for {car_model} ({car_year}) has been {new_status}.",
            f'booking_{new_status}'
        )
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating booking status: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def show_admin_insurance_claims(c):
    """Enhanced insurance claims management tab"""
    st.markdown("<h2>Insurance Claims Management</h2>", unsafe_allow_html=True)
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status", 
            ["All", "Pending", "Approved", "Rejected", "Partial", "Paid"]
        )
    
    with col2:
        date_range = st.date_input(
            "Date Range",
            value=(
                datetime.now().date() - timedelta(days=30),
                datetime.now().date()
            ),
            max_value=datetime.now().date()
        )
    
    # Build query based on filters
    query = '''
        SELECT ic.*, u.full_name, b.car_id, cl.model, cl.year
        FROM insurance_claims ic
        JOIN users u ON ic.user_email = u.email
        JOIN bookings b ON ic.booking_id = b.id
        JOIN car_listings cl ON b.car_id = cl.id
        WHERE 1=1
    '''
    params = []
    
    # Add status filter
    if status_filter != "All":
        query += " AND ic.claim_status = ?"
        params.append(status_filter.lower())
    
    # Add date range filter
    if len(date_range) == 2:
        start_date, end_date = date_range
        query += " AND ic.created_at BETWEEN ? AND ?"
        params.extend([start_date.strftime('%Y-%m-%d'), (end_date + timedelta(days=1)).strftime('%Y-%m-%d')])
    
    # Add ordering
    query += " ORDER BY ic.created_at DESC"
    
    # Execute query
    c.execute(query, params)
    claims = c.fetchall()
    
    if not claims:
        st.info("No insurance claims found matching the criteria.")
        return
    
    # Display claims
    for claim in claims:
        claim_id = claim[0]
        booking_id = claim[1]
        user_email = claim[2]
        incident_date = claim[3]
        claim_date = claim[4]
        description = claim[5]
        damage_type = claim[6]
        claim_amount = claim[7]
        evidence_images = claim[8]
        claim_status = claim[9]
        admin_notes = claim[10]
        created_at = claim[11]
        user_name = claim[12]
        car_id = claim[13]
        car_model = claim[14]
        car_year = claim[15]
        
        # Status color
        status_colors = {
            'pending': 'pending',
            'approved': 'approved',
            'rejected': 'rejected',
            'partial': 'pending',
            'paid': 'approved'
        }
        status_class = status_colors.get(claim_status.lower(), 'pending')
        
        with st.container():
            st.markdown(f"""
                <div class="insurance-claim-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3 style="margin: 0;">Claim #{claim_id} - {car_model} ({car_year})</h3>
                        <span class="status-badge {status_class}">{claim_status.upper()}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                        <div>
                            <p><strong>Submitted By:</strong> {user_name}<br><span style="font-size: 0.8rem; color: #666;">{user_email}</span></p>
                            <p><strong>Booking ID:</strong> #{booking_id}</p>
                            <p><strong>Claim Date:</strong> {claim_date}</p>
                        </div>
                        <div>
                            <p><strong>Incident Date:</strong> {incident_date}</p>
                            <p><strong>Damage Type:</strong> {damage_type}</p>
                            <p><strong>Claim Amount:</strong> {format_currency(claim_amount)}</p>
                        </div>
                        <div>
                            <p><strong>Description:</strong> {description}</p>
                        </div>
                    </div>
            """, unsafe_allow_html=True)
            
            # Show evidence images if available
            if evidence_images:
                try:
                    evidence_list = json.loads(evidence_images)
                    if evidence_list:
                        st.markdown("<h4>Evidence Photos</h4>", unsafe_allow_html=True)
                        st.markdown("<div class='image-gallery'>", unsafe_allow_html=True)
                        for img_data in evidence_list:
                            st.markdown(f"""
                                <img src="data:image/jpeg;base64,{img_data}" alt="Evidence Photo">
                            """, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                except json.JSONDecodeError:
                    st.error("Error loading evidence images")
            
            # Show admin notes if available
            if admin_notes:
                st.markdown(f"""
                    <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                        <h4>Admin Notes</h4>
                        <p>{admin_notes}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            # Only show assessment form for pending claims
            if claim_status.lower() == 'pending':
                st.markdown("<h4>Claim Assessment</h4>", unsafe_allow_html=True)
                
                assessment_notes = st.text_area(
                    "Assessment Notes", 
                    placeholder="Provide details about your decision...",
                    key=f"notes_{claim_id}"
                )
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Approve Claim", key=f"approve_{claim_id}"):
                        if process_claim_assessment(claim_id, 'approved', assessment_notes):
                            st.success(f"Claim #{claim_id} approved!")
                            st.rerun()
                
                with col2:
                    if st.button("Partial Approval", key=f"partial_{claim_id}"):
                        if process_claim_assessment(claim_id, 'partial', assessment_notes):
                            st.success(f"Claim #{claim_id} partially approved!")
                            st.rerun()
                
                with col3:
                    if st.button("Reject Claim", key=f"reject_{claim_id}"):
                        if process_claim_assessment(claim_id, 'rejected', assessment_notes):
                            st.success(f"Claim #{claim_id} rejected!")
                            st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

def process_claim_assessment(claim_id, status, notes):
    """Process an insurance claim assessment"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Get claim details
        c.execute('SELECT user_email, booking_id FROM insurance_claims WHERE id = ?', (claim_id,))
        user_email, booking_id = c.fetchone()
        
        # Update claim status
        c.execute('''
            UPDATE insurance_claims 
            SET claim_status = ?, admin_notes = ? 
            WHERE id = ?
        ''', (status, notes, claim_id))
        
        # Create notification
        create_notification(
            user_email,
            f"Your insurance claim #{claim_id} for booking #{booking_id} has been {status}. {notes if notes else ''}",
            f'claim_{status}'
        )
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error processing claim assessment: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def show_user_management(c):
    """User management tab for admin"""
    st.markdown("<h2>User Management</h2>", unsafe_allow_html=True)
    
    # Search users
    search_query = st.text_input("Search Users", placeholder="Enter name, email, or phone number")
    
    # Build query
    query = '''
        SELECT u.*, COUNT(DISTINCT cl.id) as listings_count, COUNT(DISTINCT b.id) as bookings_count,
               MAX(s.plan_type) as subscription
        FROM users u
        LEFT JOIN car_listings cl ON u.email = cl.owner_email
        LEFT JOIN bookings b ON u.email = b.user_email
        LEFT JOIN subscription_history s ON u.email = s.user_email
        WHERE 1=1
    '''
    params = []
    
    # Add search filter
    if search_query:
        query += " AND (u.full_name LIKE ? OR u.email LIKE ? OR u.phone LIKE ?)"
        search_param = f"%{search_query}%"
        params.extend([search_param, search_param, search_param])
    
    # Add grouping and ordering
    query += " GROUP BY u.id ORDER BY u.created_at DESC"
    
    # Execute query
    c.execute(query, params)
    users = c.fetchall()
    
    if not users:
        st.info("No users found matching the criteria.")
        return
    
    # Display users in a table
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    # Table header
    st.markdown("""
        <div style="display: grid; grid-template-columns: 2fr 1.5fr 1fr 1fr 1fr 1fr; font-weight: bold; padding: 0.8rem 0; border-bottom: 2px solid #ddd;">
            <div>User</div>
            <div>Contact</div>
            <div>Role</div>
            <div>Listings</div>
            <div>Bookings</div>
            <div>Subscription</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Table rows
    for user in users:
        user_id = user[0]
        full_name = user[1]
        email = user[2]
        phone = user[3]
        role = user[5]
        profile_pic = user[6]
        subscription_type = user[7]
        subscription_expiry = user[8]
        created_at = user[9]
        listings_count = user[10]
        bookings_count = user[11]
        
        # Default profile image if none exists
        profile_img = f"data:image/jpeg;base64,{profile_pic}" if profile_pic else "https://ui-avatars.com/api/?name={full_name}&background=random"
        
        # Format subscription
        subscription_text = subscription_type.replace('_', ' ').title() if subscription_type else 'Free'
        
        # Format expiry date
        expiry_text = ""
        if subscription_expiry:
            try:
                expiry_date = datetime.strptime(subscription_expiry, '%Y-%m-%d').date()
                today = datetime.now().date()
                days_left = (expiry_date - today).days
                
                if days_left > 0:
                    expiry_text = f"({days_left} days left)"
                else:
                    expiry_text = "(Expired)"
            except ValueError:
                pass
        
        st.markdown(f"""
            <div style="display: grid; grid-template-columns: 2fr 1.5fr 1fr 1fr 1fr 1fr; padding: 1rem 0; border-bottom: 1px solid #eee; align-items: center;"
                 onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'"
                 style="cursor: pointer;">
                <div style="display: flex; align-items: center;">
                    <img src="{profile_img}" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 1rem;" />
                    <div>
                        <div style="font-weight: 500;">{full_name}</div>
                        <div style="font-size: 0.8rem; color: #666;">Since {created_at[:10]}</div>
                    </div>
                </div>
                <div>
                    <div>{email}</div>
                    <div style="font-size: 0.8rem; color: #666;">{phone}</div>
                </div>
                <div>{role.title()}</div>
                <div>{listings_count}</div>
                <div>{bookings_count}</div>
                <div>
                    <div>{subscription_text}</div>
                    <div style="font-size: 0.8rem; color: #666;">{expiry_text}</div>
                </div>
            </div>
            <div style="display: none; padding: 1rem; background-color: #f9f9f9; border-radius: 0.5rem; margin: 0.5rem 0 1rem;">
                <h4>User Actions</h4>
        """, unsafe_allow_html=True)
        
        # User actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if role != 'admin':
                new_role = 'admin' if role == 'user' else 'user'
                if st.button(f"Change to {new_role.title()}", key=f"role_{user_id}"):
                    if update_user_role(email, new_role):
                        st.success(f"User role updated to {new_role}!")
                        st.rerun()
        
        with col2:
            subscription_options = [
                'free_renter', 'premium_renter', 'elite_renter', 
                'free_host', 'premium_host', 'elite_host'
            ]
            new_subscription = st.selectbox(
                "Change Subscription", 
                subscription_options,
                index=subscription_options.index(subscription_type) if subscription_type in subscription_options else 0,
                key=f"sub_{user_id}"
            )
            if st.button("Update Subscription", key=f"update_sub_{user_id}"):
                if update_user_subscription(email, new_subscription, 3):
                    st.success(f"Subscription updated to {new_subscription.replace('_', ' ').title()} for 3 months!")
                    st.rerun()
        
        with col3:
            if st.button("Send Notification", key=f"notify_{user_id}"):
                notification_text = st.text_input(
                    "Notification Message", 
                    placeholder="Enter message to send to user",
                    key=f"msg_{user_id}"
                )
                if notification_text:
                    create_notification(email, notification_text, 'admin')
                    st.success("Notification sent!")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def update_user_role(email, new_role):
    """Update a user's role"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Update role
        c.execute('''
            UPDATE users 
            SET role = ? 
            WHERE email = ?
        ''', (new_role, email))
        
        # Create notification
        create_notification(
            email,
            f"Your account role has been updated to {new_role}.",
            'role_update'
        )
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating user role: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def my_bookings_page():
    """Enhanced my bookings page with better UI"""
    st.markdown("<h1>My Bookings</h1>", unsafe_allow_html=True)
    
    # Back button
    if st.button('← Back to Browse', key='bookings_back'):
        st.session_state.current_page = 'browse_cars'
    
    # Connect to database
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Add tabs for Active/Past bookings
    active_tab, past_tab = st.tabs(["Active Bookings", "Past Bookings"])
    
    # Current date for filtering
    current_date = datetime.now().date().isoformat()
    
    with active_tab:
        # Fetch user's active bookings with car details
        c.execute('''
            SELECT b.*, cl.model, cl.year, cl.owner_email, li.image_data
            FROM bookings b
            JOIN car_listings cl ON b.car_id = cl.id
            LEFT JOIN listing_images li ON cl.id = li.listing_id AND li.is_primary = TRUE
            WHERE b.user_email = ? AND b.return_date >= ?
            ORDER BY b.pickup_date ASC
        ''', (st.session_state.user_email, current_date))
        
        active_bookings = c.fetchall()
        
        if not active_bookings:
            st.info("You don't have any active bookings.")
        else:
            display_bookings(active_bookings, c, is_active=True)
    
    with past_tab:
        # Fetch user's past bookings
        c.execute('''
            SELECT b.*, cl.model, cl.year, cl.owner_email, li.image_data
            FROM bookings b
            JOIN car_listings cl ON b.car_id = cl.id
            LEFT JOIN listing_images li ON cl.id = li.listing_id AND li.is_primary = TRUE
            WHERE b.user_email = ? AND b.return_date < ?
            ORDER BY b.return_date DESC
        ''', (st.session_state.user_email, current_date))
        
        past_bookings = c.fetchall()
        
        if not past_bookings:
            st.info("You don't have any past bookings.")
        else:
            display_bookings(past_bookings, c, is_active=False)
    
    conn.close()

def display_bookings(bookings, c, is_active=True):
    """Helper function to display bookings with better UI"""
    for booking in bookings:
        # Unpack booking details
        booking_id = booking[0]
        user_email = booking[1]
        car_id = booking[2]
        pickup_date = booking[3]
        return_date = booking[4]
        location = booking[5]
        total_price = booking[6]
        insurance = booking[7]
        driver = booking[8]
        delivery = booking[9]
        vip_service = booking[10]
        booking_status = booking[11]
        created_at = booking[12]
        insurance_price = booking[13]
        driver_price = booking[14]
        delivery_price = booking[15]
        vip_service_price = booking[16]
        model = booking[17]
        year = booking[18]
        owner_email = booking[19]
        image_data = booking[20]
        
        # Status color
        status_class = booking_status.lower()
        
        # Create a card for each booking
        with st.container():
            st.markdown(f"""
                <div class="card" style="margin-bottom: 2rem;">
                    <div style="display: flex; align-items: flex-start; gap: 1.5rem;">
                        <div style="flex: 1;">
            """, unsafe_allow_html=True)
            
            # Display car image if available
            if image_data:
                st.image(
                    f"data:image/jpeg;base64,{image_data}", 
                    use_container_width=True
                )
            
            st.markdown(f"""
                        </div>
                        <div style="flex: 2;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                                <h3 style="margin: 0;">{model} ({year})</h3>
                                <span class="status-badge {status_class}">{booking_status.upper()}</span>
                            </div>
                            
                            <div class="booking-details">
                                <div class="booking-detail-item">
                                    <div class="booking-detail-label">Booking ID</div>
                                    <div class="booking-detail-value">#{booking_id}</div>
                                </div>
                                <div class="booking-detail-item">
                                    <div class="booking-detail-label">Pickup Date</div>
                                    <div class="booking-detail-value">{pickup_date}</div>
                                </div>
                                <div class="booking-detail-item">
                                    <div class="booking-detail-label">Return Date</div>
                                    <div class="booking-detail-value">{return_date}</div>
                                </div>
                                <div class="booking-detail-item">
                                    <div class="booking-detail-label">Location</div>
                                    <div class="booking-detail-value">{location}</div>
                                </div>
                                <div class="booking-detail-item">
                                    <div class="booking-detail-label">Total Price</div>
                                    <div class="booking-detail-value">{format_currency(total_price)}</div>
                                </div>
                                <div class="booking-detail-item">
                                    <div class="booking-detail-label">Booked On</div>
                                    <div class="booking-detail-value">{created_at[:10]}</div>
                                </div>
                            </div>
                            
                            <h4 style="margin: 1.5rem 0 0.5rem;">Additional Services</h4>
                            <div style="display: flex; flex-wrap: wrap; gap: 1rem;">
            """, unsafe_allow_html=True)
            
            # Show included services
            if insurance:
                st.markdown(f"""
                    <div style="background-color: rgba(75, 45, 111, 0.1); padding: 0.5rem 1rem; border-radius: 30px;">
                        <span style="font-size: 0.9rem;">🛡️ Insurance (AED {insurance_price:.2f})</span>
                    </div>
                """, unsafe_allow_html=True)
            
            if driver:
                st.markdown(f"""
                    <div style="background-color: rgba(75, 45, 111, 0.1); padding: 0.5rem 1rem; border-radius: 30px;">
                        <span style="font-size: 0.9rem;">👨‍✈️ Driver (AED {driver_price:.2f})</span>
                    </div>
                """, unsafe_allow_html=True)
            
            if delivery:
                st.markdown(f"""
                    <div style="background-color: rgba(75, 45, 111, 0.1); padding: 0.5rem 1rem; border-radius: 30px;">
                        <span style="font-size: 0.9rem;">🚚 Delivery (AED {delivery_price:.2f})</span>
                    </div>
                """, unsafe_allow_html=True)
            
            if vip_service:
                st.markdown(f"""
                    <div style="background-color: rgba(75, 45, 111, 0.1); padding: 0.5rem 1rem; border-radius: 30px;">
                        <span style="font-size: 0.9rem;">⭐ VIP Service (AED {vip_service_price:.2f})</span>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("""
                            </div>
                        </div>
                    </div>
            """, unsafe_allow_html=True)
            
            # Action buttons based on booking status and whether it's active
            if is_active and booking_status.lower() == 'confirmed':
                
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    # Contact owner button
                    if st.button(f"Contact Owner", key=f"contact_{booking_id}"):
                        st.info(f"Contact the owner at: {owner_email}")
                
                with col2:
                    # Extend booking (if active)
                    if st.button(f"Extend Booking", key=f"extend_{booking_id}"):
                        st.session_state.current_page = 'extend_booking'
                        st.session_state.selected_booking = booking_id
                        st.rerun()
                
                with col3:
                    # File insurance claim (if insurance was included)
                    if insurance:
                        # Check if a claim already exists
                        c.execute('SELECT id FROM insurance_claims WHERE booking_id = ?', (booking_id,))
                        existing_claim = c.fetchone()
                        
                        if not existing_claim:
                            if st.button(f"File Insurance Claim", key=f"claim_{booking_id}"):
                                st.session_state.selected_booking_for_claim = booking_id
                                st.session_state.current_page = 'insurance_claims'
                                st.rerun()
                        else:
                            st.info("Claim already filed")
            
            # For past bookings, show review button if no review exists
            if not is_active and booking_status.lower() == 'confirmed':
                # Check if a review already exists
                c.execute('SELECT id FROM reviews WHERE booking_id = ?', (booking_id,))
                existing_review = c.fetchone()
                
                if not existing_review:
                    if st.button(f"Write Review", key=f"review_{booking_id}"):
                        # Show review form
                        with st.form(key=f"review_form_{booking_id}"):
                            st.markdown(f"<h4>Review for {model} ({year})</h4>", unsafe_allow_html=True)
                            
                            rating = st.slider("Rating", 1, 5, 5, key=f"rating_{booking_id}")
                            comment = st.text_area("Your Review", key=f"comment_{booking_id}")
                            
                            if st.form_submit_button("Submit Review"):
                                if submit_review(booking_id, user_email, car_id, rating, comment):
                                    st.success("Review submitted successfully!")
                                    st.rerun()
                                else:
                                    st.error("Error submitting review")
                else:
                    # Display the existing review
                    c.execute('SELECT rating, comment, created_at FROM reviews WHERE booking_id = ?', (booking_id,))
                    review = c.fetchone()
                    if review:
                        rating, comment, review_date = review
                        st.markdown(f"""
                            <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; margin-top: 1rem;">
                                <h4>Your Review</h4>
                                <div style="color: #FFD700; margin-bottom: 0.5rem;">{"★" * rating}{"☆" * (5 - rating)}</div>
                                <p>{comment}</p>
                                <p style="font-size: 0.8rem; color: #666; text-align: right;">Submitted on {review_date[:10]}</p>
                            </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

def submit_review(booking_id, user_email, car_id, rating, comment):
    """Submit a review for a booking"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Insert review
        c.execute('''
            INSERT INTO reviews 
            (booking_id, user_email, car_id, rating, comment)
            VALUES (?, ?, ?, ?, ?)
        ''', (booking_id, user_email, car_id, rating, comment))
        
        # Get car and owner details
        c.execute('''
            SELECT cl.model, cl.year, cl.owner_email 
            FROM car_listings cl
            WHERE cl.id = ?
        ''', (car_id,))
        car_model, car_year, owner_email = c.fetchone()
        
        # Create notification for the car owner
        create_notification(
            owner_email,
            f"New {rating}★ review for your {car_model} ({car_year})",
            'new_review'
        )
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error submitting review: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def list_your_car_page():
    """Enhanced car listing page with better UX"""
    st.markdown("<h1>List Your Car</h1>", unsafe_allow_html=True)
    
    if st.button('← Back to Browse', key='list_back'):
        st.session_state.current_page = 'browse_cars'
    
    # Get user's subscription type
    user_info = get_user_info(st.session_state.user_email)
    subscription_type = user_info[7] if user_info else 'free_host'
    
    # Display subscription benefits for hosts
    if subscription_type.endswith('_host'):
        benefits = get_subscription_benefits(subscription_type)
        
        st.markdown(f"""
            <div style="background-color: rgba(255, 211, 105, 0.2); padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem; border-left: 4px solid var(--accent-color);">
                <h3 style="margin-top: 0;">Your {subscription_type.replace('_', ' ').title()} Benefits</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div>
                        <p><strong>Commission:</strong> {benefits['commission']}</p>
                        <p><strong>Visibility:</strong> {benefits['visibility']}</p>
                    </div>
                    <div>
                        <p><strong>Damage Protection:</strong> {benefits['damage_protection']}</p>
                        <p><strong>Payout Speed:</strong> {benefits['payout_speed']}</p>
                    </div>
                    <div>
                        <p><strong>Support:</strong> {benefits['support']}</p>
                        <p><strong>Marketing:</strong> {benefits['marketing']}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Enhanced form with multi-step progress
    steps = ["Car Details", "Specifications", "Photos", "Terms"]
    
    if 'listing_step' not in st.session_state:
        st.session_state.listing_step = 0
    
    # Progress bar
    progress_val = (st.session_state.listing_step + 1) / len(steps)
    st.progress(progress_val)
    
    # Step indicator - Fixed the syntax error with proper string building
    step_html = ""
    for i, step in enumerate(steps):
        font_weight = "600" if i == st.session_state.listing_step else "400"
        color = "var(--primary-color)" if i == st.session_state.listing_step else "#666"
        step_html += f'<div style="flex: 1; text-align: center; font-weight: {font_weight}; color: {color};">{step}</div>'
    
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; margin-bottom: 2rem;">
            {step_html}
        </div>
    """, unsafe_allow_html=True)
    
    # Persistent form data
    if 'listing_form_data' not in st.session_state:
        st.session_state.listing_form_data = {
            'model': '',
            'year': datetime.now().year,
            'price': 1000,
            'category': 'Luxury',
            'location': 'Dubai Marina',
            'engine': '',
            'mileage': 0,
            'transmission': 'Automatic',
            'description': '',
            'features': {
                'leather_seats': False,
                'bluetooth': False,
                'parking_sensors': False,
                'cruise_control': False,
                'sunroof': False,
                'navigation': False
            },
            'uploaded_files': []
        }
    
    # Form steps
    if st.session_state.listing_step == 0:
        # Car Details
        st.markdown("<h2>Car Details</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.listing_form_data['model'] = st.text_input(
                "Car Model*", 
                value=st.session_state.listing_form_data['model'],
                placeholder="e.g., Ferrari 488 Spider"
            )
            
            st.session_state.listing_form_data['year'] = st.number_input(
                "Year*", 
                min_value=1990, 
                max_value=datetime.now().year,
                value=st.session_state.listing_form_data['year']
            )
            
            st.session_state.listing_form_data['price'] = st.number_input(
                "Daily Rate (AED)*", 
                min_value=0,
                value=st.session_state.listing_form_data['price']
            )
        
        with col2:
            st.session_state.listing_form_data['category'] = st.selectbox(
                "Category*", 
                get_car_categories()[1:],  # Skip "All" option
                index=get_car_categories()[1:].index(st.session_state.listing_form_data['category'])
            )
            
            st.session_state.listing_form_data['location'] = st.selectbox(
                "Location*", 
                get_location_options(),
                index=get_location_options().index(st.session_state.listing_form_data['location'])
            )
            
            st.session_state.listing_form_data['description'] = st.text_area(
                "Description*", 
                value=st.session_state.listing_form_data['description'],
                placeholder="Provide detailed information about your car"
            )
        
        col_next1, col_empty1, col_empty2 = st.columns([1, 1, 1])
        with col_next1:
            if st.button("Next: Specifications", use_container_width=True):
                if all([
                    st.session_state.listing_form_data['model'],
                    st.session_state.listing_form_data['description'],
                    st.session_state.listing_form_data['price'] > 0
                ]):
                    st.session_state.listing_step = 1
                    st.rerun()
                else:
                    st.error("Please fill in all required fields")
    
    elif st.session_state.listing_step == 1:
        # Specifications
        st.markdown("<h2>Car Specifications</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.listing_form_data['engine'] = st.text_input(
                "Engine Specifications*", 
                value=st.session_state.listing_form_data['engine'],
                placeholder="e.g., 3.9L V8 Twin-Turbo 660 hp"
            )
            
            st.session_state.listing_form_data['mileage'] = st.number_input(
                "Mileage (km)*", 
                min_value=0,
                value=st.session_state.listing_form_data['mileage']
            )
        
        with col2:
            st.session_state.listing_form_data['transmission'] = st.selectbox(
                "Transmission*", 
                ["Automatic", "Manual", "Semi-Automatic"],
                index=["Automatic", "Manual", "Semi-Automatic"].index(st.session_state.listing_form_data['transmission'])
            )
        
        # Additional features with improved UI
        st.markdown("<h3>Additional Features</h3>", unsafe_allow_html=True)
        
        feature_cols = st.columns(3)
        features = list(st.session_state.listing_form_data['features'].keys())
        
        for i, feature in enumerate(features):
            with feature_cols[i % 3]:
                feature_name = feature.replace('_', ' ').title()
                st.session_state.listing_form_data['features'][feature] = st.checkbox(
                    feature_name, 
                    value=st.session_state.listing_form_data['features'][feature],
                    key=f"feature_{feature}"
                )
        
        col_prev2, col_next2 = st.columns(2)
        with col_prev2:
            if st.button("← Previous: Car Details", use_container_width=True):
                st.session_state.listing_step = 0
                st.rerun()
        
        with col_next2:
            if st.button("Next: Upload Photos", use_container_width=True):
                if all([
                    st.session_state.listing_form_data['engine'],
                    st.session_state.listing_form_data['mileage'] >= 0
                ]):
                    st.session_state.listing_step = 2
                    st.rerun()
                else:
                    st.error("Please fill in all required fields")
    
    elif st.session_state.listing_step == 2:
        # Photos
        st.markdown("<h2>Upload Car Photos</h2>", unsafe_allow_html=True)
        
        st.markdown("""
            <p style="margin-bottom: 1rem;">
                Upload clear, high-quality photos of your car. The first photo will be the main image shown in search results.
            </p>
            <ul>
                <li>Include exterior views from different angles</li>
                <li>Add interior photos showing seats, dashboard, etc.</li>
                <li>Maximum 5 photos, each under 5MB</li>
                <li>Accepted formats: JPG, JPEG, PNG</li>
            </ul>
        """, unsafe_allow_html=True)
        
        # Image upload
        uploaded_files = st.file_uploader(
            "Upload Car Images* (Select multiple files)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )
        
        # Store uploads in session state
        if uploaded_files:
            st.session_state.listing_form_data['uploaded_files'] = uploaded_files
            
            # Display uploaded images in a grid
            st.markdown("<div class='image-gallery'>", unsafe_allow_html=True)
            for idx, uploaded_file in enumerate(uploaded_files):
                # Validate image
                is_valid, message = validate_image(uploaded_file)
                if is_valid:
                    image = Image.open(uploaded_file)
                    st.image(image, caption=f"Image {idx+1}", use_container_width=True)
                else:
                    st.error(message)
            st.markdown("</div>", unsafe_allow_html=True)
        
        col_prev3, col_next3 = st.columns(2)
        with col_prev3:
            if st.button("← Previous: Specifications", use_container_width=True):
                st.session_state.listing_step = 1
                st.rerun()
        
        with col_next3:
            if st.button("Next: Terms & Submit", use_container_width=True):
                if uploaded_files and len(uploaded_files) > 0:
                    st.session_state.listing_step = 3
                    st.rerun()
                else:
                    st.error("Please upload at least one photo")
    
    elif st.session_state.listing_step == 3:
        # Terms and Submit
        st.markdown("<h2>Terms & Conditions</h2>", unsafe_allow_html=True)
        
        # Display summary of listing
        st.markdown("<h3>Listing Summary</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div class="card">
                    <h4>Car Details</h4>
                    <p><strong>Model:</strong> {st.session_state.listing_form_data['model']}</p>
                    <p><strong>Year:</strong> {st.session_state.listing_form_data['year']}</p>
                    <p><strong>Category:</strong> {st.session_state.listing_form_data['category']}</p>
                    <p><strong>Daily Rate:</strong> {format_currency(st.session_state.listing_form_data['price'])}</p>
                    <p><strong>Location:</strong> {st.session_state.listing_form_data['location']}</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="card">
                    <h4>Specifications</h4>
                    <p><strong>Engine:</strong> {st.session_state.listing_form_data['engine']}</p>
                    <p><strong>Mileage:</strong> {st.session_state.listing_form_data['mileage']} km</p>
                    <p><strong>Transmission:</strong> {st.session_state.listing_form_data['transmission']}</p>
                    <p><strong>Features:</strong> {', '.join([k.replace('_', ' ').title() for k, v in st.session_state.listing_form_data['features'].items() if v])}</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="card">
                <h4>Description</h4>
                <p>{st.session_state.listing_form_data['description']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Terms and conditions
        st.markdown("<h3>Host Agreement</h3>", unsafe_allow_html=True)
        
        st.markdown("""
            <div style="height: 200px; overflow-y: scroll; border: 1px solid #ddd; padding: 1rem; margin-bottom: 1rem; background-color: #f9f9f9;">
                <h4>Luxury Car Rentals - Host Terms and Conditions</h4>
                <p>By listing your vehicle on our platform, you agree to the following terms:</p>
                <ol>
                    <li>You confirm that you are the legal owner of the vehicle or have the owner's permission to list it.</li>
                    <li>You warrant that all information provided about the vehicle is accurate and complete.</li>
                    <li>You are responsible for maintaining the vehicle in excellent condition and ensuring it meets all safety standards.</li>
                    <li>You agree to the commission structure based on your subscription plan.</li>
                    <li>You must respond to booking requests within 24 hours.</li>
                    <li>Cancellations within 48 hours of a confirmed booking may result in penalties.</li>
                    <li>You must provide the exact vehicle that was listed and approved.</li>
                    <li>You agree to our insurance and damage policy terms.</li>
                    <li>Your listing will go through an approval process before becoming visible on the platform.</li>
                    <li>Luxury Car Rentals reserves the right to remove listings that violate our policies.</li>
                </ol>
            </div>
        """, unsafe_allow_html=True)
        
        agree = st.checkbox("I agree to the Host Terms and Conditions", key="agree_terms")
        
        col_prev4, col_submit = st.columns(2)
        with col_prev4:
            if st.button("← Previous: Photos", use_container_width=True):
                st.session_state.listing_step = 2
                st.rerun()
        
        with col_submit:
            if st.button("Submit Listing", use_container_width=True, disabled=not agree):
                if agree:
                    with st.spinner("Submitting your listing..."):
                        success = submit_car_listing(st.session_state.listing_form_data)
                        
                        if success:
                            st.success("Your car has been listed successfully! Our team will review it shortly.")
                            st.balloons()
                            
                            # Reset form data and step
                            st.session_state.listing_form_data = {}
                            st.session_state.listing_step = 0
                            
                            # Redirect to my listings page after a brief delay
                            time.sleep(2)
                            st.session_state.current_page = 'my_listings'
                            st.rerun()
                        else:
                            st.error("An error occurred while listing your car. Please try again.")
                else:
                    st.error("Please agree to the Terms and Conditions")
                    
def submit_car_listing(form_data):
    """Submit a new car listing to the database"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Create specs dictionary
        specs = {
            "engine": form_data['engine'],
            "mileage": form_data['mileage'],
            "transmission": form_data['transmission'],
            "features": form_data['features']
        }
        
        # Insert listing
        c.execute('''
            INSERT INTO car_listings 
            (owner_email, model, year, price, location, description, 
            category, specs, listing_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            st.session_state.user_email,
            form_data['model'],
            form_data['year'],
            form_data['price'],
            form_data['location'],
            form_data['description'],
            form_data['category'],
            json.dumps(specs),
            'pending'
        ))
        
        listing_id = c.lastrowid
        
        # Save images
        for idx, file in enumerate(form_data['uploaded_files']):
            image_data = save_uploaded_image(file)
            if image_data:
                c.execute('''
                    INSERT INTO listing_images 
                    (listing_id, image_data, is_primary)
                    VALUES (?, ?, ?)
                ''', (listing_id, image_data, idx == 0))  # First image is primary
        
        conn.commit()
        
        # Create notification for user
        create_notification(
            st.session_state.user_email,
            f"Your listing for {form_data['model']} has been submitted for review. We'll notify you once it's approved.",
            'listing_submitted'
        )
        
        # Create notification for admin
        create_notification(
            "admin@luxuryrentals.com",
            f"New car listing submitted by {st.session_state.user_email} for {form_data['model']} ({form_data['year']})",
            'admin_new_listing'
        )
        
        return True
    except Exception as e:
        print(f"Error submitting listing: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def my_listings_page():
    """Enhanced my listings page with better UI"""
    st.markdown("<h1>My Listings</h1>", unsafe_allow_html=True)
    
    # Back button and Add new car button
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button('← Back to Browse', key='my_listings_back'):
            st.session_state.current_page = 'browse_cars'
    
    with col2:
        if st.button("+ Add New Car", key="add_new_car"):
            st.session_state.current_page = 'list_your_car'
            st.rerun()
    
    # Connect to database
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Get user's subscription type for commission info
    user_info = get_user_info(st.session_state.user_email)
    subscription_type = user_info[7] if user_info else 'free_host'
    
    # Get commission rate based on subscription
    commission_rate = 0.15  # default 15%
    if subscription_type == 'premium_host':
        commission_rate = 0.10
    elif subscription_type == 'elite_host':
        commission_rate = 0.05
    
    # Add tabs for Active/Pending/Rejected listings
    active_tab, pending_tab, rejected_tab = st.tabs(["Active Listings", "Pending Approval", "Rejected"])
    
    with active_tab:
        # Fetch user's active listings
        c.execute('''
            SELECT cl.*, GROUP_CONCAT(li.image_data) as images,
                   (SELECT COUNT(*) FROM bookings WHERE car_id = cl.id AND booking_status = 'confirmed') as booking_count,
                   (SELECT AVG(rating) FROM reviews WHERE car_id = cl.id) as avg_rating,
                   (SELECT COUNT(*) FROM reviews WHERE car_id = cl.id) as review_count
            FROM car_listings cl
            LEFT JOIN listing_images li ON cl.id = li.listing_id
            WHERE cl.owner_email = ? AND cl.listing_status = 'approved'
            GROUP BY cl.id
            ORDER BY cl.created_at DESC
        ''', (st.session_state.user_email,))
        
        active_listings = c.fetchall()
        
        if not active_listings:
            st.info("You don't have any active listings yet.")
        else:
            for listing in active_listings:
                display_listing(listing, c, commission_rate, 'active')
    
    with pending_tab:
        # Fetch user's pending listings
        c.execute('''
            SELECT cl.*, GROUP_CONCAT(li.image_data) as images
            FROM car_listings cl
            LEFT JOIN listing_images li ON cl.id = li.listing_id
            WHERE cl.owner_email = ? AND cl.listing_status = 'pending'
            GROUP BY cl.id
            ORDER BY cl.created_at DESC
        ''', (st.session_state.user_email,))
        
        pending_listings = c.fetchall()
        
        if not pending_listings:
            st.info("You don't have any listings pending approval.")
        else:
            for listing in pending_listings:
                display_listing(listing, c, commission_rate, 'pending')
    
    with rejected_tab:
        # Fetch user's rejected listings
        c.execute('''
            SELECT cl.*, GROUP_CONCAT(li.image_data) as images,
                   (SELECT comment FROM admin_reviews WHERE listing_id = cl.id ORDER BY created_at DESC LIMIT 1) as rejection_reason
            FROM car_listings cl
            LEFT JOIN listing_images li ON cl.id = li.listing_id
            WHERE cl.owner_email = ? AND cl.listing_status = 'rejected'
            GROUP BY cl.id
            ORDER BY cl.created_at DESC
        ''', (st.session_state.user_email,))
        
        rejected_listings = c.fetchall()
        
        if not rejected_listings:
            st.info("You don't have any rejected listings.")
        else:
            for listing in rejected_listings:
                display_listing(listing, c, commission_rate, 'rejected')
    
    conn.close()

def display_listing(listing, c, commission_rate, status_type):
    """Helper function to display a car listing with better UI"""
    listing_id = listing[0]
    model = listing[2]
    year = listing[3]
    price = listing[4]
    location = listing[5]
    description = listing[6]
    category = listing[7]
    specs_json = listing[8]
    created_at = listing[10]
    
    # Parse images and specs
    images = listing[11].split(',') if listing[11] else []
    specs = json.loads(specs_json) if specs_json else {}
    
    # Get extra info for active listings
    booking_count = listing[12] if status_type == 'active' and len(listing) > 12 else 0
    avg_rating = listing[13] if status_type == 'active' and len(listing) > 13 else 0
    review_count = listing[14] if status_type == 'active' and len(listing) > 14 else 0
    
    # Get rejection reason for rejected listings
    rejection_reason = listing[12] if status_type == 'rejected' and len(listing) > 12 else None
    
    # Create card
    st.markdown(f"""
        <div class="card" style="margin-bottom: 2rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                <h3 style="margin: 0;">{model} ({year})</h3>
                <span class="status-badge {status_type}">{status_type.upper()}</span>
            </div>
    """, unsafe_allow_html=True)
    
    # Display the primary image
    if images and images[0]:
        st.image(
            f"data:image/jpeg;base64,{images[0]}",
            caption=f"{model} ({year})",
            use_container_width=True
        )
    
    # Display listing details
    st.markdown(f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0;">
            <div>
                <p><strong>Price:</strong> {format_currency(price)}/day</p>
                <p><strong>Location:</strong> {location}</p>
                <p><strong>Category:</strong> {category}</p>
            </div>
            <div>
                <p><strong>Engine:</strong> {specs.get('engine', 'N/A')}</p>
                <p><strong>Mileage:</strong> {specs.get('mileage', 'N/A')} km</p>
                <p><strong>Transmission:</strong> {specs.get('transmission', 'N/A')}</p>
            </div>
        </div>
        <p><strong>Description:</strong> {description}</p>
    """, unsafe_allow_html=True)
    
    # Show rating and booking stats for active listings
    if status_type == 'active' and avg_rating:
        rating_stars = "★" * int(avg_rating) + "☆" * (5 - int(avg_rating))
        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; background-color: #f9f9f9; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                <div>
                    <div style="font-size: 0.9rem; color: #666;">Rating</div>
                    <div style="font-size: 1.2rem; color: #FFD700;">{rating_stars} ({review_count} reviews)</div>
                </div>
                <div>
                    <div style="font-size: 0.9rem; color: #666;">Total Bookings</div>
                    <div style="font-size: 1.2rem; font-weight: 600;">{booking_count}</div>
                </div>
                <div>
                    <div style="font-size: 0.9rem; color: #666;">Commission Rate</div>
                    <div style="font-size: 1.2rem; font-weight: 600;">{int(commission_rate * 100)}%</div>
                </div>
                <div>
                    <div style="font-size: 0.9rem; color: #666;">Estimated Earnings</div>
                    <div style="font-size: 1.2rem; font-weight: 600;">{format_currency(price * (1 - commission_rate))}/day</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Show rejection reason for rejected listings
    if status_type == 'rejected' and rejection_reason:
        st.markdown(f"""
            <div style="background-color: #FFEBEE; padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #C62828;">
                <h4 style="margin-top: 0; color: #C62828;">Rejection Reason</h4>
                <p>{rejection_reason if rejection_reason else 'No specific reason provided.'}</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Show actions based on listing status
    col1, col2 = st.columns(2)
    
    if status_type == 'active':
        with col1:
            if st.button(f"View Bookings", key=f"bookings_{listing_id}"):
                st.session_state.current_page = 'owner_bookings'
                st.session_state.filter_car_id = listing_id
                st.rerun()
        
        with col2:
            if st.button(f"Edit Listing", key=f"edit_{listing_id}"):
                st.session_state.selected_listing_for_edit = listing_id
                st.session_state.current_page = 'edit_listing'
                st.rerun()
    
    elif status_type == 'rejected':
        with col1:
            if st.button(f"Resubmit with Changes", key=f"resubmit_{listing_id}"):
                st.session_state.selected_listing_for_edit = listing_id
                st.session_state.current_page = 'edit_listing'
                st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

def subscription_plans_page():
    """Enhanced subscription plans page with better UI"""
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
    
    # Enhanced tabs with icons
    st.markdown("""
        <div style="display: flex; gap: 1rem; margin-bottom: 2rem;">
            <div style="flex: 1; text-align: center; cursor: pointer;" onclick="document.getElementById('renter_tab_btn').click();">
                <div style="background-color: var(--primary-color); color: white; padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem;">
                    <span style="font-size: 2rem;">🚗</span>
                </div>
                <div style="font-weight: 500;">Renter Plans</div>
                <div style="font-size: 0.8rem; color: #666;">For those who rent cars</div>
            </div>
            <div style="flex: 1; text-align: center; cursor: pointer;" onclick="document.getElementById('host_tab_btn').click();">
                <div style="background-color: var(--secondary-color); color: white; padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem;">
                    <span style="font-size: 2rem;">🏠</span>
                </div>
                <div style="font-weight: 500;">Host Plans</div>
                <div style="font-size: 0.8rem; color: #666;">For those who list cars</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Hidden buttons for the tabs to work with JavaScript
    col1, col2 = st.columns(2)
    with col1:
        renter_tab = st.button("Renter Plans", key="renter_tab_btn", type="primary")
    with col2:
        host_tab = st.button("Host Plans", key="host_tab_btn")
    
    # Default to the user's primary type
    if 'active_plan_tab' not in st.session_state:
        st.session_state.active_plan_tab = user_type
    
    # Update active tab based on button clicks
    if renter_tab:
        st.session_state.active_plan_tab = 'renter'
    elif host_tab:
        st.session_state.active_plan_tab = 'host'
    
    # Show plans based on active tab
    if st.session_state.active_plan_tab == 'renter':
        show_renter_plans(current_plan)
    else:
        show_host_plans(current_plan)

def show_renter_plans(current_plan):
    """Display renter subscription plans"""
    st.markdown("<h2>Plans for Renters</h2>", unsafe_allow_html=True)
    
    # Create cards for each plan
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="subscription-card">
                <h3>Free Plan</h3>
                <div class="subscription-price">
                    <span class="currency">AED</span>
                    0
                    <span class="period">/month</span>
                </div>
                <div class="subscription-features">
                    <ul>
                        <li>Standard service fees apply</li>
                        <li>No booking priority</li>
                        <li>No special discounts</li>
                        <li>Cancellations may have penalties</li>
                        <li>No roadside assistance</li>
                        <li>Standard customer support</li>
                        <li>Access to general vehicle listings</li>
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
    
    with col2:
        st.markdown("""
            <div class="subscription-card premium">
                <h3>Premium Plan</h3>
                <div class="subscription-price">
                    <span class="currency">AED</span>
                    99
                    <span class="period">/month</span>
                </div>
                <div class="subscription-features">
                    <ul>
                        <li>Reduced service fees</li>
                        <li>Priority booking access</li>
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
    
    with col3:
        st.markdown("""
            <div class="subscription-card elite">
                <span class="popular-tag">Popular</span>
                <h3>Elite VIP Plan</h3>
                <div class="subscription-price">
                    <span class="currency">AED</span>
                    249
                    <span class="period">/month</span>
                </div>
                <div class="subscription-features">
                    <ul>
                        <li>Lowest service fees on rentals</li>
                        <li>First priority booking access</li>
                        <li>Up to 20% discount on rentals</li>
                        <li>Unlimited free cancellations</li>
                        <li>Premium roadside assistance</li>
                        <li>24/7 priority customer support</li>
                        <li>Access to exotic and chauffeur-driven cars</li>
                        <li>Full damage waiver protection</li>
                        <li>Free vehicle upgrades (if available)</li>
                        <li>VIP concierge service</li>
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
    
    # Feature comparison
    st.markdown("<h3>Feature Comparison</h3>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="feature-comparison">
            <div class="feature-row" style="font-weight: 600; border-bottom: 2px solid #ddd;">
                <div class="feature-name">Feature</div>
                <div class="feature-value">Free</div>
                <div class="feature-value">Premium</div>
                <div class="feature-value">Elite VIP</div>
            </div>
            <div class="feature-row">
                <div class="feature-name">Service Fees</div>
                <div class="feature-value">Standard</div>
                <div class="feature-value">Reduced</div>
                <div class="feature-value">Lowest</div>
            </div>
            <div class="feature-row">
                <div class="feature-name">Booking Priority</div>
                <div class="feature-value">None</div>
                <div class="feature-value">Medium</div>
                <div class="feature-value">Highest</div>
            </div>
            <div class="feature-row">
                <div class="feature-name">Rental Discounts</div>
                <div class="feature-value">None</div>
                <div class="feature-value">Up to 10%</div>
                <div class="feature-value">Up to 20%</div>
            </div>
            <div class="feature-row">
                <div class="feature-name">Cancellation Policy</div>
                <div class="feature-value">Penalties Apply</div>
                <div class="feature-value">Limited Free</div>
                <div class="feature-value">Unlimited Free</div>
            </div>
            <div class="feature-row">
                <div class="feature-name">Roadside Assistance</div>
                <div class="feature-value">Not Included</div>
                <div class="feature-value">Included</div>
                <div class="feature-value">Premium</div>
            </div>
            <div class="feature-row">
                <div class="feature-name">Vehicle Access</div>
                <div class="feature-value">General Only</div>
                <div class="feature-value">Exclusive Luxury</div>
                <div class="feature-value">All Including Exotic</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def show_host_plans(current_plan):
    """Display host subscription plans"""
    st.markdown("<h2>Plans for Hosts</h2>", unsafe_allow_html=True)
    
    # Create cards for each plan
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="subscription-card">
                <h3>Free Host Plan</h3>
                <div class="subscription-price">
                    <span class="currency">AED</span>
                    0
                    <span class="period">/month</span>
                </div>
                <div class="subscription-features">
                    <ul>
                        <li>Standard listing visibility</li>
                        <li>15% platform commission</li>
                        <li>No dynamic pricing tools</li>
                        <li>Basic damage protection</li>
                        <li>Basic fraud prevention</li>
                        <li>Standard payout (3-5 days)</li>
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
    
    with col2:
        st.markdown("""
            <div class="subscription-card premium">
                <h3>Premium Host Plan</h3>
                <div class="subscription-price">
                    <span class="currency">AED</span>
                    199
                    <span class="period">/month</span>
                </div>
                <div class="subscription-features">
                    <ul>
                        <li>Boosted visibility for listings</li>
                        <li>Lower platform commission (10%)</li>
                        <li>Dynamic pricing tools</li>
                        <li>Extra damage protection</li>
                        <li>Enhanced renter verification</li>
                        <li>Faster payouts (1-2 days)</li>
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
                    st.success(f"Successfully subscribed to Premium Host plan for {duration} {'month' if duration == 1 else 'months'}!")
                    st.rerun()
    
    with col3:
        st.markdown("""
            <div class="subscription-card elite">
                <span class="popular-tag">Popular</span>
                <h3>Elite Host Plan</h3>
                <div class="subscription-price">
                    <span class="currency">AED</span>
                    399
                    <span class="period">/month</span>
                </div>
                <div class="subscription-features">
                    <ul>
                        <li>Top placement for listings</li>
                        <li>Lowest platform commission (5%)</li>
                        <li>Advanced AI-driven pricing</li>
                        <li>Full damage protection</li>
                        <li>AI-based risk assessment</li>
                        <li>Instant same-day payouts</li>
                        <li>24/7 dedicated support manager</li>
                        <li>Featured placement in promotions</li>
                        <li>Dedicated account manager</li>
                        <li>Performance analytics dashboard</li>
                    </ul>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if current_plan != 'elite_host':
            duration = st.selectbox("Subscription Duration", [1, 3, 6, 12], key="elite_host_duration")
            if st.button(f"Subscribe for {duration} {'month' if duration == 1 else 'months'}", key="subscribe_elite_host"):
                if update_user_subscription(st.session_state.user_email, 'elite_host', duration):
                    st.success(f"Successfully subscribed to Elite Host plan for {duration} {'month' if duration == 1 else 'months'}!")
                    st.rerun()
    
    # Commission comparison
    st.markdown("<h3>Commission Comparison</h3>", unsafe_allow_html=True)
    
    # Create a sample chart to show commission differences
    sample_booking = 2000  # AED 2000 booking
    
    free_commission = sample_booking * 0.15
    premium_commission = sample_booking * 0.10
    elite_commission = sample_booking * 0.05
    
    free_earnings = sample_booking - free_commission
    premium_earnings = sample_booking - premium_commission
    elite_earnings = sample_booking - elite_commission
    
    # Create chart data
    chart_data = {
        'plan': ['Free Host', 'Premium Host', 'Elite Host'],
        'commission': [free_commission, premium_commission, elite_commission],
        'earnings': [free_earnings, premium_earnings, elite_earnings]
    }
    
    # Create a DataFrame
    df_chart = pd.DataFrame(chart_data)
    
    # Create the chart using Plotly
    fig = go.Figure()
    
    # Add bars for earnings
    fig.add_trace(go.Bar(
        x=df_chart['plan'],
        y=df_chart['earnings'],
        name='Your Earnings',
        marker_color='#4B2D6F'
    ))
    
    # Add bars for commission
    fig.add_trace(go.Bar(
        x=df_chart['plan'],
        y=df_chart['commission'],
        name='Platform Commission',
        marker_color='#8E4162'
    ))
    
    # Customize the layout
    fig.update_layout(
        title='Earnings Comparison for a AED 2,000 Booking',
        xaxis_title='Subscription Plan',
        yaxis_title='Amount (AED)',
        barmode='stack',
        height=500
    )
    
    # Add labels on the bars
    for i, plan in enumerate(df_chart['plan']):
        fig.add_annotation(
            x=i,
            y=df_chart['earnings'][i] / 2,
            text=f"{format_currency(df_chart['earnings'][i])}",
            showarrow=False,
            font=dict(color='white')
        )
        fig.add_annotation(
            x=i,
            y=df_chart['earnings'][i] + df_chart['commission'][i] / 2,
            text=f"{format_currency(df_chart['commission'][i])}",
            showarrow=False,
            font=dict(color='white')
        )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Feature comparison
    st.markdown("<h3>Feature Comparison</h3>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="feature-comparison">
            <div class="feature-row" style="font-weight: 600; border-bottom: 2px solid #ddd;">
                <div class="feature-name">Feature</div>
                <div class="feature-value">Free Host</div>
                <div class="feature-value">Premium Host</div>
                <div class="feature-value">Elite Host</div>
            </div>
            <div class="feature-row">
                <div class="feature-name">Listing Visibility</div>
                <div class="feature-value">Standard</div>
                <div class="feature-value">Boosted</div>
                <div class="feature-value">Top Placement</div>
            </div>
            <div class="feature-row">
                <div class="feature-name">Platform Commission</div>
                <div class="feature-value">15%</div>
                <div class="feature-value">10%</div>
                <div class="feature-value">5%</div>
            </div>
            <div class="feature-row">
                <div class="feature-name">Pricing Tools</div>
                <div class="feature-value">Basic</div>
                <div class="feature-value">Dynamic</div>
                <div class="feature-value">AI-driven</div>
            </div>
            <div class="feature-row">
                <div class="feature-name">Damage Protection</div>
                <div class="feature-value">Basic</div>
                <div class="feature-value">Extra</div>
                <div class="feature-value">Full</div>
            </div>
            <div class="feature-row">
                <div class="feature-name">Payout Speed</div>
                <div class="feature-value">3-5 days</div>
                <div class="feature-value">1-2 days</div>
                <div class="feature-value">Same-day</div>
            </div>
            <div class="feature-row">
                <div class="feature-name">Customer Support</div>
                <div class="feature-value">Standard</div>
                <div class="feature-value">Priority</div>
                <div class="feature-value">Dedicated Manager</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def notifications_page():
    """Enhanced notifications page with better UI"""
    st.markdown("<h1>Notifications</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button('← Back to Browse', key='notifications_back'):
            st.session_state.current_page = 'browse_cars'
    
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Fetch unread notifications
    c.execute('''
        SELECT * FROM notifications 
        WHERE user_email = ? AND read = FALSE
        ORDER BY created_at DESC
    ''', (st.session_state.user_email,))
    
    unread_notifications = c.fetchall()
    
    # Fetch read notifications
    c.execute('''
        SELECT * FROM notifications 
        WHERE user_email = ? AND read = TRUE
        ORDER BY created_at DESC
        LIMIT 20
    ''', (st.session_state.user_email,))
    
    read_notifications = c.fetchall()
    
    # Clear notifications functionality
    with col2:
        if unread_notifications:
            if st.button('Mark All as Read'):
                mark_notifications_as_read(st.session_state.user_email)
                st.success("All notifications marked as read!")
                st.rerun()
    
    # Display tabs for unread/read notifications
    if unread_notifications or read_notifications:
        unread_tab, read_tab = st.tabs([f"Unread ({len(unread_notifications)})", f"Read ({len(read_notifications)})"])
        
        with unread_tab:
            if unread_notifications:
                for notif in unread_notifications:
                    display_notification(notif, unread=True)
            else:
                st.info("No unread notifications")
        
        with read_tab:
            if read_notifications:
                for notif in read_notifications:
                    display_notification(notif, unread=False)
            else:
                st.info("No read notifications")
    else:
        st.info("No notifications")
    
    # Mark all unread as read when viewing
    if unread_notifications:
        mark_notifications_as_read(st.session_state.user_email)
    
    conn.close()

def display_notification(notification, unread=False):
    """Helper function to display a notification with better UI"""
    notification_id = notification[0]
    message = notification[2]
    notification_type = notification[3]
    created_at = notification[5]
    
    # Format datetime
    try:
        dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
        display_time = dt.strftime("%b %d, %Y at %I:%M %p")
    except:
        display_time = created_at
    
    # Get appropriate icon based on notification type
    icons = {
        'welcome': '👋',
        'booking_confirmed': '✅',
        'booking_rejected': '❌',
        'listing_submitted': '📝',
        'listing_approved': '👍',
        'listing_rejected': '👎',
        'claim_submitted': '🛡️',
        'claim_approved': '💰',
        'claim_rejected': '🚫',
        'claim_partial': '⚖️',
        'subscription_activated': '🔄',
        'new_booking': '🚗',
        'role_update': '👤',
        'new_review': '⭐',
        'admin': '👑'
    }
    
    icon = icons.get(notification_type, '📣')
    
    # Notification color
    if notification_type in ['booking_confirmed', 'listing_approved', 'claim_approved']:
        color = 'var(--success-color)'
    elif notification_type in ['booking_rejected', 'listing_rejected', 'claim_rejected']:
        color = 'var(--danger-color)'
    elif notification_type in ['welcome', 'subscription_activated']:
        color = 'var(--primary-color)'
    else:
        color = 'var(--secondary-color)'
    
    st.markdown(f"""
        <div class="notification-item {'unread' if unread else ''}" style="border-left-color: {color};">
            <div style="display: flex;">
                <div style="width: 40px; height: 40px; background-color: rgba(75, 45, 111, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 1rem;">
                    <span style="font-size: 1.5rem;">{icon}</span>
                </div>
                <div style="flex: 1;">
                    <div class="notification-message">{message}</div>
                    <div class="notification-time">{display_time}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def about_us_page():
    """Enhanced about us page with better UI"""
    st.markdown("<h1>About Luxury Car Rentals</h1>", unsafe_allow_html=True)
    
    if st.button('← Back to Welcome', key='about_back'):
        st.session_state.current_page = 'welcome'
    
    # Main content
    st.markdown("""
        <div class="card" style="padding: 2rem; margin-bottom: 2rem;">
            <h2 style="text-align: center; margin-bottom: 1.5rem;">Our Mission</h2>
            <p style="font-size: 1.1rem; line-height: 1.7; text-align: center; max-width: 800px; margin: 0 auto;">
                At Luxury Car Rentals, we're committed to transforming the car rental experience through 
                <span style="color: var(--primary-color); font-weight: 600;">sustainability</span>, 
                <span style="color: var(--primary-color); font-weight: 600;">innovation</span>, and 
                <span style="color: var(--primary-color); font-weight: 600;">exceptional service</span>. 
                We believe in providing premium vehicles while contributing to a more sustainable future for transportation.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Sustainability section
    st.markdown("<h2>Our Commitment to Sustainable Development Goals</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
            <div style="margin-bottom: 2rem;">
                <p>Our business model aligns with multiple UN Sustainable Development Goals (SDGs), with particular focus on:</p>
                
                <h3>SDG 11: Sustainable Cities and Communities</h3>
                <p>We contribute to more sustainable cities and communities by:</p>
                <ul>
                    <li>Promoting shared mobility solutions to reduce the need for car ownership</li>
                    <li>Offering electric and hybrid vehicles to reduce urban emissions</li>
                    <li>Supporting smart mobility integration with public transportation</li>
                    <li>Implementing carbon offset programs for all rentals</li>
                </ul>
                
                <h3>SDG 12: Responsible Consumption and Production</h3>
                <p>We practice responsible business through:</p>
                <ul>
                    <li>Regular fleet maintenance to extend vehicle lifespan</li>
                    <li>Recycling and proper disposal of automotive fluids and parts</li>
                    <li>Paperless booking and digital receipts</li>
                    <li>Partnerships with sustainable suppliers and local businesses</li>
                </ul>
                
                <h3>SDG 13: Climate Action</h3>
                <p>We're actively fighting climate change by:</p>
                <ul>
                    <li>Transitioning our fleet to electric and hybrid vehicles</li>
                    <li>Carbon offsetting program for all rentals</li>
                    <li>Investment in renewable energy for our facilities</li>
                    <li>Educating customers on eco-friendly driving practices</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # SDG Logos
        st.image("https://www.localgovernmentassociation.sa.gov.au/__data/assets/image/0016/1205080/SDG-11.jpg", 
                caption="SDG 11: Sustainable Cities and Communities")
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRDayMFgGtUTvd6D_cWCYbCVQ46Hp0_6Bsh7xsODPvFX4nM3l63n8G11Zl6b3pWfE_Ia0A&usqp=CAU", 
                caption="SDG 12: Responsible Consumption and Production")
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSFdSP0D6_UN0LKhd-LdVffEuDdUomJA-OIB4v-sxDYVkSPNCcCTVuozTHfR1r4o4l1A5s&usqp=CAU", 
                caption="SDG 13: Climate Action")
    
    # Sustainability initiatives
    st.markdown("""
        <div class="card" style="margin-top: 2rem;">
            <h3>Our Sustainability Initiatives</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-top: 1.5rem;">
                <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
                    <div style="width: 80px; height: 80px; background-color: rgba(75, 45, 111, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-bottom: 1rem;">
                        <span style="font-size: 2rem;">⚡</span>
                    </div>
                    <h4>EV First</h4>
                    <p>30% of our fleet is electric, growing to 75% by 2027</p>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
                    <div style="width: 80px; height: 80px; background-color: rgba(75, 45, 111, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-bottom: 1rem;">
                        <span style="font-size: 2rem;">🌱</span>
                    </div>
                    <h4>Carbon Neutral</h4>
                    <p>All rentals include carbon offset in partnership with Climate Action UAE</p>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
                    <div style="width: 80px; height: 80px; background-color: rgba(75, 45, 111, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-bottom: 1rem;">
                        <span style="font-size: 2rem;">🏢</span>
                    </div>
                    <h4>Green Facilities</h4>
                    <p>Our locations use solar power and rainwater harvesting</p>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
                    <div style="width: 80px; height: 80px; background-color: rgba(75, 45, 111, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-bottom: 1rem;">
                        <span style="font-size: 2rem;">🤝</span>
                    </div>
                    <h4>Community Support</h4>
                    <p>2% of profits go to sustainable transportation initiatives</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Team section
    st.markdown("""
        <h2 style="margin-top: 3rem;">Our Team</h2>
        <p>Luxury Car Rentals was founded in 2020 by a team of automotive enthusiasts and sustainability experts 
        who believed luxury transportation could be both premium and environmentally responsible.</p>
        <p>Our leadership team brings together experience from the automotive industry, hospitality, technology, 
        and environmental science to create a truly innovative approach to car rentals.</p>
    """, unsafe_allow_html=True)
    
    # Contact information
    st.markdown("""
        <div class="card" style="margin-top: 2rem;">
            <h3>Contact Us</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-top: 1.5rem;">
                <div>
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <div style="width: 40px; height: 40px; background-color: rgba(75, 45, 111, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 1rem;">
                            <span style="font-size: 1.5rem;">📍</span>
                        </div>
                        <div>
                            <div style="font-weight: 600; margin-bottom: 0.2rem;">Address</div>
                            <div>Dubai Marina, Tower 3, Floor 15</div>
                        </div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <div style="width: 40px; height: 40px; background-color: rgba(75, 45, 111, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 1rem;">
                            <span style="font-size: 1.5rem;">📧</span>
                        </div>
                        <div>
                            <div style="font-weight: 600; margin-bottom: 0.2rem;">Email</div>
                            <div>info@luxurycarrentals.ae</div>
                        </div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <div style="width: 40px; height: 40px; background-color: rgba(75, 45, 111, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 1rem;">
                            <span style="font-size: 1.5rem;">📞</span>
                        </div>
                        <div>
                            <div style="font-weight: 600; margin-bottom: 0.2rem;">Phone</div>
                            <div>+971 4 123 4567</div>
                        </div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <div style="width: 40px; height: 40px; background-color: rgba(75, 45, 111, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 1rem;">
                            <span style="font-size: 1.5rem;">🌐</span>
                        </div>
                        <div>
                            <div style="font-weight: 600; margin-bottom: 0.2rem;">Social Media</div>
                            <div>@LuxuryCarRentalsUAE</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def update_bookings_table():
    """Update database tables if needed"""
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

def show_sidebar():
    """Display sidebar with navigation for logged-in users"""
    with st.sidebar:
        # Get user info
        user_info = get_user_info(st.session_state.user_email)
        
        # Display profile section
        if user_info:
            st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
            
            if user_info[6]:  # profile picture
                st.markdown(f"""
                    <img src="data:image/jpeg;base64,{user_info[6]}" class="profile-picture" alt="{user_info[1]}">
                """, unsafe_allow_html=True)
            else:
                # Create a default profile image with initials
                initials = ''.join([name[0].upper() for name in user_info[1].split() if name])
                st.markdown(f"""
                    <div style="width: 100px; height: 100px; background-color: var(--primary-color); color: white; display: flex; justify-content: center; align-items: center; border-radius: 50%; font-size: 2rem; margin-bottom: 1rem;">
                        {initials}
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="profile-name">{user_info[1]}</div>
                <div class="profile-role">{user_info[7].replace('_', ' ').title()}</div>
            """, unsafe_allow_html=True)
            
            # Add edit profile button
            if st.button("Edit Profile", key="edit_profile_btn"):
                st.session_state.current_page = 'edit_profile'
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Navigation section
        st.markdown("<h3>Navigation</h3>", unsafe_allow_html=True)
        
        # Get current page to highlight active nav item
        current_page = st.session_state.current_page
        
        # Navigation items with icons
        nav_items = [
            ("🚗 Browse Cars", 'browse_cars'),
            ("📝 My Listings", 'my_listings'),
            ("➕ List Your Car", 'list_your_car'),
            ("🔖 My Bookings", 'my_bookings'),
            ("📋 Bookings for My Cars", 'owner_bookings'),
            ("⭐ My Reviews", 'my_reviews'),
            ("💰 Subscription Plans", 'subscription_plans'),
            ("🛡️ Insurance Claims", 'insurance_claims'),
            ("ℹ️ About Us", 'about_us')
        ]
        
        # Add admin panel for admin users
        role = get_user_role(st.session_state.user_email)
        if role == 'admin':
            nav_items.insert(0, ("🔧 Admin Dashboard", 'admin_dashboard'))
        
        # Display navigation items
        for label, page in nav_items:
            active_class = 'active' if current_page == page else ''
            
            # Using HTML for better styling
            st.markdown(f"""
                <div class="nav-item {active_class}" onclick="document.getElementById('nav_{page}').click();">
                    <span class="nav-item-icon">{label.split()[0]}</span>
                    <span>{' '.join(label.split()[1:])}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Hidden button to handle the click
            if st.button(label, key=f"nav_{page}"):
                st.session_state.current_page = page
                st.rerun()
        
        # Notifications section
        unread_count = get_unread_notifications_count(st.session_state.user_email)
        notification_label = f"🔔 Notifications ({unread_count})" if unread_count > 0 else "🔔 Notifications"
        st.markdown("""
            <style>
            .stButton>button#nav_notifications {
                display: none;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="nav-item {'active' if current_page == 'notifications' else ''}" onclick="document.getElementById('nav_notifications').click();">
                <span class="nav-item-icon">🔔</span>
                <span>Notifications</span>
                {f'<span style="background-color: var(--accent-color); color: var(--primary-color); border-radius: 50%; min-width: 24px; height: 24px; display: inline-flex; justify-content: center; align-items: center; margin-left: auto; font-size: 0.8rem; font-weight: 600;">{unread_count}</span>' if unread_count > 0 else ''}
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(notification_label, key="nav_notifications"):
            st.session_state.current_page = 'notifications'
            st.rerun()
        
        # Divider
        st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)
        
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
def insurance_claims_page():
    """Enhanced insurance claims page with better UI"""
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
                st.markdown("<div class='image-gallery'>", unsafe_allow_html=True)
                for file in evidence_files:
                    is_valid, message = validate_image(file)
                    if is_valid:
                        image = Image.open(file)
                        st.image(image, use_container_width=True)
                    else:
                        st.error(message)
                st.markdown("</div>", unsafe_allow_html=True)
            
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
                        st.rerun()
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
                    'pending': 'pending',
                    'approved': 'approved',
                    'rejected': 'rejected',
                    'partial': 'pending',
                    'paid': 'approved'
                }
                status_class = status_colors.get(status.lower(), 'pending')
                
                st.markdown(f"""
                    <div class="insurance-claim-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                            <h3 style="margin: 0;">Claim #{claim_id} - {car_model} ({car_year})</h3>
                            <span class="status-badge {status_class}">{status.upper()}</span>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                            <div>
                                <p><strong>Booking ID:</strong> #{booking_id}</p>
                                <p><strong>Incident Date:</strong> {incident_date}</p>
                                <p><strong>Damage Type:</strong> {damage_type}</p>
                            </div>
                            <div>
                                <p><strong>Claim Amount:</strong> {format_currency(claim_amount)}</p>
                                <p><strong>Status:</strong> {status.title()}</p>
                            </div>
                        </div>
                """, unsafe_allow_html=True)
                
                # Show evidence images if available
                if claim[8]:  # evidence_images field
                    try:
                        evidence_images = json.loads(claim[8])
                        if evidence_images:
                            st.markdown("<h4>Evidence Photos</h4>", unsafe_allow_html=True)
                            st.markdown("<div class='image-gallery'>", unsafe_allow_html=True)
                            for img_data in evidence_images:
                                st.markdown(f"""
                                    <img src="data:image/jpeg;base64,{img_data}" alt="Evidence Photo">
                                """, unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                    except json.JSONDecodeError:
                        st.error("Error loading evidence images")
                
                # Show admin notes if available
                if admin_notes:
                    st.markdown(f"""
                        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                            <h4>Admin Notes</h4>
                            <p>{admin_notes}</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

def main():
    """Main application function"""
    try:
        # Check if PIL's ImageDraw is imported for image generation
        from PIL import Image, ImageDraw
        
        # Create necessary folders
        create_folder_structure()
        
        # Setup or update database with comprehensive table creation
        if not os.path.exists('car_rental.db'):
            setup_database()
        else:
            conn = None
            try:
                conn = sqlite3.connect('car_rental.db')
                c = conn.cursor()
                
                # Check and create missing tables/indexes
                table_schemas = {
                    'users': '''
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
                    ''',
                    'car_listings': '''
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
                    ''',
                    'listing_images': '''
                        CREATE TABLE IF NOT EXISTS listing_images (
                            id INTEGER PRIMARY KEY,
                            listing_id INTEGER NOT NULL,
                            image_data TEXT NOT NULL,
                            is_primary BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (listing_id) REFERENCES car_listings (id)
                        )
                    ''',
                    'bookings': '''
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
                    ''',
                    'insurance_claims': '''
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
                    ''',
                    'notifications': '''
                        CREATE TABLE IF NOT EXISTS notifications (
                            id INTEGER PRIMARY KEY,
                            user_email TEXT NOT NULL,
                            message TEXT NOT NULL,
                            type TEXT NOT NULL,
                            read BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_email) REFERENCES users (email)
                        )
                    ''',
                    'admin_reviews': '''
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
                    ''',
                    'subscription_history': '''
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
                    ''',
                    'reviews': '''
                        CREATE TABLE IF NOT EXISTS reviews (
                            id INTEGER PRIMARY KEY,
                            booking_id INTEGER NOT NULL,
                            user_email TEXT NOT NULL,
                            car_id INTEGER NOT NULL,
                            rating INTEGER NOT NULL,
                            comment TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (booking_id) REFERENCES bookings (id),
                            FOREIGN KEY (user_email) REFERENCES users (email),
                            FOREIGN KEY (car_id) REFERENCES car_listings (id)
                        )
                    '''
                }
                
                # Indexes to create
                indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)',
                    'CREATE INDEX IF NOT EXISTS idx_listings_status ON car_listings(listing_status)',
                    'CREATE INDEX IF NOT EXISTS idx_listings_category ON car_listings(category)',
                    'CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(booking_status)',
                    'CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_email, read)',
                    'CREATE INDEX IF NOT EXISTS idx_claims_status ON insurance_claims(claim_status)',
                    'CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscription_history(user_email)',
                    'CREATE INDEX IF NOT EXISTS idx_reviews_car_id ON reviews(car_id)',
                    'CREATE INDEX IF NOT EXISTS idx_reviews_booking_id ON reviews(booking_id)'
                ]
                
                # Check and create missing tables
                for table_name, table_schema in table_schemas.items():
                    c.execute(table_schema)
                
                # Create indexes
                for index_query in indexes:
                    c.execute(index_query)
                
                # Ensure sample data is added if no listings exist
                c.execute('SELECT COUNT(*) FROM car_listings')
                if c.fetchone()[0] == 0:
                    # Create admin user if not exists
                    c.execute('SELECT * FROM users WHERE email = ?', ('admin@luxuryrentals.com',))
                    if not c.fetchone():
                        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
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
                    
                    # Add sample car data
                    add_sample_data(c)
                
                conn.commit()
                print("Database tables checked and updated successfully")
            
            except sqlite3.Error as e:
                st.error(f"Database error during setup: {e}")
                print(f"Database error: {e}")
            finally:
                if conn:
                    conn.close()
        
        # Initialize session state variables if not already set
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if 'user_email' not in st.session_state:
            st.session_state.user_email = None
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'welcome'
        
        # Persist session if applicable
        persist_session()
        
        # Main app logic
        if not st.session_state.logged_in:
            # Default to welcome page when not logged in
            welcome_page()
        else:
            # Show sidebar for logged-in users
            show_sidebar()
            
            # Routing based on current page
            if st.session_state.current_page == 'welcome':
                welcome_page()
            elif st.session_state.current_page == 'login':
                login_page()
            elif st.session_state.current_page == 'signup':
                signup_page()
            elif st.session_state.current_page == 'browse_cars':
                browse_cars_page()
            elif st.session_state.current_page == 'car_details':
                show_car_details(st.session_state.selected_car)
            elif st.session_state.current_page == 'book_car':
                book_car_page()
            elif st.session_state.current_page == 'my_bookings':
                my_bookings_page()
            elif st.session_state.current_page == 'notifications':
                notifications_page()
            elif st.session_state.current_page == 'about_us':
                about_us_page()
            elif st.session_state.current_page == 'subscription_plans':
                subscription_plans_page()
            elif st.session_state.current_page == 'list_your_car':
                list_your_car_page()
            elif st.session_state.current_page == 'my_listings':
                my_listings_page()
            elif st.session_state.current_page == 'admin_dashboard':
                admin_dashboard()
            elif st.session_state.current_page == 'insurance_claims':
                insurance_claims_page()
            else:
                # Fallback to welcome page
                welcome_page()
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        print(f"Error details: {traceback.format_exc()}")

# Main app execution
if __name__ == '__main__':
    import traceback
    import streamlit as st
    main()
