import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import sqlite3
import os

# Page config and custom CSS
st.set_page_config(page_title="Luxury Car Rentals", layout="wide")

# Custom CSS
st.markdown("""
    <style>
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
        
        .css-1d391kg {
            padding: 2rem 1rem;
        }
        
        input[type="text"], input[type="password"] {
            border-radius: 20px;
            padding: 10px 15px;
            border: 2px solid #4B0082;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: #6A0DAD;
            box-shadow: 0 0 5px rgba(106,13,173,0.5);
        }
        
        h1 {
            color: #4B0082;
            text-align: center;
            padding: 1rem 0;
        }
        
        .car-card {
            background-color: white;
            border-radius: 15px;
            padding: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        
        .car-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        }
        
        .success-message {
            background-color: #E8F5E9;
            color: #2E7D32;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        
        .error-message {
            background-color: #FFEBEE;
            color: #C62828;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
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

# Database setup
def init_db():
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
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
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Sample car data with images (replace with your actual image paths)
def load_car_data():
    return {
        'Luxury': [
            {
                'id': 1,
                'model': 'Lamborghini Urus',
                'price': 2500,
                'location': 'Dubai Marina',
                'image': 'images/urus.jpg',  # Replace with actual image path
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
                'image': 'images/ghost.jpg',  # Replace with actual image path
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
                'image': 'images/range_rover.jpg',  # Replace with actual image path
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
                'image': 'images/f8.jpg',  # Replace with actual image path
                'specs': {
                    'engine': '3.9L V8 Twin-Turbo',
                    'power': '710 hp',
                    'acceleration': '0-60 mph in 2.9s'
                },
                'available': True
            }
        ]
    }

# Load car data
cars_data = load_car_data()

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

def login_page():
    if st.button('← Back to Welcome', key='login_back'):
        st.session_state.current_page = 'welcome'
    
    st.markdown("<h1>Welcome Back</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        email = st.text_input('Email/Phone')
        password = st.text_input('Password', type='password')
        
        if st.button('Login', key='login_submit'):
            if verify_user(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.current_page = 'browse_cars'
                st.success('Login successful!')
            else:
                st.error('Invalid credentials')
        
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
    col1, col2, col3 = st.columns([1,8,1])
    with col1:
        if st.button('← Back', key='browse_back'):
            st.session_state.current_page = 'welcome'
    with col3:
        if st.button('Logout', key='logout'):
            st.session_state.logged_in = False
            st.session_state.current_page = 'welcome'
    
    st.markdown("<h1>Explore Our Fleet</h1>", unsafe_allow_html=True)
    
    # Search and filters
    search = st.text_input('Search for your dream car', placeholder='e.g., "Lamborghini"')
    
    st.markdown("<h3 style='color: #4B0082; margin-top: 1rem;'>Categories</h3>", unsafe_allow_html=True)
    cat_col1, cat_col2, cat_col3 = st.columns(3)
    
    with cat_col1:
        luxury = st.button('🎯 Luxury', key='luxury_filter')
    with cat_col2:
        suv = st.button('🚙 SUV', key='suv_filter')
    with cat_col3:
        sports = st.button('🏎 Sports', key='sports_filter')
    
    # Display cars
    for category, cars in cars_data.items():
        if (luxury and category == 'Luxury') or \
           (suv and category == 'SUV') or \
           (sports and category == 'Sports') or \
           (not any([luxury, suv, sports])):
            
            st.markdown(f"<h2 style='color: #4B0082; margin-top: 2rem;'>{category}</h2>", unsafe_allow_html=True)
            
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

def book_car_page():
    if st.button('← Back to Browse', key='book_back'):
        st.session_state.current_page = 'browse_cars'
    
    st.markdown("<h1>Book Your Car</h1>", unsafe_allow_html=True)
    
    car = st.session_state.selected_car
    
    # Display car details
    col1, col2 = st.columns(2)
    with col1:
        st.image(car['image'], use_column_width=True)
    with col2:
        st.markdown(f"""
            <div class='car-card'>
                <h2 style='color: #4B0082;'>{car['model']}</h2>
                <p style='font-size: 1.5rem; color: #666;'>AED {car['price']}/day</p>
                <p style='color: #666;'>{car['location']}</p>
                <div style='margin-top: 1rem;'>
                    <p>🏎 {car['specs']['engine']}</p>
                    <p>⚡ {car['specs']['power']}</p>
                    <p>🚀 {car['specs']['acceleration']}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Booking details section
    st.markdown("<h3 style='color: #4B0082; margin-top: 2rem;'>Booking Details</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        pickup_date = st.date_input('Pick-up Date', min_value=datetime.today())
        pickup_time = st.time_input('Pick-up Time')
    with col2:
        return_date = st.date_input('Return Date', min_value=pickup_date)
        return_time = st.time_input('Return Time')
    
    # Additional details
    st.markdown("<div style='background-color: #f8f9fa; padding: 1.5rem; border-radius: 15px; margin-top: 1rem;'>", unsafe_allow_html=True)
    location = st.selectbox('Pickup Location', ['Dubai Marina', 'Palm Jumeirah', 'Downtown Dubai'])
    payment_method = st.selectbox('Payment Method', ['Credit Card', 'Debit Card'])
    
    # Additional services
    st.markdown("<h4 style='color: #4B0082; margin-top: 1rem;'>Additional Services</h4>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        insurance = st.checkbox('Full Insurance (+AED 150/day)', help='Comprehensive insurance coverage')
        driver = st.checkbox('Professional Driver (+AED 500/day)', help='Experienced chauffeur service')
    with col2:
        delivery = st.checkbox('Car Delivery (+AED 200)', help='Delivery to your location')
        vip_service = st.checkbox('VIP Service (+AED 300)', help='Priority support and exclusive benefits')
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Price calculation
    days = (return_date - pickup_date).days + 1
    base_price = days * car['price']
    additional_costs = 0
    
    if insurance:
        additional_costs += 150 * days
    if driver:
        additional_costs += 500 * days
    if delivery:
        additional_costs += 200
    if vip_service:
        additional_costs += 300
    
    total_price = base_price + additional_costs
    
    # Price breakdown
    st.markdown(f"""
        <div style='background-color: #4B0082; color: white; padding: 1.5rem; border-radius: 15px; margin-top: 1rem;'>
            <h3>Price Breakdown</h3>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0;'>
                <div>
                    <p>Base Rental ({days} days)</p>
                    <p>Full Insurance</p>
                    <p>Professional Driver</p>
                    <p>Car Delivery</p>
                    <p>VIP Service</p>
                </div>
                <div style='text-align: right;'>
                    <p>AED {base_price}</p>
                    <p>AED {150 * days if insurance else 0}</p>
                    <p>AED {500 * days if driver else 0}</p>
                    <p>AED {200 if delivery else 0}</p>
                    <p>AED {300 if vip_service else 0}</p>
                </div>
            </div>
            <hr style='border-color: white; margin: 1rem 0;'>
            <h2 style='text-align: right;'>Total: AED {total_price}</h2>
        </div>
    """, unsafe_allow_html=True)
    
    # Payment section
    if st.button('Proceed to Payment', key='payment'):
        # Save booking to database
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO bookings 
                (user_email, car_id, pickup_date, return_date, location, 
                total_price, insurance, driver, delivery, vip_service)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                st.session_state.user_email, car['id'], 
                f"{pickup_date} {pickup_time}", f"{return_date} {return_time}",
                location, total_price, insurance, driver, delivery, vip_service
            ))
            conn.commit()
            
            # Store booking details in session state
            st.session_state.booking_details = {
                'car': car['model'],
                'pickup': f"{pickup_date} {pickup_time}",
                'return': f"{return_date} {return_time}",
                'location': location,
                'total': total_price,
                'additional_services': {
                    'insurance': insurance,
                    'driver': driver,
                    'delivery': delivery,
                    'vip_service': vip_service
                }
            }
            st.session_state.current_page = 'confirmation'
            
        except Exception as e:
            st.error(f"An error occurred while processing your booking. Please try again.")
        finally:
            conn.close()

def confirmation_page():
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h1>🎉 Booking Confirmed!</h1>
            <p style='color: #4B0082; font-size: 1.2rem;'>Your luxury car experience awaits</p>
        </div>
    """, unsafe_allow_html=True)
    
    details = st.session_state.booking_details
    
    # Booking summary card
    st.markdown(f"""
        <div style='background-color: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 2rem 0;'>
            <h2 style='color: #4B0082; margin-bottom: 1rem;'>Booking Summary</h2>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;'>
                <div>
                    <p style='color: #666;'><strong>Car:</strong> {details['car']}</p>
                    <p style='color: #666;'><strong>Pick-up:</strong> {details['pickup']}</p>
                    <p style='color: #666;'><strong>Location:</strong> {details['location']}</p>
                </div>
                <div>
                    <p style='color: #666;'><strong>Return:</strong> {details['return']}</p>
                    <p style='color: #666;'><strong>Additional Services:</strong></p>
                    <ul style='color: #666;'>
                        {f"<li>Full Insurance</li>" if details['additional_services']['insurance'] else ""}
                        {f"<li>Professional Driver</li>" if details['additional_services']['driver'] else ""}
                        {f"<li>Car Delivery</li>" if details['additional_services']['delivery'] else ""}
                        {f"<li>VIP Service</li>" if details['additional_services']['vip_service'] else ""}
                    </ul>
                </div>
            </div>
            <h3 style='color: #4B0082; margin-top: 1rem; text-align: right;'>Total: AED {details['total']}</h3>
        </div>
        
        <div style='background-color: #E8F5E9; padding: 1rem; border-radius: 15px; margin-top: 1rem;'>
            <p style='color: #2E7D32;'>📧 A confirmation email has been sent to your registered email address.</p>
            <p style='color: #2E7D32;'>📞 Our customer service team will contact you shortly to confirm the details.</p>
            <p style='color: #2E7D32;'>🎁 Your VIP welcome package will be prepared for your arrival.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Download booking details button
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button('Download Booking Details', key='download'):
            # Here you would implement the download functionality
            st.success('Booking details downloaded successfully!')
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        if st.button('Return to Home', key='return_home'):
            st.session_state.current_page = 'browse_cars'

# Main app remains the same
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
                
