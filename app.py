import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import sqlite3
import os

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'welcome'

# Database setup
def init_db():
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
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
            'available': True
        },
        {
            'id': 2,
            'model': 'Rolls-Royce Ghost',
            'price': 3000,
            'location': 'Palm Jumeirah',
            'image': 'https://example.com/ghost.jpg',
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
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE email = ?', (email,))
    result = c.fetchone()
    conn.close()
    if result and result[0] == hash_password(password):
        return True
    return False

# Page components
def welcome_page():
    st.title('Luxury Car Rentals')
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Login'):
            st.session_state.current_page = 'login'
    with col2:
        if st.button('Create Account'):
            st.session_state.current_page = 'signup'

def login_page():
    st.title('Welcome Back')
    
    email = st.text_input('Email/Phone')
    password = st.text_input('Password', type='password')
    
    if st.button('Login'):
        if verify_user(email, password):
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.current_page = 'browse_cars'
            st.success('Login successful!')
        else:
            st.error('Invalid credentials')
    
    if st.button('Forgot Password?'):
        st.session_state.current_page = 'reset_password'
    
    if st.button('Back'):
        st.session_state.current_page = 'welcome'

def signup_page():
    st.title('Create Account')
    
    full_name = st.text_input('Full Name')
    email = st.text_input('Email')
    phone = st.text_input('Phone Number')
    password = st.text_input('Password', type='password')
    confirm_password = st.text_input('Confirm Password', type='password')
    
    if st.button('Create Account'):
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
    
    if st.button('Back'):
        st.session_state.current_page = 'welcome'

def reset_password_page():
    st.title('Reset Password')
    
    email = st.text_input('Enter your email to reset password')
    
    if st.button('Send Reset Link'):
        st.success('Check your email for password reset instructions')
    
    if st.button('Back'):
        st.session_state.current_page = 'login'

def browse_cars_page():
    st.title('Browse Cars')
    
    # Search bar
    search = st.text_input('Search (e.g., "Lamborghini")')
    
    # Category filters
    st.write('Categories')
    cols = st.columns(3)
    with cols[0]:
        luxury = st.button('Luxury')
    with cols[1]:
        suv = st.button('SUV')
    with cols[2]:
        sports = st.button('Sports')
    
    # Display cars
    for category, cars in cars_data.items():
        if (luxury and category == 'Luxury') or \
           (suv and category == 'SUV') or \
           (sports and category == 'Sports') or \
           (not any([luxury, suv, sports])):
            st.subheader(category)
            car_cols = st.columns(len(cars))
            for idx, car in enumerate(cars):
                if search.lower() in car['model'].lower() or not search:
                    with car_cols[idx]:
                        st.image(car['image'], use_column_width=True)
                        st.write(f"**{car['model']}**")
                        st.write(f"AED {car['price']}/day")
                        st.write(f"Location: {car['location']}")
                        if st.button(f'Select {car["model"]}'):
                            st.session_state.selected_car = car
                            st.session_state.current_page = 'book_car'

def book_car_page():
    st.title('Book Car')
    
    car = st.session_state.selected_car
    st.image(car['image'], use_column_width=True)
    st.write(f"**{car['model']}**")
    st.write(f"Price: AED {car['price']}/day")
    st.write(f"Location: {car['location']}")
    
    col1, col2 = st.columns(2)
    with col1:
        pickup_date = st.date_input('Pick-up Date')
        pickup_time = st.time_input('Pick-up Time')
    with col2:
        return_date = st.date_input('Return Date')
        return_time = st.time_input('Return Time')
    
    location = st.selectbox('Location', ['Dubai Marina', 'Palm Jumeirah', 'Downtown Dubai'])
    payment_method = st.selectbox('Payment Method', ['Credit Card', 'Debit Card'])
    
    if st.button('Confirm Booking'):
        # Calculate total price
        days = (return_date - pickup_date).days + 1
        total_price = days * car['price']
        
        # Save booking to database
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        c.execute(
            'INSERT INTO bookings (user_email, car_id, pickup_date, return_date, location, total_price) VALUES (?, ?, ?, ?, ?, ?)',
            (st.session_state.user_email, car['id'], pickup_date.isoformat(), return_date.isoformat(), location, total_price)
        )
        conn.commit()
        conn.close()
        
        st.session_state.current_page = 'confirmation'
        st.session_state.booking_details = {
            'car': car['model'],
            'pickup': f"{pickup_date} {pickup_time}",
            'return': f"{return_date} {return_time}",
            'location': location,
            'total': total_price
        }

def confirmation_page():
    st.title('Booking Confirmed!')
    
    details = st.session_state.booking_details
    st.write('Booking Summary:')
    st.write(f"Car: {details['car']}")
    st.write(f"Pick-up: {details['pickup']}")
    st.write(f"Return: {details['return']}")
    st.write(f"Location: {details['location']}")
    st.write(f"Total: AED {details['total']}")
    
    if st.button('Back to Browse'):
        st.session_state.current_page = 'browse_cars'

# Main app
def main():
    if st.session_state.current_page == 'welcome':
        welcome_page()
    elif st.session_state.current_page == 'login':
        login_page()
    elif st.session_state.current_page == 'signup':
        signup_page()
    elif st.session_state.current_page == 'reset_password':
        reset_password_page()
    elif st.session_state.current_page == 'browse_cars':
        if st.session_state.logged_in:
            browse_cars_page()
        else:
            st.warning('Please log in first')
            st.session_state.current_page = 'login'
    elif st.session_state.current_page == 'book_car':
        if st.session_state.logged_in:
            book_car_page()
        else:
            st.warning('Please log in first')
            st.session_state.current_page = 'login'
    elif st.session_state.current_page == 'confirmation':
        confirmation_page()

if __name__ == '__main__':
    main()
