import streamlit as st
import sqlite3
import os
import hashlib
import base64
from PIL import Image

# Ensure Database is Persistent
db_path = "car_rental.db"

def get_connection():
    return sqlite3.connect(db_path, check_same_thread=False)

# Ensure database setup only runs if it doesn't exist
def setup_database():
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT NOT NULL,
                    password TEXT NOT NULL,
                    profile_picture TEXT,
                    subscription TEXT DEFAULT 'free',
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS insurance_claims (
                    id INTEGER PRIMARY KEY,
                    user_email TEXT NOT NULL,
                    car_id INTEGER NOT NULL,
                    incident_details TEXT NOT NULL,
                    claim_status TEXT DEFAULT 'pending',
                    image_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_email) REFERENCES users(email)
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY,
                    user_email TEXT UNIQUE NOT NULL,
                    plan TEXT NOT NULL,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_email) REFERENCES users(email)
                )''')
    
    conn.commit()
    conn.close()

setup_database()

# Hashing passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Save profile picture
def save_uploaded_image(uploaded_file):
    image = Image.open(uploaded_file)
    image = image.convert("RGB")
    img_byte_arr = base64.b64encode(image.tobytes()).decode()
    return img_byte_arr

# Registration with Profile Picture
def create_user(full_name, email, phone, password, profile_picture=None):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        if c.fetchone():
            return False
        
        c.execute('''INSERT INTO users (full_name, email, phone, password, profile_picture)
                     VALUES (?, ?, ?, ?, ?)''', (full_name, email, phone, hash_password(password), profile_picture))
        conn.commit()
        return True
    except sqlite3.Error as e:
        return False
    finally:
        conn.close()

# Display Profile Picture & Name in Sidebar
def display_user_sidebar():
    if 'user_email' in st.session_state:
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT full_name, profile_picture FROM users WHERE email = ?', (st.session_state.user_email,))
        user = c.fetchone()
        conn.close()
        
        if user:
            name, profile_picture = user
            st.sidebar.markdown(f"## Welcome, {name}")
            if profile_picture:
                image_data = base64.b64decode(profile_picture)
                st.sidebar.image(Image.frombytes("RGB", (200, 200), image_data), caption="Profile Picture", use_column_width=True)

# Insurance Claim Submission
def submit_insurance_claim(car_id, incident_details, uploaded_file):
    try:
        image_data = save_uploaded_image(uploaded_file) if uploaded_file else None
        conn = get_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO insurance_claims (user_email, car_id, incident_details, image_data)
                     VALUES (?, ?, ?, ?)''', (st.session_state.user_email, car_id, incident_details, image_data))
        conn.commit()
        return True
    except sqlite3.Error as e:
        return False
    finally:
        conn.close()

# Subscription System
def subscribe_user(plan):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO subscriptions (user_email, plan) VALUES (?, ?)
                     ON CONFLICT(user_email) DO UPDATE SET plan = excluded.plan''',
                  (st.session_state.user_email, plan))
        conn.commit()
        return True
    except sqlite3.Error as e:
        return False
    finally:
        conn.close()

# UI for Subscription Selection
def subscription_page():
    st.title("Choose Your Subscription Plan")
    plans = {"free": "Free Plan", "premium": "Premium Plan ($20/month)", "elite": "Elite VIP Plan ($50/month)"}
    choice = st.radio("Select a plan", list(plans.keys()), format_func=lambda x: plans[x])
    if st.button("Subscribe Now"):
        if subscribe_user(choice):
            st.success(f"You are now subscribed to {plans[choice]}!")
        else:
            st.error("Subscription failed. Try again.")

# About Us with SDG
def about_us_page():
    st.title("About Us")
    st.markdown("""
        **Luxury Car Rentals** provides premium and exotic car rentals in Dubai. 
        Our mission is to make luxury accessible while promoting sustainability through shared vehicle usage.
    
        ### Sustainable Development Goal (SDG 11): Sustainable Cities and Communities
        By encouraging car rentals instead of ownership, we help reduce urban congestion and environmental impact.
    
        ### Why Choose Us?
        - Wide range of luxury cars
        - Seamless booking process
        - Insurance & roadside assistance options
    """)

# Persistent Page Reload Handling
def get_current_page():
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    return st.session_state.current_page

def set_current_page(page):
    st.session_state.current_page = page
    st.experimental_rerun()

# Navigation
st.sidebar.button("Home", on_click=lambda: set_current_page('home'))
st.sidebar.button("My Subscription", on_click=lambda: set_current_page('subscription'))
st.sidebar.button("About Us", on_click=lambda: set_current_page('about'))

display_user_sidebar()

# Page Routing
page = get_current_page()
if page == "home":
    st.title("Welcome to Luxury Car Rentals")
elif page == "subscription":
    subscription_page()
elif page == "about":
    about_us_page()
