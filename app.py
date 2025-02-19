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
    except Exception as e:
        st.error(f"Failed to send SMS: {str(e)}")

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
            try:
                c.execute('INSERT INTO users (name, email, phone, password, created_at) VALUES (?, ?, ?, ?, ?)', 
                          (name, email, phone, hash_password(password), datetime.now()))
                conn.commit() 
                st.success("Account created successfully! You can now login.")
                time.sleep(2)
                st.session_state.current_page = 'login'
                st.experimental_rerun()
            except sqlite3.IntegrityError:
                st.error("An account with this email already exists.")
            finally:
                conn.close()
        else:
            st.error("Passwords do not match")


def profile_page():
    st.title(f"Welcome, {st.session_state.user_email}! 👋")

    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()

    # Fetch user details  
    c.execute('SELECT * FROM users WHERE email = ?', (st.session_state.user_email,))
    user_info = c.fetchone()

    if user_info:
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
                try:
                    if profile_pic:
                        profile_pic = save_uploaded_image(profile_pic) 
                        c.execute('UPDATE users SET name = ?, phone = ?, profile_pic = ? WHERE email = ?',
                                  (name, phone, profile_pic, st.session_state.user_email))
                    else:  
                        c.execute('UPDATE users SET name = ?, phone = ? WHERE email = ?',
                                  (name, phone, st.session_state.user_email))
                        
                    conn.commit()
                    st.success("Profile updated successfully!")
                except Exception as e:
                    st.error(f"An error occurred while updating your profile: {str(e)}")
    else:
        st.error("User information not found. Please try logging in again.")

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
    if cars:
        display_car_carousel(cars)
    else:
        st.info("No featured cars available at the moment. Check back soon!")
    
    # How it works section
    st.subheader("How LuxeRides Works")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 1. Browse 🔍")
        st.write("Explore our collection of premium vehicles")
    
    with col2:
        st.markdown("### 2. Book 📅")
        st.write("Choose your dates and pickup/dropoff locations")
    
    with col3:
        st.markdown("### 3. Confirm 🔒")
        st.write("Securely book through the app and get your digital car key")
    
    with col4:
        st.markdown("### 4. Enjoy 🏎️")
        st.write("Unlock your car with the app and enjoy your luxurious ride!")
    
    # Call-to-action buttons
    st.markdown("""
        <div style="display: flex; justify-content: center; gap: 20px; margin-top: 30px;">
            <a href="/browse" class="cta-button">Browse Cars</a>
            <a href="/list" class="cta-button">List Your Car</a>
        </div>
    """, unsafe_allow_html=True)
    
    # Testimonials
    st.subheader("What Our Customers Say")
    testimonials = get_testimonials()
    if testimonials:
        for testimonial in testimonials:
            st.markdown(f"""
                > "{testimonial['text']}"
                >
                > — {testimonial['name']}
            """)
    else:
        st.info("Be the first to share your LuxeRides experience!")
    
    # Footer
    st.markdown("""
        ---
        © 2025 LuxeRides. All rights reserved. | [Terms of Service](/terms) | [Privacy Policy](/privacy)
    """)

def get_featured_cars():
    # This function should fetch featured cars from the database
    # For now, we'll return a placeholder
    return [
        {"id": 1, "make": "Tesla", "model": "Model S", "year": 2025, "price": 150},
        {"id": 2, "make": "Porsche", "model": "911", "year": 2024, "price": 200},
        {"id": 3, "make": "Range Rover", "model": "Evoque", "year": 2025, "price": 180}
    ]

def display_car_carousel(cars):
    # This function should display a carousel of featured cars
    # For now, we'll just list them
    for car in cars:
        st.write(f"{car['make']} {car['model']} ({car['year']}) - ${car['price']}/day")

