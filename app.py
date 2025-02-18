import streamlit as st
import sqlite3
import hashlib
import os
import stripe
from datetime import datetime, timedelta
from PIL import Image
import base64
import io
import json

# Stripe API setup
STRIPE_SECRET_KEY = "your_stripe_secret_key"
stripe.api_key = STRIPE_SECRET_KEY

db_path = "permanent_car_rental.db"  # Permanent database

def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Users table with profile picture support
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            profile_pic TEXT,
            role TEXT DEFAULT 'user',
            subscription TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insurance claims table
    c.execute('''
        CREATE TABLE IF NOT EXISTS insurance_claims (
            id INTEGER PRIMARY KEY,
            user_email TEXT NOT NULL,
            car_id INTEGER NOT NULL,
            claim_description TEXT,
            claim_status TEXT DEFAULT 'pending',
            images TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    ''')
    
    # Subscriptions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY,
            user_email TEXT UNIQUE NOT NULL,
            plan TEXT NOT NULL,
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    ''')
    
    conn.commit()
    conn.close()

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Save profile picture
def save_profile_pic(uploaded_file):
    image = Image.open(uploaded_file)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    return base64.b64encode(img_byte_arr.getvalue()).decode()

# Subscription pricing
def get_subscription_pricing(plan):
    plans = {
        "free": 0,
        "premium": 20,
        "elite": 50,
        "host_premium": 50,
        "host_elite": 100
    }
    return plans.get(plan, 0)

# Process Stripe payment
def process_payment(email, plan):
    amount = get_subscription_pricing(plan) * 100  # Convert to cents
    if amount == 0:
        return False
    
    try:
        charge = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            description=f"Subscription for {plan} plan",
            receipt_email=email
        )
        return charge['status'] == 'succeeded'
    except Exception as e:
        st.error(f"Payment failed: {e}")
        return False

# Subscription handling
def subscribe_user(email, plan):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    end_date = datetime.now() + timedelta(days=30)
    c.execute('''
        INSERT INTO subscriptions (user_email, plan, end_date) 
        VALUES (?, ?, ?)
        ON CONFLICT(user_email) DO UPDATE SET plan=?, end_date=?, status='active'
    ''', (email, plan, end_date, plan, end_date))
    
    c.execute('''UPDATE users SET subscription=? WHERE email=?''', (plan, email))
    conn.commit()
    conn.close()
    
    st.success(f"You have successfully subscribed to the {plan.capitalize()} plan!")

# Show user profile
def show_profile():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT full_name, profile_pic, subscription FROM users WHERE email=?', (st.session_state.user_email,))
    user = c.fetchone()
    conn.close()
    
    if user:
        full_name, profile_pic, subscription = user
        st.sidebar.markdown(f"### {full_name}")
        if profile_pic:
            st.sidebar.image(f"data:image/jpeg;base64,{profile_pic}", width=100)
        st.sidebar.markdown(f"**Subscription:** {subscription.capitalize()}")

# Claim insurance
def claim_insurance():
    st.markdown("## Claim Insurance")
    claim_description = st.text_area("Describe the damage")
    uploaded_images = st.file_uploader("Upload Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if st.button("Submit Claim"):
        image_data = [save_profile_pic(img) for img in uploaded_images]
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO insurance_claims (user_email, car_id, claim_description, images) 
                     VALUES (?, ?, ?, ?)''', 
                  (st.session_state.user_email, 1, claim_description, json.dumps(image_data)))
        conn.commit()
        conn.close()
        st.success("Claim submitted successfully!")

# Main function
def main():
    st.sidebar.title("Luxury Car Rentals")
    show_profile()
    
    page = st.sidebar.radio("Navigation", ["Home", "Claim Insurance", "Subscribe"])
    
    if page == "Home":
        st.title("Welcome to Luxury Car Rentals")
        st.write("Premium car rental services with top-tier benefits.")
    elif page == "Claim Insurance":
        claim_insurance()
    elif page == "Subscribe":
        plan = st.selectbox("Choose a Subscription Plan", ["free", "premium", "elite", "host_premium", "host_elite"])
        if st.button("Subscribe Now"):
            if process_payment(st.session_state.user_email, plan):
                subscribe_user(st.session_state.user_email, plan)
            else:
                st.error("Subscription failed. Try again.")

if __name__ == "__main__":
    init_db()
    main()
