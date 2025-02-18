import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import io
import base64
from PIL import Image
from datetime import datetime

# ---- Page Configuration ----
st.set_page_config(page_title="Luxury Car Rentals", layout="wide")

# ---- CSS Styling ----
st.markdown("""
    <style>
        .stApp {
            background-color: #F4F4F8;
            font-family: 'Inter', sans-serif;
        }
        .profile-pic {
            border-radius: 50%;
            width: 100px;
            height: 100px;
            object-fit: cover;
        }
    </style>
""", unsafe_allow_html=True)

# ---- Permanent Database Setup ----
# ---- Permanent Database Setup ----
DB_FILE = "permanent_car_rental.db"
def setup_database():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        profile_picture TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS insurance_claims (
        id INTEGER PRIMARY KEY,
        user_email TEXT NOT NULL,
        car_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        proof_image TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

setup_database()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(full_name, email, phone, password, profile_picture=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    hashed_pw = hash_password(password)
    
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    if c.fetchone():
        return False
    
    c.execute('''INSERT INTO users (full_name, email, phone, password, profile_picture)
                 VALUES (?, ?, ?, ?, ?)''',
                 (full_name, email, phone, hashed_pw, profile_picture))
    conn.commit()
    conn.close()
    return True

def verify_user(email, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE email = ?', (email,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == hash_password(password)

def get_user_details(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT full_name, profile_picture FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    return user

# ---- Profile Picture Handling ----
def save_profile_picture(uploaded_file):
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        return base64.b64encode(img_byte_arr.getvalue()).decode()
    return None

# ---- Sidebar Navigation ----
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

if st.session_state.logged_in:
    user_name, profile_picture = get_user_details(st.session_state.user_email)
    with st.sidebar:
        if profile_picture:
            st.image(f"data:image/jpeg;base64,{profile_picture}", caption=user_name, width=100)
        else:
            st.write(f"Welcome, {user_name}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_email = None
            st.rerun()

# ---- User Authentication ----
def login_page():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_user(email, password):
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.success("Login Successful!")
            st.rerun()
        else:
            st.error("Invalid Credentials")

def signup_page():
    st.title("Create Account")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    profile_picture = st.file_uploader("Upload Profile Picture (Optional)", type=["jpg", "png"])
    
    if st.button("Create Account"):
        if password != confirm_password:
            st.error("Passwords do not match")
        else:
            picture_data = save_profile_picture(profile_picture)
            if create_user(full_name, email, phone, password, picture_data):
                st.success("Account Created Successfully!")
                st.session_state.current_page = 'login'
                st.rerun()
            else:
                st.error("Email already exists")


# ---- Subscription Plans ----
SUBSCRIPTION_PLANS = {
    "renter": {
        "Free": {"fee": 0, "benefits": ["Standard service fees", "No booking priority", "No special discounts"]},
        "Premium": {"fee": 20, "benefits": ["Reduced service fees", "Priority booking", "10% discount on rentals"]},
        "Elite VIP": {"fee": 50, "benefits": ["Lowest service fees", "First priority booking", "20% discount on rentals"]}
    },
    "host": {
        "Free": {"fee": 0, "benefits": ["Standard listing visibility", "15% commission per booking"]},
        "Premium": {"fee": 50, "benefits": ["Boosted visibility", "Lower commission (10%)"]},
        "Elite": {"fee": 100, "benefits": ["Top placement", "Lowest commission (5%)"]}
    }
}

# ---- Insurance Claims ----

def submit_insurance_claim(user_email, car_id, description, proof_file):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    image_data = base64.b64encode(proof_file.read()).decode()
    c.execute("""
        INSERT INTO insurance_claims (user_email, car_id, description, proof_image, status, created_at)
        VALUES (?, ?, ?, ?, 'pending', ?)
    """, (user_email, car_id, description, image_data, datetime.now()))
    conn.commit()
    conn.close()

def view_insurance_claims():
    st.markdown("# Insurance Claims")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM insurance_claims")
    claims = c.fetchall()
    conn.close()
    if claims:
        for claim in claims:
            st.write(f"**User:** {claim[1]} | **Car ID:** {claim[2]} | **Status:** {claim[5]}")
            st.write(f"**Description:** {claim[3]}")
            st.image(base64.b64decode(claim[4]), caption="Proof Image")
            if st.button("Approve", key=f"approve_{claim[0]}"):
                update_insurance_claim(claim[0], "approved")
            if st.button("Reject", key=f"reject_{claim[0]}"):
                update_insurance_claim(claim[0], "rejected")
    else:
        st.info("No insurance claims yet.")

def update_insurance_claim(claim_id, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE insurance_claims SET status = ? WHERE id = ?", (status, claim_id))
    conn.commit()
    conn.close()
    st.success(f"Claim {status} successfully!")
    st.experimental_rerun()

# ---- About Us & SDG Section ----
def about_us():
    st.markdown("""
        # About Us 🚗
        Welcome to **Luxury Car Rentals**, where luxury meets convenience. Our mission is to provide premium car rental experiences
        for tourists, expats, and luxury enthusiasts in Dubai.

        ## Our SDG Commitment 🌍
        We align with the **United Nations Sustainable Development Goals (SDGs)**:
        - **SDG 12 (Responsible Consumption & Production):** We promote sustainable car-sharing practices to reduce carbon footprint.
        - **SDG 11 (Sustainable Cities & Communities):** By optimizing vehicle usage, we contribute to smarter urban mobility.
        - **SDG 9 (Industry, Innovation & Infrastructure):** Our AI-driven platform ensures efficient resource allocation.
    """, unsafe_allow_html=True)

# ---- Page Routing ----
if not st.session_state.get("logged_in", False):
    login_page()
else:
    user_name, profile_picture = get_user_details(st.session_state.user_email)
    with st.sidebar:
        if profile_picture:
            st.image(f"data:image/jpeg;base64,{profile_picture}", caption=user_name, width=100)
        else:
            st.write(f"Welcome, {user_name}")
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to", ["Dashboard", "List Car", "My Bookings", "Insurance Claims", "Subscriptions", "About Us"])
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.session_state["user_email"] = None
            st.rerun()
    
    if page == "Dashboard":
        st.write("Welcome to the dashboard!")
    elif page == "List Car":
        list_your_car_page()
    elif page == "My Bookings":
        my_bookings_page()
    elif page == "Insurance Claims":
        if get_user_role(st.session_state.user_email) == "admin":
            view_insurance_claims()
        else:
            submit_insurance_claim()
    elif page == "Subscriptions":
        manage_subscriptions()
    elif page == "About Us":
        about_us()