def get_testimonials():
    # This function should fetch testimonials from the database
    # For now, we'll return placeholders
    return [
        {"name": "John D.", "text": "LuxeRides made my anniversary weekend unforgettable. The Tesla Model S was a dream to drive!"},
        {"name": "Sarah M.", "text": "Renting a Porsche 911 for my business trip was a game-changer. I arrived at meetings in style and comfort."}
    ]

def browse_cars_page():
    st.title("Browse Our Premium Collection")
    
    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        with col1:
            pickup_location = st.text_input("Pickup Location")
            pickup_date = st.date_input("Pickup Date", value=datetime.now().date())
        with col2:
            dropoff_location = st.text_input("Dropoff Location")
            dropoff_date = st.date_input("Dropoff Date", value=datetime.now().date() + timedelta(days=1))
        
        col3, col4, col5 = st.columns(3)
        with col3:
            vehicle_type = st.selectbox("Vehicle Type", ['All', 'Sedan', 'SUV', 'Sports', 'Luxury'])
        with col4:
            min_price = st.number_input("Min Price", min_value=0, value=0)
        with col5:
            max_price = st.number_input("Max Price", min_value=0, value=1000)
        
        search = st.form_submit_button("Search")

    if search:
        # Fetch matching cars from database
        cars = get_cars(pickup_location, dropoff_location, pickup_date, dropoff_date, vehicle_type, min_price, max_price)
        
        if cars:
            st.subheader(f"Found {len(cars)} matching vehicles")
            # Display cars
            for car in cars:
                with st.expander(f"{car['make']} {car['model']} ({car['year']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        if car['image']:
                            st.image(car['image'], use_column_width=True)
                        else:
                            st.image("placeholder_car.jpg", use_column_width=True)
                    with col2:    
                        st.write(f"**Price:** ${car['price']}/day")
                        st.write(f"**Location:** {car['location']}")
                        st.write(f"**Vehicle Type:** {car['vehicle_type']}")
                        st.write(car['description'])
                        
                        if st.button("Book Now", key=f"book_{car['id']}"):
                            if st.session_state.logged_in:
                                st.session_state.selected_car = car
                                st.session_state.pickup_date = pickup_date
                                st.session_state.dropoff_date = dropoff_date
                                st.session_state.pickup_location = pickup_location
                                st.session_state.dropoff_location = dropoff_location
                                st.experimental_rerun()
                            else:
                                st.warning("Please log in to book a car.")
        else:
            st.info("No cars found matching your criteria. Try adjusting your search parameters.")

def get_cars(pickup_location, dropoff_location, pickup_date, dropoff_date, vehicle_type, min_price, max_price):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    
    query = '''
    SELECT * FROM car_listings
    WHERE location LIKE ? 
    AND price BETWEEN ? AND ?
    '''
    params = [f'%{pickup_location}%', min_price, max_price]
    
    if vehicle_type != 'All':
        query += ' AND vehicle_type = ?'
        params.append(vehicle_type)
    
    c.execute(query, params)
    cars = c.fetchall()
    
    conn.close()
    
    # Convert to list of dictionaries
    car_list = []
    for car in cars:
        car_dict = {
            'id': car[0],
            'make': car[3],
            'model': car[4],
            'year': car[5],
            'color': car[6],
            'price': car[7],
            'location': car[8],
            'description': car[11],
            'image': car[13],
            'vehicle_type': car[2]
        }
        car_list.append(car_dict)
    
    return car_list



def list_car_page():
    st.title("List Your Car on LuxeRides")
    
    if not st.session_state.logged_in:
        st.warning("Please log in to list your car.")
        return

    # Car details form
    with st.form("car_form"):
        col1, col2 = st.columns(2)
        with col1:
            make = st.text_input("Make")
            model = st.text_input("Model")
            year = st.number_input("Year", min_value=1900, max_value=datetime.now().year)
            color = st.color_picker("Color")
        with col2:
            vehicle_type = st.selectbox("Type", ["Sedan", "SUV", "Sports", "Luxury"])
            price = st.number_input("Daily Price ($)", min_value=1)
            location = st.text_input("Location")
        
        description = st.text_area("Description")
        image = st.file_uploader("Car Image", type=['jpg', 'jpeg', 'png'])
        
        submit = st.form_submit_button("List Car")
        
        if submit:
            if not all([make, model, year, color, vehicle_type, price, location, description]):
                st.error("Please fill in all fields.")
            elif not image:
                st.error("Please upload an image of your car.")
            else:
                try:
                    image_data = save_uploaded_image(image)
                    
                    conn = sqlite3.connect('luxerides.db')
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO car_listings 
                        (owner_email, vehicle_type, make, model, year, color, price, location, description, image_data, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        st.session_state.user_email, vehicle_type, make, model, year, color, price, location, 
                        description, image_data, datetime.now()
                    ))
                    conn.commit()
                    conn.close()
                    
                    st.success("Your car has been listed successfully!")
                    time.sleep(2)
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"An error occurred while listing your car: {str(e)}")

