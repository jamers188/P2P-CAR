import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import sqlite3
import os

# Custom CSS for better UI
st.set_page_config(page_title="Luxury Car Rentals", layout="wide")

# Add custom CSS
st.markdown("""
    <style>
        /* Main container styling */
        .main {
            padding: 2rem;
        }
        
        /* Custom button styling */
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
        
        /* Navigation button styling */
        .nav-button {
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 1000;
        }
        
        /* Card styling */
        .car-card {
            background-color: white;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        
        .car-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        }
        
        /* Input field styling */
        .stTextInput>div>div>input {
            border-radius: 20px;
            border: 2px solid #4B0082;
            padding: 1rem;
        }
        
        /* Header styling */
        h1 {
            color: #4B0082;
            font-size: 3rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        /* Category buttons */
        .category-button {
            background-color: #F0E6FA;
            border-radius: 15px;
            padding: 1rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .category-button:hover {
            background-color: #4B0082;
            color: white;
        }
        
        /* Success message styling */
        .success-message {
            background-color: #E8F5E9;
            color: #2E7D32;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            margin: 1rem 0;
        }
        
        /* Error message styling */
        .error-message {
            background-color: #FFEBEE;
            color: #C62828;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            margin: 1rem 0;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state (same as before)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'welcome'

# Enhanced welcome page
def welcome_page():
    st.markdown("<h1>Luxury Car Rentals</h1>", unsafe_allow_html=True)
    
    # Welcome message with animation
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h2 style='color: #4B0082;'>Experience Luxury on Wheels</h2>
            <p style='font-size: 1.2rem; color: #666;'>Discover our exclusive collection of premium vehicles</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create a centered container for buttons
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div style='padding: 2rem;'>", unsafe_allow_html=True)
        if st.button('Login', key='welcome_login'):
            st.session_state.current_page = 'login'
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        if st.button('Create Account', key='welcome_signup'):
            st.session_state.current_page = 'signup'
        st.markdown("</div>", unsafe_allow_html=True)

# Enhanced login page
def login_page():
    # Back button
    if st.button('← Back', key='login_back'):
        st.session_state.current_page = 'welcome'
    
    st.markdown("<h1>Welcome Back</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container():
            st.markdown("<div class='login-form'>", unsafe_allow_html=True)
            email = st.text_input('Email/Phone')
            password = st.text_input('Password', type='password')
            
            if st.button('Login', key='login_submit'):
                if verify_user(email, password):
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.current_page = 'browse_cars'
                    st.markdown("<div class='success-message'>Login successful!</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='error-message'>Invalid credentials</div>", unsafe_allow_html=True)
            
            st.markdown("<div style='text-align: center; margin-top: 1rem;'>", unsafe_allow_html=True)
            if st.button('Forgot Password?', key='forgot_password'):
                st.session_state.current_page = 'reset_password'
            st.markdown("</div>", unsafe_allow_html=True)

# Enhanced browse cars page
def browse_cars_page():
    st.markdown("<h1>Explore Our Fleet</h1>", unsafe_allow_html=True)
    
    # Top navigation bar
    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.button('← Back to Welcome', key='browse_back'):
            st.session_state.current_page = 'welcome'
    with col3:
        if st.button('Logout', key='logout'):
            st.session_state.logged_in = False
            st.session_state.current_page = 'welcome'
    
    # Search and filters
    st.markdown("<div style='background-color: #F8F9FA; padding: 2rem; border-radius: 15px; margin: 2rem 0;'>", unsafe_allow_html=True)
    search = st.text_input('Search for your dream car', placeholder='e.g., "Lamborghini"')
    
    # Category filters with custom styling
    st.markdown("<h3 style='color: #4B0082; margin-top: 1rem;'>Categories</h3>", unsafe_allow_html=True)
    cat_col1, cat_col2, cat_col3 = st.columns(3)
    
    with cat_col1:
        luxury = st.button('🎯 Luxury', key='luxury_filter')
    with cat_col2:
        suv = st.button('🚙 SUV', key='suv_filter')
    with cat_col3:
        sports = st.button('🏎 Sports', key='sports_filter')
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Display cars in a grid
    for category, cars in cars_data.items():
        if (luxury and category == 'Luxury') or \
           (suv and category == 'SUV') or \
           (sports and category == 'Sports') or \
           (not any([luxury, suv, sports])):
            
            st.markdown(f"<h2 style='color: #4B0082; margin-top: 2rem;'>{category}</h2>", unsafe_allow_html=True)
            
            # Create a grid of car cards
            cols = st.columns(min(3, len(cars)))
            for idx, car in enumerate(cars):
                if search.lower() in car['model'].lower() or not search:
                    with cols[idx % 3]:
                        st.markdown(f"""
                            <div class='car-card'>
                                <img src='{car['image']}' style='width: 100%; border-radius: 10px;'>
                                <h3 style='color: #4B0082; margin: 1rem 0;'>{car['model']}</h3>
                                <p style='color: #666;'>AED {car['price']}/day</p>
                                <p style='color: #666;'>{car['location']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f'Book Now', key=f"book_{car['id']}"):
                            st.session_state.selected_car = car
                            st.session_state.current_page = 'book_car'

# Enhanced booking confirmation page
def confirmation_page():
    st.markdown("<h1>Booking Confirmed! 🎉</h1>", unsafe_allow_html=True)
    
    details = st.session_state.booking_details
    
    # Display booking summary in a card
    st.markdown(f"""
        <div style='background-color: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 2rem 0;'>
            <h2 style='color: #4B0082; margin-bottom: 1rem;'>Booking Summary</h2>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;'>
                <div>
                    <p style='color: #666;'><strong>Car:</strong> {details['car']}</p>
                    <p style='color: #666;'><strong>Pick-up:</strong> {details['pickup']}</p>
                </div>
                <div>
                    <p style='color: #666;'><strong>Return:</strong> {details['return']}</p>
                    <p style='color: #666;'><strong>Location:</strong> {details['location']}</p>
                </div>
            </div>
            <h3 style='color: #4B0082; margin-top: 1rem;'>Total: AED {details['total']}</h3>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button('Back to Browse', key='confirmation_back'):
            st.session_state.current_page = 'browse_cars'

# Main app (same as before)
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
