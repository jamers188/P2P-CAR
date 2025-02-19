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

# New imports for enhanced features
import streamlit_authenticator as stauth
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
import requests
from geopy.geocoders import Nominatim
import folium 
from streamlit_folium import folium_static
import qrcode
from twilio.rest import Client
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model

# Fancy fonts and icons
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.0/css/all.min.css"/>
""", unsafe_allow_html=True)

# Page config
st.set_page_config(
    page_title="LuxeRides | Premium Car Rental",
    page_icon=":sports_car:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.luxerides.com/help',
        'Report a bug': "https://www.luxerides.com/bug",
        'About': "Luxury car rentals made easy. LuxeRides focuses on premium service, sustainability, and giving back to local communities."
    }
)

# Load CSS styles
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:    
    st.session_state.user_email = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'selected_car' not in st.session_state:
    st.session_state.selected_car = None

# Database setup - SQLite3
def setup_database():
    # Connect to database 
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()

    # Create tables if not exists
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            phone TEXT,
            role TEXT,
            profile_pic TEXT,
            created_at TIMESTAMP
        )
    ''')
    
    # Car listings table
    c.execute('''
        CREATE TABLE IF NOT EXISTS car_listings (
            listing_id INTEGER PRIMARY KEY,
            owner_email TEXT,
            vehicle_type TEXT,
            make TEXT,
            model TEXT,
            year INTEGER,
            color TEXT,
            price REAL,
            location TEXT,
            lat REAL,
            lon REAL, 
            description TEXT,
            added_features TEXT,
            image_data BLOB,
            created_at TIMESTAMP,
            FOREIGN KEY (owner_email) REFERENCES users (email)
        )
    ''')

    # Bookings table  
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY,
            renter_email TEXT,
            car_id INTEGER, 
            owner_email TEXT,
            pickup_date TEXT,
            return_date TEXT,
            pickup_location TEXT,
            dropoff_location TEXT,
            airport_pickup INTEGER,
            home_delivery INTEGER,
            trip_details TEXT,
            price REAL,
            booking_status TEXT,
            confirm_code TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY(renter_email) REFERENCES users(email), 
            FOREIGN KEY (car_id) REFERENCES car_listings(listing_id),
            FOREIGN KEY(owner_email) REFERENCES users(email)
        )
    ''')

    # Reviews table
    c.execute('''  
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY,
            booking_id INTEGER,
            reviewer_email TEXT,
            reviewee_email TEXT,
            rating INTEGER,
            review_text TEXT,
            review_response TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY(booking_id) REFERENCES bookings(booking_id),
            FOREIGN KEY(reviewer_email) REFERENCES users(email),
            FOREIGN KEY(reviewee_email) REFERENCES users(email)    
        )
    ''')

    # Insert admin user if not exists
    c.execute('''
        INSERT OR IGNORE INTO users (name, email, password, role)
        VALUES ('Admin', 'admin@luxerides.com', ?, 'admin')
    ''', (stauth.Hasher(['admin123']).generate()[0],))

    conn.commit()
    conn.close()

setup_database()

# Utility functions
def load_lottie(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)
  
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def save_uploaded_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        byte_im = buf.getvalue()
        return byte_im
    except:
        return None

def get_geocode(location):
    locator = Nominatim(user_agent='LuxeRides')
    location = locator.geocode(location)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None
    
def send_sms(to, msg):
    try:
        client = Client(st.secrets['TWILIO_ACCOUNT_SID'], st.secrets['TWILIO_AUTH_TOKEN'])
        client.messages.create(to=to, from_=st.secrets['TWILIO_PHONE_NUMBER'], body=msg)
    except:
        pass

# Machine Learning functions
CLASS_NAMES = ['damage', 'no_damage']

def detect_damage(image):
    model = load_model('car_damage_detector.h5')
    img = img_to_array(image.resize((224, 224))) 
    img = preprocess_input(img)
    img = img.reshape(1, 224, 224, 3)
    pred = model.predict(img)
    return CLASS_NAMES[pred.argmax()]

# Authentication 
def verify_login(email, password):
    conn = sqlite3.connect('luxerides.db') 
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE email = ?', (email,))
    db_password = c.fetchone()
    conn.close()

    if db_password:
        return db_password[0] == hash_password(password)
    return False

# App Navigation
def nav_sidebar():
    menu_items = ['Home', 'Browse Cars', 'List Your Car', 'Your Trips', 'Your Listings', 'Profile']
    icons = ['house', 'search', 'car', 'map-marked', 'list', 'user']
    
    with st.sidebar:
        if not st.session_state.logged_in:
            selected = option_menu(
                menu_title="Menu",
                options=['Home', 'Browse Cars', 'Login'],
                icons=['house', 'search', 'user'],
                default_index=0
            )
        else:
            selected = option_menu(
                menu_title="Menu", 
                options=menu_items,
                icons=icons,
                default_index=0
            )
            
    return selected    

# App Pages  
def login_page():
    st.title("Login to LuxeRides")
    
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        if verify_login(email, password):
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.success("Logged in successfully!")
            st.experimental_rerun()
        else:
            st.error("Invalid email or password")
            
    st.markdown("Don't have an account? [Register now](/register)")
            
def register_page():
    st.title("Create a LuxeRides Account")

    name = st.text_input("Full Name")    
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    password = st.text_input("Password", type='password') 
    confirm_password = st.text_input("Confirm Password", type='password')

    if st.button("Register"):
        if password == confirm_password:
            conn = sqlite3.connect('luxerides.db')
            c = conn.cursor()
            c.execute('INSERT INTO users (name, email, phone, password, created_at) VALUES (?, ?, ?, ?, ?)', 
                      (name, email, phone, hash_password(password), datetime.now()))
            conn.commit() 
            conn.close()
            
            st.success("Account created successfully! You can now login.")
            time.sleep(2)
            st.session_state.current_page = 'login'
            st.experimental_rerun()
        else:
            st.error("Passwords do not match")
            
def profile_page():
    st.title(f"Welcome, {st.session_state.user_name}! 👋")

    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()

    # Fetch user details  
    c.execute('SELECT * FROM users WHERE email = ?', (st.session_state.user_email,))
    user_info = c.fetchone()

    # Display user info  
    st.write("**Name:**", user_info[1])
    st.write("**Email:**", user_info[2]) 
    st.write("**Phone:**", user_info[4])
    st.write("**Member Since:**", user_info[7])

    # Update info form
    with st.expander("Update Your Information"):
        name = st.text_input("Name", value=user_info[1])
        phone = st.text_input("Phone", value=user_info[4])
        profile_pic = st.file_uploader("Profile Picture", type=['jpg', 'jpeg', 'png'])

        if st.button("Update"):
            if profile_pic:
                profile_pic = save_uploaded_image(profile_pic) 
                c.execute('UPDATE users SET name = ?, phone = ?, profile_pic = ? WHERE email = ?',
                          (name, phone, profile_pic, st.session_state.user_email))
            else:  
                c.execute('UPDATE users SET name = ?, phone = ? WHERE email = ?',
                          (name, phone, st.session_state.user_email))
                
            conn.commit()
            st.success("Profile updated successfully!")

    conn.close()


def home_page():
    st.title("Welcome to LuxeRides! 🚗💨")
    
    # Hero section
    st.write("""
        LuxeRides is your premier destination for luxury car rentals. 
        Whether you're looking for a sleek sports car for a weekend getaway or a spacious SUV for a family trip, 
        we've got you covered. With our easy-to-use app, you can browse, book, and unlock your dream car in just a few taps!
    """)
    
    # Featured cars carousel
    st.subheader("Featured Rides")
    cars = get_featured_cars()
    display_car_carousel(cars)
    
    # How it works section
    st.subheader("How LuxeRides Works")
    st.write("1. 🔍 Browse our collection of premium vehicles")
    st.write("2. 📅 Choose your dates and pickup/dropoff locations") 
    st.write("3. 🔒 Book securely through the app and get your digital car key")
    st.write("4. 🏎️ Unlock your car with the app and enjoy your luxurious ride!")
    
    # Call-to-action buttons
    st.markdown("""
        <div style="display: flex; justify-content: center; gap: 20px;">
            <a href="/browse" class="cta-button">Browse Cars</a>
            <a href="/list" class="cta-button">List Your Car</a>
        </div>
    """, unsafe_allow_html=True)
    
def browse_cars_page():
    st.title("Browse Our Premium Collection")
    
    # Search form
    with st.form("search_form"):
        pickup_location = st.text_input("Pickup Location")
        pickup_date = st.date_input("Pickup Date", value=datetime.now().date())
        dropoff_date = st.date_input("Dropoff Date", value=datetime.now().date() + timedelta(days=1))
        vehicle_type = st.selectbox("Vehicle Type", ['All', 'Sedan', 'SUV', 'Sports', 'Luxury'])
        search = st.form_submit_button("Search")

    # Fetch matching cars from database
    cars = get_cars(pickup_location, pickup_date, dropoff_date, vehicle_type)
    
    # Display cars
    for car in cars:
        with st.expander(f"{car['make']} {car['model']} ({car['year']})"):
            col1, col2 = st.columns(2)
            with col1:
                st.image(car['image'], use_column_width=True)
            with col2:    
                st.write(f"**Price:** ${car['price']}/day")
                st.write(f"**Location:** {car['location']}")
                st.write(car['description'])
                
                if st.button("Book Now", key=f"book_{car['id']}"):
                    st.session_state.selected_car = car
                    st.session_state.pickup_date = pickup_date
                    st.session_state.dropoff_date = dropoff_date
                    st.session_state.pickup_location = pickup_location
                    st.experimental_rerun()
                    
def list_car_page():
    st.title("List Your Car on LuxeRides")
    
    # Car details form
    with st.form("car_form"):
        make = st.text_input("Make")
        model = st.text_input("Model")
        year = st.number_input("Year", min_value=1900, max_value=datetime.now().year)
        price = st.number_input("Daily Price ($)", min_value=1)
        vehicle_type = st.selectbox("Type", ["Sedan", "SUV", "Sports", "Luxury"])
        color = st.color_picker("Color")
        location = st.text_input("Location")
        description = st.text_area("Description")
        image = st.file_uploader("Image", type=['jpg', 'jpeg', 'png'])
        
        submit = st.form_submit_button("List Car")
        
        if submit:
            if image:
                image_data = save_uploaded_image(image) 
                
                conn = sqlite3.connect('luxerides.db')
                c = conn.cursor()
                c.execute('''
                    INSERT INTO car_listings (owner_email, make, model, year, color, price, location, description, image_data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    st.session_state.user_email, make, model, year, color, price, location, description, image_data, datetime.now()  
                ))
                conn.commit()
                conn.close()
                
                st.success("Your car has been listed successfully!")
            else:
                st.error("Please upload an image of your car.")
                
def your_trips_page():
    st.title("Your Trips")
    
    trips = get_user_trips(st.session_state.user_email)
    
    if trips:
        for trip in trips:
            car = get_car(trip['car_id'])
            with st.expander(f"Trip to {trip['dropoff_location']} ({trip['pickup_date']} - {trip['return_date']})"):
                st.write(f"**Car:** {car['make']} {car['model']} ({car['year']})")  
                st.write(f"**Pickup Location:** {trip['pickup_location']}")
                st.write(f"**Dropoff Location:** {trip['dropoff_location']}")
                st.write(f"**Total Price:** ${trip['price']}")
                st.write(f"**Status:** {trip['status']}")
                
                # Check-in button 
                if trip['status'] == 'upcoming' and st.button("Check In", key=f"checkin_{trip['id']}"):
                    # Redirect to check-in page
                    st.session_state.trip_id = trip['id']
                    st.experimental_rerun()
                
    else:
        st.info("You don't have any trips yet. Book a car to get started!")
        
def your_listings_page():
    st.title("Your Car Listings")
    
    listings = get_user_listings(st.session_state.user_email)
    
    if listings:
        for listing in listings:
            with st.expander(f"{listing['make']} {listing['model']} ({listing['year']})"):
                st.write(f"**Daily Price:** ${listing['price']}")
                st.write(f"**Location:** {listing['location']}")
                st.write(f"**Description:** {listing['description']}")
                
                # Listing analytics
                bookings = get_listing_bookings(listing['id'])
                total_earnings = sum(booking['price'] for booking in bookings) 
                st.write(f"**Total Bookings:** {len(bookings)}")
                st.write(f"**Total Earnings:** ${total_earnings}")
                
                # Edit and delete buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Edit", key=f"edit_{listing['id']}"):
                        st.session_state.listing_to_edit = listing
                        st.experimental_rerun()
                        
                with col2:
                    if st.button("Delete", key=f"delete_{listing['id']}"):
                        conn = sqlite3.connect('luxerides.db')
                        c = conn.cursor()
                        c.execute('DELETE FROM car_listings WHERE id = ?', (listing['id'],))
                        conn.commit()
                        conn.close()
                        
                        st.experimental_rerun()
  
    else:
        st.info("You haven't listed any cars yet. List a car to start earning!")

    if st.button("+ List a New Car"):
        st.experimental_rerun()
        st.session_state.current_page = 'list_car'


# Advanced features
def check_in_page():
    st.title("Check-In")
    
    trip = get_trip(st.session_state.trip_id)
    car = get_car(trip['car_id'])
    
    st.write(f"**Car:** {car['make']} {car['model']} ({car['year']})")
    st.write(f"**Pickup Location:** {trip['pickup_location']}")
    
    qr_code = generate_checkin_qr(trip['id']) 
    st.image(qr_code, width=200)
    
    unlock_code = generate_unlock_code(trip['id'])
    st.write(f"**Unlock Code:** {unlock_code}")
    
    if st.button("📤 Send Unlock Code", key="send_code"):
        send_sms(f"+1{trip['renter_phone']}", f"Your LuxeRides unlock code is: {unlock_code}. Enjoy your trip!")
        st.success("Unlock code sent!")
        
    st.subheader("Vehicle Condition Check")
    st.write("Please take photos of any pre-existing damage and upload them below.")
    damage_images = st.file_uploader("Upload Damage Photos", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
    
    if damage_images:
        for image in damage_images:
            img = Image.open(image)
            damage_assessment = detect_damage(img)
            
            col1, col2 = st.columns(2)
            with col1:
                st.image(img, caption=image.name, use_column_width=True)
            with col2:
                st.write(f"**Damage Assessment:** {damage_assessment}")
                if damage_assessment == 'damage':
                    st.warning("Potential damage detected. Please review with the owner.")
                    
def virtual_assistant():
    st.title("Meet Luna, Your Virtual Car Assistant")
    
    luna_image = Image.open("luna.jpg")
    st.image(luna_image, width=200)
    
    st.write("Hi there! I'm Luna, your friendly AI assistant. How can I help you today?")
    
    query = st.text_input("Ask Luna a question")
    
    if query:
        response = generate_response(query) 
        st.write(f"**Luna:** {response}")
        
        if 'booking' in query.lower() or 'reservation' in query.lower():
            st.write("Here are your upcoming bookings:")
            trips = get_user_trips(st.session_state.user_email, upcoming_only=True)
            for trip in trips:
                st.write(f"- {trip['pickup_date']} to {trip['return_date']}: {trip['car_make']} {trip['car_model']}")

        elif 'weather' in query.lower() or 'forecast' in query.lower():
            st.write("Here's the weather forecast for your next trip:")
            trip = get_user_next_trip(st.session_state.user_email)
            if trip:
                weather = get_weather(trip['pickup_location'], trip['pickup_date'])
                st.write(weather)
            else:
                st.write("You don't have any upcoming trips. Book a car to get a weather forecast!")
                
        elif 'recommend' in query.lower() or 'suggestion' in query.lower():
            st.write("Based on your rental history, here are some cars you might like:")
            recommendations = get_user_recommendations(st.session_state.user_email)
            for car in recommendations:
                st.write(f"- {car['make']} {car['model']} ({car['year']}): {car['price']}/day")
                
        st.write("Let me know if you need anything else!")


# App routing logic        
def app():
    # Setup page
    st.set_page_config(page_title="LuxeRides", page_icon="🚗", layout="wide")
    
    # Initialize session state
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    
    # Get current page from URL    
    query_params = st.experimental_get_query_params()
    if 'page' in query_params:
        st.session_state.current_page = query_params['page'][0]
    
    # Render appropriate page based on session state
    if st.session_state.current_page == 'home':
        home_page()
    elif st.session_state.current_page == 'login':
        login_page()
    elif st.session_state.current_page == 'register':  
        register_page()
    elif st.session_state.current_page == 'profile':
        profile_page()
    elif st.session_state.current_page == 'browse':
        browse_cars_page()
    elif st.session_state.current_page == 'list':
        list_car_page()  
    elif st.session_state.current_page == 'trips':
        your_trips_page()
    elif st.session_state.current_page == 'listings':
        your_listings_page()
    elif st.session_state.current_page == 'checkin':
        check_in_page()
    elif st.session_state.current_page == 'assistant':
        virtual_assistant()
        
    # Show sidebar 
    nav_sidebar()
    
if __name__ == "__main__":
    app()