def save_uploaded_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        img = img.resize((800, 600))  # Resize image for consistency
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        byte_im = buf.getvalue()
        return byte_im
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None




def your_trips_page():
    st.title("Your Trips")
    
    if not st.session_state.logged_in:
        st.warning("Please log in to view your trips.")
        return
    
    trips = get_user_trips(st.session_state.user_email)
    
    if trips:
        for trip in trips:
            with st.expander(f"Trip to {trip['dropoff_location']} ({trip['pickup_date']} - {trip['return_date']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Car:** {trip['car_make']} {trip['car_model']} ({trip['car_year']})")  
                    st.write(f"**Pickup Location:** {trip['pickup_location']}")
                    st.write(f"**Dropoff Location:** {trip['dropoff_location']}")
                with col2:
                    st.write(f"**Total Price:** ${trip['price']}")
                    st.write(f"**Status:** {trip['booking_status']}")
                
                # Check-in button 
                if trip['booking_status'] == 'upcoming' and st.button("Check In", key=f"checkin_{trip['booking_id']}"):
                    st.session_state.trip_id = trip['booking_id']
                    st.experimental_rerun()
                
                # Cancel button
                if trip['booking_status'] == 'upcoming' and st.button("Cancel Trip", key=f"cancel_{trip['booking_id']}"):
                    if cancel_trip(trip['booking_id']):
                        st.success("Trip cancelled successfully.")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to cancel the trip. Please try again.")
    else:
        st.info("You don't have any trips yet. Book a car to get started!")

def your_listings_page():
    st.title("Your Car Listings")
    
    if not st.session_state.logged_in:
        st.warning("Please log in to view your listings.")
        return
    
    listings = get_user_listings(st.session_state.user_email)
    
    if listings:
        for listing in listings:
            with st.expander(f"{listing['make']} {listing['model']} ({listing['year']})"):
                col1, col2 = st.columns(2)
                with col1:
                    if listing['image_data']:
                        st.image(listing['image_data'], use_column_width=True)
                    else:
                        st.image("placeholder_car.jpg", use_column_width=True)
                with col2:
                    st.write(f"**Daily Price:** ${listing['price']}")
                    st.write(f"**Location:** {listing['location']}")
                    st.write(f"**Vehicle Type:** {listing['vehicle_type']}")
                    st.write(f"**Description:** {listing['description']}")
                
                # Listing analytics
                bookings = get_listing_bookings(listing['listing_id'])
                total_earnings = sum(booking['price'] for booking in bookings) 
                st.write(f"**Total Bookings:** {len(bookings)}")
                st.write(f"**Total Earnings:** ${total_earnings}")
                
                # Edit and delete buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Edit", key=f"edit_{listing['listing_id']}"):
                        st.session_state.listing_to_edit = listing
                        st.experimental_rerun()
                        
                with col2:
                    if st.button("Delete", key=f"delete_{listing['listing_id']}"):
                        if delete_listing(listing['listing_id']):
                            st.success("Listing deleted successfully.")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to delete the listing. Please try again.")
  
    else:
        st.info("You haven't listed any cars yet. List a car to start earning!")

    if st.button("+ List a New Car"):
        st.session_state.current_page = 'list_car'
        st.experimental_rerun()

def get_user_trips(user_email):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    c.execute('''
        SELECT b.*, cl.make as car_make, cl.model as car_model, cl.year as car_year
        FROM bookings b
        JOIN car_listings cl ON b.car_id = cl.listing_id
        WHERE b.renter_email = ?
        ORDER BY b.pickup_date DESC
    ''', (user_email,))
    trips = c.fetchall()
    conn.close()
    
    return [dict(zip([column[0] for column in c.description], trip)) for trip in trips]

def get_user_listings(user_email):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    c.execute('SELECT * FROM car_listings WHERE owner_email = ?', (user_email,))
    listings = c.fetchall()
    conn.close()
    
    return [dict(zip([column[0] for column in c.description], listing)) for listing in listings]

def get_listing_bookings(listing_id):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    c.execute('SELECT * FROM bookings WHERE car_id = ?', (listing_id,))
    bookings = c.fetchall()
    conn.close()
    
    return [dict(zip([column[0] for column in c.description], booking)) for booking in bookings]

def cancel_trip(booking_id):
    try:
        conn = sqlite3.connect('luxerides.db')
        c = conn.cursor()
        c.execute('UPDATE bookings SET booking_status = "cancelled" WHERE booking_id = ?', (booking_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error cancelling trip: {str(e)}")
        return False

def delete_listing(listing_id):
    try:
        conn = sqlite3.connect('luxerides.db')
        c = conn.cursor()
        
        # First, check if there are any active bookings for this listing
        c.execute('''
            SELECT COUNT(*) FROM bookings 
            WHERE car_id = ? AND booking_status IN ('upcoming', 'ongoing')
        ''', (listing_id,))
        active_bookings = c.fetchone()[0]
        
        if active_bookings > 0:
            conn.close()
            return False, "Cannot delete listing with active bookings."
        
        # If no active bookings, proceed with deletion
        c.execute('DELETE FROM car_listings WHERE listing_id = ?', (listing_id,))
        
        # Also delete any past bookings associated with this listing
        c.execute('DELETE FROM bookings WHERE car_id = ?', (listing_id,))
        
        conn.commit()
        conn.close()
        return True, "Listing deleted successfully."
    except Exception as e:
        print(f"Error deleting listing: {str(e)}")
        return False, f"An error occurred: {str(e)}"

# Update the your_listings_page function to use the new return values
def your_listings_page():
    st.title("Your Car Listings")
    
    if not st.session_state.logged_in:
        st.warning("Please log in to view your listings.")
        return
    
    listings = get_user_listings(st.session_state.user_email)
    
    if listings:
        for listing in listings:
            with st.expander(f"{listing['make']} {listing['model']} ({listing['year']})"):
                col1, col2 = st.columns(2)
                with col1:
                    if listing['image_data']:
                        st.image(listing['image_data'], use_column_width=True)
                    else:
                        st.image("placeholder_car.jpg", use_column_width=True)
                with col2:
                    st.write(f"**Daily Price:** ${listing['price']}")
                    st.write(f"**Location:** {listing['location']}")
                    st.write(f"**Vehicle Type:** {listing['vehicle_type']}")
                    st.write(f"**Description:** {listing['description']}")
                
                # Listing analytics
                bookings = get_listing_bookings(listing['listing_id'])
                total_earnings = sum(booking['price'] for booking in bookings) 
                st.write(f"**Total Bookings:** {len(bookings)}")
                st.write(f"**Total Earnings:** ${total_earnings}")
                
                # Edit and delete buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Edit", key=f"edit_{listing['listing_id']}"):
                        st.session_state.listing_to_edit = listing
                        st.experimental_rerun()
                        
                with col2:
                    if st.button("Delete", key=f"delete_{listing['listing_id']}"):
                        success, message = delete_listing(listing['listing_id'])
                        if success:
                            st.success(message)
                            st.experimental_rerun()
                        else:
                            st.error(message)
  
    else:
        st.info("You haven't listed any cars yet. List a car to start earning!")

    if st.button("+ List a New Car"):
        st.session_state.current_page = 'list_car'
        st.experimental_rerun()

 

def check_in_page():
    st.title("Check-In")
    
    if 'trip_id' not in st.session_state:
        st.error("No trip selected for check-in.")
        return
    
    trip = get_trip(st.session_state.trip_id)
    if not trip:
        st.error("Trip not found.")
        return
    
    car = get_car(trip['car_id'])
    
    st.write(f"**Car:** {car['make']} {car['model']} ({car['year']})")
    st.write(f"**Pickup Location:** {trip['pickup_location']}")
    st.write(f"**Pickup Date:** {trip['pickup_date']}")
    st.write(f"**Return Date:** {trip['return_date']}")
    
    # Generate QR code for check-in
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"CHECKIN-{trip['booking_id']}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert PIL image to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # Display QR code
    st.image(img_byte_arr, caption="Scan this QR code at the pickup location", width=300)
    
    unlock_code = generate_unlock_code(trip['booking_id'])
    st.write(f"**Unlock Code:** {unlock_code}")
    
    if st.button("📤 Send Unlock Code", key="send_code"):
        success = send_sms(trip['renter_phone'], f"Your LuxeRides unlock code is: {unlock_code}. Enjoy your trip!")
        if success:
            st.success("Unlock code sent!")
        else:
            st.error("Failed to send unlock code. Please try again.")
        
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
    
    if st.button("Complete Check-In"):
        # Update trip status to 'ongoing'
        update_trip_status(trip['booking_id'], 'ongoing')
        st.success("Check-in completed successfully. Enjoy your trip!")
        time.sleep(2)
        st.session_state.pop('trip_id')
        st.experimental_rerun()

def get_trip(trip_id):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    c.execute('SELECT * FROM bookings WHERE booking_id = ?', (trip_id,))
    trip = c.fetchone()
    conn.close()
    
    if trip:
        return dict(zip([column[0] for column in c.description], trip))
    return None

def get_car(car_id):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    c.execute('SELECT * FROM car_listings WHERE listing_id = ?', (car_id,))
    car = c.fetchone()
    conn.close()
    
    if car:
        return dict(zip([column[0] for column in c.description], car))
    return None

def generate_unlock_code(booking_id):
    # Generate a simple 6-digit code based on the booking ID
    return f"{booking_id:06d}"

def update_trip_status(booking_id, status):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    c.execute('UPDATE bookings SET booking_status = ? WHERE booking_id = ?', (status, booking_id))
    conn.commit()
    conn.close()




def virtual_assistant():
    st.title("Meet Luna, Your Virtual Car Assistant")
    
    # Display Luna's avatar
    luna_image = Image.open("luna_avatar.png")
    st.image(luna_image, width=200)
    
    st.write("Hi there! I'm Luna, your friendly AI assistant. How can I help you today?")
    
    query = st.text_input("Ask Luna a question")
    
    if query:
        response = generate_response(query)
        st.write(f"**Luna:** {response}")
        
        if 'booking' in query.lower() or 'reservation' in query.lower():
            st.write("Here are your upcoming bookings:")
            trips = get_user_trips(st.session_state.user_email, upcoming_only=True)
            if trips:
                for trip in trips:
                    st.write(f"- {trip['pickup_date']} to {trip['return_date']}: {trip['car_make']} {trip['car_model']}")
            else:
                st.write("You don't have any upcoming bookings at the moment.")

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
            if recommendations:
                for car in recommendations:
                    st.write(f"- {car['make']} {car['model']} ({car['year']}): ${car['price']}/day")
            else:
                st.write("I don't have enough data to make personalized recommendations yet. Try renting a few cars first!")
                
        st.write("Is there anything else I can help you with?")

def generate_response(query):
    # This is a placeholder for a more sophisticated NLP model
    responses = [
        "I understand you're asking about {}. Let me help you with that.",
        "Regarding {}, I have some information that might be useful.",
        "I'd be happy to assist you with {}. Here's what I know.",
        "Let me see what I can find about {}.",
        "I've got some details about {} that might interest you."
    ]
    return random.choice(responses).format(query.lower())

def get_user_trips(user_email, upcoming_only=False):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    
    query = '''
        SELECT b.*, cl.make as car_make, cl.model as car_model
        FROM bookings b
        JOIN car_listings cl ON b.car_id = cl.listing_id
        WHERE b.renter_email = ?
    '''
    
    if upcoming_only:
        query += " AND b.pickup_date >= DATE('now')"
    
    query += " ORDER BY b.pickup_date ASC"
    
    c.execute(query, (user_email,))
    trips = c.fetchall()
    conn.close()
    
    return [dict(zip([column[0] for column in c.description], trip)) for trip in trips]

def get_user_next_trip(user_email):
    trips = get_user_trips(user_email, upcoming_only=True)
    return trips[0] if trips else None

def get_weather(location, date):
    # This is a placeholder for an actual weather API call
    weather_conditions = ["sunny", "partly cloudy", "cloudy", "rainy", "stormy"]
    temperatures = range(60, 90)
    return f"The weather in {location} on {date} is expected to be {random.choice(weather_conditions)} with a temperature of {random.choice(temperatures)}°F."

def get_user_recommendations(user_email):
    # This is a placeholder for a more sophisticated recommendation system
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    c.execute('''
        SELECT DISTINCT cl.*
        FROM car_listings cl
        JOIN bookings b ON cl.listing_id = b.car_id
        WHERE b.renter_email = ?
        ORDER BY RANDOM()
        LIMIT 3
    ''', (user_email,))
    recommendations = c.fetchall()
    conn.close()
    
    return [dict(zip([column[0] for column in c.description], car)) for car in recommendations]


def setup_review_table():
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY,
            booking_id INTEGER,
            reviewer_email TEXT,
            reviewee_email TEXT,
            car_id INTEGER,
            rating INTEGER,
            review_text TEXT,
            review_response TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY(booking_id) REFERENCES bookings(booking_id),
            FOREIGN KEY(reviewer_email) REFERENCES users(email),
            FOREIGN KEY(reviewee_email) REFERENCES users(email),
            FOREIGN KEY(car_id) REFERENCES car_listings(listing_id)
        )
    ''')
    conn.commit()
    conn.close()

def add_review(booking_id, reviewer_email, reviewee_email, car_id, rating, review_text):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO reviews (booking_id, reviewer_email, reviewee_email, car_id, rating, review_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (booking_id, reviewer_email, reviewee_email, car_id, rating, review_text, datetime.now()))
    conn.commit()
    conn.close()

def get_car_reviews(car_id):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    c.execute('''
        SELECT r.*, u.name as reviewer_name
        FROM reviews r
        JOIN users u ON r.reviewer_email = u.email
        WHERE r.car_id = ?
        ORDER BY r.created_at DESC
    ''', (car_id,))
    reviews = c.fetchall()
    conn.close()
    return [dict(zip([column[0] for column in c.description], review)) for review in reviews]

def add_review_response(review_id, response_text):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    c.execute('UPDATE reviews SET review_response = ? WHERE review_id = ?', (response_text, review_id))
    conn.commit()
    conn.close()

def review_page():
    st.title("Leave a Review")

    if not st.session_state.logged_in:
        st.warning("Please log in to leave a review.")
        return

    # Get user's completed trips
    completed_trips = get_user_completed_trips(st.session_state.user_email)

    if not completed_trips:
        st.info("You don't have any completed trips to review yet.")
        return

    # Select a trip to review
    selected_trip = st.selectbox("Select a trip to review", 
                                 options=completed_trips,
                                 format_func=lambda x: f"{x['car_make']} {x['car_model']} - {x['return_date']}")

    # Review form
    with st.form("review_form"):
        rating = st.slider("Rating", 1, 5, 5)
        review_text = st.text_area("Your Review")
        submit_button = st.form_submit_button("Submit Review")

        if submit_button:
            if not review_text:
                st.error("Please write a review before submitting.")
            else:
                add_review(selected_trip['booking_id'], 
                           st.session_state.user_email,
                           selected_trip['owner_email'],
                           selected_trip['car_id'],
                           rating,
                           review_text)
                st.success("Thank you for your review!")

def get_user_completed_trips(user_email):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    c.execute('''
        SELECT b.*, cl.make as car_make, cl.model as car_model, u.email as owner_email
        FROM bookings b
        JOIN car_listings cl ON b.car_id = cl.listing_id
        JOIN users u ON cl.owner_email = u.email
        WHERE b.renter_email = ? AND b.booking_status = 'completed'
        AND b.booking_id NOT IN (SELECT booking_id FROM reviews WHERE reviewer_email = ?)
        ORDER BY b.return_date DESC
    ''', (user_email, user_email))
    trips = c.fetchall()
    conn.close()
    return [dict(zip([column[0] for column in c.description], trip)) for trip in trips]

def display_car_reviews(car_id):
    reviews = get_car_reviews(car_id)
    
    if not reviews:
        st.info("This car doesn't have any reviews yet.")
        return

    for review in reviews:
        with st.expander(f"{review['reviewer_name']} - {review['created_at']}"):
            st.write(f"**Rating:** {'⭐' * review['rating']}")
            st.write(review['review_text'])
            if review['review_response']:
                st.write("**Owner's Response:**")
                st.write(review['review_response'])

 
def advanced_search_page():
    st.title("Find Your Perfect Ride")

    with st.form("advanced_search_form"):
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input("Location")
            pickup_date = st.date_input("Pickup Date", value=datetime.now().date())
            min_price = st.number_input("Min Price per Day", min_value=0, value=0)
        with col2:
            vehicle_type = st.multiselect("Vehicle Type", ["Sedan", "SUV", "Sports", "Luxury"])
            dropoff_date = st.date_input("Dropoff Date", value=datetime.now().date() + timedelta(days=1))
            max_price = st.number_input("Max Price per Day", min_value=0, value=1000)
        
        col3, col4 = st.columns(2)
        with col3:
            min_year = st.number_input("Min Year", min_value=1900, value=2000)
            min_rating = st.slider("Minimum Rating", 1, 5, 1)
        with col4:
            max_year = st.number_input("Max Year", min_value=1900, value=datetime.now().year)
            features = st.multiselect("Features", ["GPS", "Bluetooth", "Backup Camera", "Sunroof"])

        search_button = st.form_submit_button("Search")

    if search_button:
        search_results = search_cars(location, pickup_date, dropoff_date, vehicle_type, 
                                     min_price, max_price, min_year, max_year, min_rating, features)
        display_search_results(search_results)

def search_cars(location, pickup_date, dropoff_date, vehicle_type, min_price, max_price, 
                min_year, max_year, min_rating, features):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()

    query = '''
    SELECT cl.*, AVG(r.rating) as avg_rating
    FROM car_listings cl
    LEFT JOIN reviews r ON cl.listing_id = r.car_id
    WHERE cl.location LIKE ?
    AND cl.price BETWEEN ? AND ?
    AND cl.year BETWEEN ? AND ?
    '''
    params = [f'%{location}%', min_price, max_price, min_year, max_year]

    if vehicle_type:
        query += ' AND cl.vehicle_type IN ({})'.format(','.join(['?']*len(vehicle_type)))
        params.extend(vehicle_type)

    if features:
        for feature in features:
            query += f' AND cl.added_features LIKE ?'
            params.append(f'%{feature}%')

    query += ' GROUP BY cl.listing_id HAVING avg_rating >= ?'
    params.append(min_rating)

    query += ' ORDER BY avg_rating DESC'

    c.execute(query, params)
    results = c.fetchall()
    conn.close()

    return [dict(zip([column[0] for column in c.description], row)) for row in results]

def display_search_results(results):
    if not results:
        st.info("No cars found matching your criteria. Try adjusting your search parameters.")
        return

    st.subheader(f"Found {len(results)} matching vehicles")
    for car in results:
        with st.expander(f"{car['make']} {car['model']} ({car['year']}) - ${car['price']}/day"):
            col1, col2 = st.columns(2)
            with col1:
                if car['image_data']:
                    st.image(car['image_data'], use_column_width=True)
                else:
                    st.image("placeholder_car.jpg", use_column_width=True)
            with col2:
                st.write(f"**Location:** {car['location']}")
                st.write(f"**Vehicle Type:** {car['vehicle_type']}")
                st.write(f"**Average Rating:** {'⭐' * int(car['avg_rating'])} ({car['avg_rating']:.1f})")
                st.write(f"**Description:** {car['description']}")
                if car['added_features']:
                    st.write(f"**Features:** {car['added_features']}")
                
                if st.button("View Details", key=f"view_{car['listing_id']}"):
                    st.session_state.current_page = 'car_details'
                    st.session_state.selected_car_id = car['listing_id']
                    st.experimental_rerun()

def car_details_page(car_id):
    car = get_car_details(car_id)
    if not car:
        st.error("Car not found.")
        return

    st.title(f"{car['make']} {car['model']} ({car['year']})")
    
    col1, col2 = st.columns(2)
    with col1:
        if car['image_data']:
            st.image(car['image_data'], use_column_width=True)
        else:
            st.image("placeholder_car.jpg", use_column_width=True)
    with col2:
        st.write(f"**Price:** ${car['price']}/day")
        st.write(f"**Location:** {car['location']}")
        st.write(f"**Vehicle Type:** {car['vehicle_type']}")
        st.write(f"**Description:** {car['description']}")
        if car['added_features']:
            st.write(f"**Features:** {car['added_features']}")
        
        if st.button("Book Now"):
            if st.session_state.logged_in:
                st.session_state.current_page = 'booking'
                st.session_state.selected_car = car
                st.experimental_rerun()
            else:
                st.warning("Please log in to book a car.")

    st.subheader("Reviews")
    display_car_reviews(car_id)

def get_car_details(car_id):
    conn = sqlite3.connect('luxerides.db')
    c = conn.cursor()
    c.execute('SELECT * FROM car_listings WHERE listing_id = ?', (car_id,))
    car = c.fetchone()
    conn.close()
    
    if car:
        return dict(zip([column[0] for column in c.description], car))
    return None

def app():
    # Setup
    setup_database()
    setup_review_table()
    setup_notification_table()

    # Check for notifications
    check_for_review_reminders()
    check_for_new_reviews()

    # Navigation
    page = nav_sidebar()

    # Routing
    if page == 'Home':
        home_page()
    elif page == 'Browse Cars':
        advanced_search_page()
    elif page == 'List Your Car':
        list_car_page()
    elif page == 'Your Trips':
        your_trips_page()
    elif page == 'Your Listings':
        your_listings_page()
    elif page == 'Profile':
        profile_page()
    elif page == 'Login':
        login_page()
    elif st.session_state.current_page == 'register':
        register_page()
    elif st.session_state.current_page == 'car_details':
        car_details_page(st.session_state.selected_car_id)
    elif st.session_state.current_page == 'booking':
        booking_page()
    elif st.session_state.current_page == 'review':
        review_page()
    elif st.session_state.current_page == 'notifications':
        notification_center()
    else:
        st.error("Page not found.")

if __name__ == "__main__":
    app()
