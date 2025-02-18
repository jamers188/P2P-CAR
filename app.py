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
import pickle

# Page config
st.set_page_config(
    page_title="Premium Car Rentals",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Logo and branding
LOGO_PATH = "logo.png"  # Place your logo in the same directory
if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, width=200)
else:
    st.title("🚗 Premium Car Rentals")

# Custom CSS with improved styling
st.markdown("""
    <style>
        /* Modern Theme Variables */
        :root {
            --primary-color: #1E88E5;
            --secondary-color: #005CB2;
            --accent-color: #FFC107;
            --background-color: #F5F7FA;
            --text-color: #2C3E50;
            --card-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        /* Global Styles */
        .stApp {
            background-color: var(--background-color);
            color: var(--text-color);
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }

        /* Modern Button Styling */
        .stButton>button {
            background-color: var(--primary-color);
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            border: none;
            box-shadow: var(--card-shadow);
            transition: all 0.3s ease;
            text-transform: none;
            font-weight: 500;
        }

        .stButton>button:hover {
            background-color: var(--secondary-color);
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }

        /* Card Styling */
        .modern-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: var(--card-shadow);
            transition: transform 0.3s ease;
        }

        .modern-card:hover {
            transform: translateY(-5px);
        }

        /* Form Input Styling */
        .stTextInput>div>div>input {
            border-radius: 8px;
            border: 2px solid #E0E7FF;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }

        .stTextInput>div>div>input:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 2px rgba(30,136,229,0.2);
        }

        /* Status Badges */
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
            display: inline-block;
        }

        .status-badge.available {
            background-color: #4CAF50;
            color: white;
        }

        .status-badge.pending {
            background-color: #FFC107;
            color: #000;
        }

        .status-badge.unavailable {
            background-color: #F44336;
            color: white;
        }

        /* Navigation Menu */
        .sidebar .sidebar-content {
            background-color: white;
            padding: 1rem;
        }

        /* Footer Styling */
        .footer {
            padding: 2rem 0;
            text-align: center;
            color: #666;
            border-top: 1px solid #eee;
            margin-top: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# Database path - Now using a permanent location
DB_PATH = os.path.join(os.path.expanduser('~'), '.car_rental.db')

# Initialize session state
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

def init_database():
    """Initialize the permanent database with all necessary tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Users table with extended profile information
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            driving_license TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            role TEXT DEFAULT 'user',
            account_status TEXT DEFAULT 'active'
        )
    ''')

    # Vehicles table with enhanced details
    c.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY,
            owner_id INTEGER,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            category TEXT NOT NULL,
            daily_rate REAL NOT NULL,
            location TEXT NOT NULL,
            status TEXT DEFAULT 'available',
            description TEXT,
            features TEXT,
            images TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
    ''')

    # Bookings table with comprehensive tracking
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            vehicle_id INTEGER,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_status TEXT DEFAULT 'pending',
            additional_services TEXT,
            pickup_location TEXT,
            return_location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        )
    ''')

    # Reviews and ratings
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            booking_id INTEGER,
            user_id INTEGER,
            vehicle_id INTEGER,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        )
    ''')

    # User sessions for persistence
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

# Initialize database if it doesn't exist
if not os.path.exists(DB_PATH):
    init_database()

def hash_password(password):
    """Create a secure hash of the password"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_session(user_id):
    """Create a new session for the user"""
    session_token = hashlib.sha256(os.urandom(24)).hexdigest()
    expires_at = datetime.now() + timedelta(days=30)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Remove any existing sessions for this user
    c.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
    
    # Create new session
    c.execute('''
        INSERT INTO sessions (user_id, session_token, expires_at)
        VALUES (?, ?, ?)
    ''', (user_id, session_token, expires_at))
    
    conn.commit()
    conn.close()
    
    return session_token
    
def verify_session(session_token):
    """Verify if a session is valid"""
    if not session_token:
        return None
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT user_id FROM sessions 
        WHERE session_token = ? AND expires_at > ?
    ''', (session_token, datetime.now()))
    
    result = c.fetchone()
    conn.close()
    
    return result[0] if result else None

def load_user_data():
    """Load user data from session"""
    if 'session_token' in st.session_state:
        user_id = verify_session(st.session_state.session_token)
        if user_id:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user_data = c.fetchone()
            conn.close()
            
            if user_data:
                st.session_state.user_data = {
                    'id': user_data[0],
                    'email': user_data[1],
                    'full_name': user_data[3],
                    'role': user_data[9]
                }
                return True
    
    st.session_state.user_data = None
    return False

def show_register_page():
    st.title("Create Account")
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
        
        with col2:
            phone = st.text_input("Phone Number")
            address = st.text_area("Address")
            driving_license = st.text_input("Driving License Number")
        
        agree_terms = st.checkbox("I agree to the Terms and Conditions")
        
        if st.form_submit_button("Register"):
            if not all([full_name, email, password, confirm_password, phone]):
                st.error("Please fill in all required fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif not agree_terms:
                st.error("Please agree to the Terms and Conditions")
            else:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                
                # Check if email already exists
                c.execute('SELECT id FROM users WHERE email = ?', (email,))
                if c.fetchone():
                    st.error("Email already registered")
                else:
                    try:
                        c.execute('''
                            INSERT INTO users 
                            (email, password, full_name, phone, address, driving_license)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (email, hash_password(password), full_name, phone, address, driving_license))
                        conn.commit()
                        st.success("Registration successful! Please login.")
                        st.session_state.page = "login"
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Registration failed: {str(e)}")
                    finally:
                        conn.close()

def show_browse_page():
    st.title("Available Vehicles")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        category = st.selectbox("Category", ["All", "Luxury", "Sports", "SUV", "Electric"])
    with col2:
        price_range = st.slider("Price Range (AED/day)", 0, 2000, (200, 1000))
    with col3:
        location = st.selectbox("Location", ["All", "Dubai Marina", "Downtown Dubai", "Palm Jumeirah"])
    with col4:
        sort_by = st.selectbox("Sort By", ["Price: Low to High", "Price: High to Low", "Newest First"])
    
    # Get vehicles from database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    query = '''
        SELECT v.*, u.full_name as owner_name 
        FROM vehicles v 
        JOIN users u ON v.owner_id = u.id 
        WHERE v.status = 'available'
    '''
    params = []
    
    if category != "All":
        query += " AND v.category = ?"
        params.append(category)
    if location != "All":
        query += " AND v.location = ?"
        params.append(location)
    
    query += f" AND v.daily_rate BETWEEN {price_range[0]} AND {price_range[1]}"
    
    if sort_by == "Price: Low to High":
        query += " ORDER BY v.daily_rate ASC"
    elif sort_by == "Price: High to Low":
        query += " ORDER BY v.daily_rate DESC"
    else:
        query += " ORDER BY v.created_at DESC"
    
    c.execute(query, params)
    vehicles = c.fetchall()
    conn.close()
    
    # Display vehicles
    for idx, vehicle in enumerate(vehicles):
        st.markdown(f"""
            <div class="modern-card">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h3>{vehicle[2]} {vehicle[3]} ({vehicle[4]})</h3>
                        <p class="status-badge available">Available</p>
                        <p><strong>AED {vehicle[6]}</strong>/day</p>
                        <p>{vehicle[8]}</p>
                        <p><small>Location: {vehicle[7]}</small></p>
                    </div>
                    {'<img src="data:image/jpeg;base64,' + vehicle[11].split(',')[0] + '" style="width:200px; border-radius:8px;">' if vehicle[11] else ''}
                </div>
            """, unsafe_allow_html=True)
        
        if st.button("Book Now", key=f"book_{vehicle[0]}"):
            st.session_state.selected_vehicle = vehicle[0]
            st.session_state.page = "booking"
            st.experimental_rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

def show_bookings_page():
    st.title("My Bookings")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get user's bookings with vehicle details
    c.execute('''
        SELECT b.*, v.make, v.model, v.year, v.daily_rate, v.images
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC
    ''', (st.session_state.user_data['id'],))
    
    bookings = c.fetchall()
    conn.close()
    
    if not bookings:
        st.info("You haven't made any bookings yet.")
        return
    
    for booking in bookings:
        st.markdown(f"""
            <div class="modern-card">
                <h3>{booking[11]} {booking[12]} ({booking[13]})</h3>
                <p class="status-badge {booking[6].lower()}">{booking[6].upper()}</p>
                <p><strong>Dates:</strong> {booking[3]} to {booking[4]}</p>
                <p><strong>Total Amount:</strong> AED {booking[5]}</p>
                <p><strong>Payment Status:</strong> {booking[7]}</p>
                {'<img src="data:image/jpeg;base64,' + booking[15].split(',')[0] + '" style="width:200px; border-radius:8px;">' if booking[15] else ''}
            </div>
        """, unsafe_allow_html=True)

def show_profile_page():
    st.title("My Profile")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (st.session_state.user_data['id'],))
    user = c.fetchone()
    conn.close()
    
    if not user:
        st.error("User data not found")
        return
    
    # Profile information
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Personal Information")
        full_name = st.text_input("Full Name", value=user[3])
        email = st.text_input("Email", value=user[1], disabled=True)
        phone = st.text_input("Phone", value=user[4] or "")
        
    with col2:
        st.markdown("### Additional Information")
        address = st.text_area("Address", value=user[5] or "")
        driving_license = st.text_input("Driving License", value=user[6] or "")
    
    if st.button("Update Profile"):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute('''
                UPDATE users 
                SET full_name = ?, phone = ?, address = ?, driving_license = ?
                WHERE id = ?
            ''', (full_name, phone, address, driving_license, user[0]))
            conn.commit()
            st.success("Profile updated successfully!")
        except Exception as e:
            st.error(f"Error updating profile: {str(e)}")
        finally:
            conn.close()
    
    # Change password section
    st.markdown("### Change Password")
    with st.form("change_password"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Change Password"):
            if not all([current_password, new_password, confirm_password]):
                st.error("Please fill in all password fields")
            elif new_password != confirm_password:
                st.error("New passwords do not match")
            elif hash_password(current_password) != user[2]:
                st.error("Current password is incorrect")
            else:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                try:
                    c.execute('UPDATE users SET password = ? WHERE id = ?',
                             (hash_password(new_password), user[0]))
                    conn.commit()
                    st.success("Password updated successfully!")
                except Exception as e:
                    st.error(f"Error updating password: {str(e)}")
                finally:
                    conn.close()

def show_admin_page():
    st.title("Admin Panel")
    
    tabs = st.tabs(["Users", "Vehicles", "Bookings", "Reports"])
    
    with tabs[0]:
        show_admin_users()
    with tabs[1]:
        show_admin_vehicles()
    with tabs[2]:
        show_admin_bookings()
    with tabs[3]:
        show_admin_reports()

def show_admin_users():
    st.subheader("User Management")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users ORDER BY created_at DESC')
    users = c.fetchall()
    conn.close()
    
    for user in users:
        with st.expander(f"{user[3]} ({user[1]})"):
            st.write(f"Role: {user[9]}")
            st.write(f"Status: {user[10]}")
            st.write(f"Created: {user[7]}")
            st.write(f"Last Login: {user[8]}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Toggle Status", key=f"toggle_{user[0]}"):
                    new_status = 'inactive' if user[10] == 'active' else 'active'
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute('UPDATE users SET account_status = ? WHERE id = ?',
                             (new_status, user[0]))
                    conn.commit()
                    conn.close()
                    st.experimental_rerun()
            with col2:
                if st.button("Make Admin", key=f"admin_{user[0]}"):
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute('UPDATE users SET role = ? WHERE id = ?',
                             ('admin', user[0]))
                    conn.commit()
                    conn.close()
                    st.experimental_rerun()

def show_admin_vehicles():
    st.subheader("Vehicle Management")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT v.*, u.full_name 
        FROM vehicles v 
        JOIN users u ON v.owner_id = u.id 
        ORDER BY v.created_at DESC
    ''')
    vehicles = c.fetchall()
    conn.close()
    
    for vehicle in vehicles:
        with st.expander(f"{vehicle[2]} {vehicle[3]} ({vehicle[4]})"):
            st.write(f"Owner: {vehicle[-1]}")
            st.write(f"Status: {vehicle[8]}")
            st.write(f"Daily Rate: AED {vehicle[6]}")
            st.write(f"Location: {vehicle[7]}")
            
            if vehicle[11]:  # If has images
                images = vehicle[11].split(',')
                cols = st.columns(len(images))
                for idx, img in enumerate(images):
                    with cols[idx]:
                        st.image(f"data:image/jpeg;base64,{img}")
            
            if st.button("Toggle Status", key=f"toggle_vehicle_{vehicle[0]}"):
                new_status = 'unavailable' if vehicle[8] == 'available' else 'available'
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('UPDATE vehicles SET status = ? WHERE id = ?',
                         (new_status, vehicle[0]))
                conn.commit()
                conn.close()
                st.experimental_rerun()

def show_admin_bookings():
    st.subheader("Booking Management")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT b.*, u.full_name, v.make, v.model, v.year
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN vehicles v ON b.vehicle_id = v.id
        ORDER BY b.created_at DESC
    ''')
    bookings = c.fetchall()
    conn.close()
    
    for booking in bookings:
        with st.expander(f"Booking #{booking[0]} - {booking[12]} {booking[13]} {booking[14]}"):
            st.write(f"Customer: {booking[11]}")
            st.write(f"Dates: {booking[3]} to {booking[4]}")
            st.write(f"Total Amount: AED {booking[5]}")
            st.write(f"Status: {booking[6]}")
            st.write(f"Payment Status: {booking[7]}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Approve", key=f"approve_{booking[0]}"):
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute('UPDATE bookings SET status = ? WHERE id = ?',
                             ('confirmed', booking[0]))
                    conn.commit()
                    conn.close()
                    st.experimental_rerun()
            with col2:
                if st.button("Reject", key=f"reject_{booking[0]}"):
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute('UPDATE bookings SET status = ? WHERE id = ?',
                             ('rejected', booking[0]))
                    conn.commit()
                    conn.close()
                    st.experimental_rerun()
            with col3:
                if st.button("Mark Paid", key=f"paid_{booking[0]}"):
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute('UPDATE bookings SET payment_status = ? WHERE id = ?',
                             ('paid', booking[0]))
                    conn.commit()
                    conn.close()
                    st.experimental_rerun()

def show_admin_reports():
    st.subheader("Reports and Analytics")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", 
                                  value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", 
                                value=datetime.now())
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Revenue metrics
    c.execute('''
        SELECT SUM(total_amount), COUNT(*), 
               AVG(total_amount),
               SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END)
        FROM bookings
        WHERE date(created_at) BETWEEN ? AND ?
    ''', (start_date, end_date))
    
    total_revenue, total_bookings, avg_booking_value, paid_revenue = c.fetchone()
    
    # Display metrics
    st.markdown("### Revenue Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Revenue", f"AED {total_revenue or 0:,.2f}")
    with col2:
        st.metric("Total Bookings", str(total_bookings or 0))
    with col3:
        st.metric("Average Booking Value", f"AED {avg_booking_value or 0:,.2f}")
    with col4:
        st.metric("Collected Revenue", f"AED {paid_revenue or 0:,.2f}")
    
    # Popular vehicles
    st.markdown("### Popular Vehicles")
    c.execute('''
        SELECT v.make, v.model, COUNT(*) as bookings, 
               SUM(b.total_amount) as revenue
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE date(b.created_at) BETWEEN ? AND ?
        GROUP BY v.id
        ORDER BY book_id:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user_data = c.fetchone()
            conn.close()
            
            if user_data:
                st.session_state.user_data = {
                    'id': user_data[0],
                    'email': user_data[1],
                    'full_name': user_data[3],
                    'role': user_data[9]
                }
                return True
    
    st.session_state.user_data = None
    return False

def show_privacy_policy():
    st.markdown("""
        ## Privacy Policy
        
        ### 1. Information We Collect
        - Personal identification information
        - Vehicle information
        - Booking details
        - Payment information
        
        ### 2. How We Use Your Information
        - To process your bookings
        - To maintain your account
        - To improve our services
        - To send periodic emails
        
        ### 3. Information Protection
        We implement various security measures to maintain the safety of your personal information.
        
        ### 4. Cookie Usage
        We use cookies to enhance your experience and analyze our traffic.
        
        ### 5. Third-party Disclosure
        We do not sell, trade, or transfer your information to third parties.
        
        ### 6. Your Rights
        You have the right to:
        - Access your data
        - Correct your data
        - Delete your data
        - Export your data
        
        ### 7. Contact Us
        For any privacy-related questions, please contact us at privacy@premiumcarrentals.com
    """)

def save_uploaded_image(uploaded_file):
    """Save and process uploaded images"""
    try:
        image = Image.open(uploaded_file)
        
        # Resize if too large
        max_size = (800, 800)
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr = img_byte_arr.getvalue()
        
        return base64.b64encode(img_byte_arr).decode()
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

def main():
    # Check for existing session
    load_user_data()
    
    # Sidebar navigation
    with st.sidebar:
        if st.session_state.user_data:
            st.write(f"Welcome, {st.session_state.user_data['full_name']}!")
            
            if st.button("Browse Cars"):
                st.session_state.page = "browse"
            if st.button("My Bookings"):
                st.session_state.page = "bookings"
            if st.button("Profile"):
                st.session_state.page = "profile"
            if st.session_state.user_data['role'] == 'admin':
                if st.button("Admin Panel"):
                    st.session_state.page = "admin"
            
            if st.button("Logout"):
                st.session_state.clear()
                st.experimental_rerun()
        else:
            if st.button("Login"):
                st.session_state.page = "login"
            if st.button("Register"):
                st.session_state.page = "register"
        
        # Privacy Policy button
        if st.button("Privacy Policy"):
            st.session_state.page = "privacy"
    
    # Main content
    if not hasattr(st.session_state, 'page'):
        st.session_state.page = "home"
    
    # Page routing
    if st.session_state.page == "home":
        show_home_page()
    elif st.session_state.page == "login":
        show_login_page()
    elif st.session_state.page == "register":
        show_register_page()
    elif st.session_state.page == "privacy":
        show_privacy_policy()
    elif not st.session_state.user_data:
        st.warning("Please login to continue")
        show_login_page()
    elif st.session_state.page == "browse":
        show_browse_page()
    elif st.session_state.page == "bookings":
        show_bookings_page()
    elif st.session_state.page == "profile":
        show_profile_page()
    elif st.session_state.page == "admin" and st.session_state.user_data['role'] == 'admin':
        show_admin_page()

def show_home_page():
    st.title("Welcome to Premium Car Rentals")
    
    # Featured cars section
    st.header("Featured Vehicles")
    col1, col2, col3 = st.columns(3)
    
    # Sample featured cars (replace with actual database queries in production)
    featured_cars = [
        {"name": "Tesla Model S", "price": "500", "image": "tesla.jpg"},
        {"name": "BMW M5", "price": "450", "image": "bmw.jpg"},
        {"name": "Mercedes S-Class", "price": "600", "image": "mercedes.jpg"}
    ]
    
    for idx, car in enumerate(featured_cars):
        with [col1, col2, col3][idx]:
            st.markdown(f"""
                <div class="modern-card">
                    <h3>{car['name']}</h3>
                    <p>AED {car['price']}/day</p>
                </div>
            """, unsafe_allow_html=True)

def show_login_page():
    st.title("Login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        remember_me = st.checkbox("Remember me")
        
        if st.form_submit_button("Login"):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE email = ? AND password = ?',
                     (email, hash_password(password)))
            user = c.fetchone()
            conn.close()
            
            if user:
                # Create session if remember_me is checked
                if remember_me:
                    session_token = create_session(user[0])
                    st.session_state.session_token = session_token
                
                # Update last login
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('UPDATE users SET last_login = ? WHERE id = ?',
                         (datetime.now(), user[0]))
                conn.commit()
                conn.close()
                
                # Set user data in session
                st.session_state.user_data = {
                    'id': user[0],
                    'email': user[1],
                    'full_name': user[3],
                    'role': user[9]
                }
                
                st.success("Login successful!")
                st.session_state.page = "browse"
                st.experimental_rerun()
            else:
                st.error("Invalid email or password")
    
    # Add links for registration and password recovery
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create New Account"):
            st.session_state.page = "register"
            st.experimental_rerun()
    with col2:
        if st.button("Forgot Password?"):
            st.session_state.page = "reset_password"
            st.experimental_rerun()

def show_register_page():
    st.title("Create Account")
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name*")
            email = st.text_input("Email*")
            phone = st.text_input("Phone Number*")
            address = st.text_area("Address")
        
        with col2:
            password = st.text_input("Password*", type="password")
            confirm_password = st.text_input("Confirm Password*", type="password")
            driving_license = st.text_input("Driving License Number*")
            profile_pic = st.file_uploader("Profile Picture (optional)", type=['jpg', 'png', 'jpeg'])
        
        st.markdown("### Terms and Conditions")
        st.markdown("""
            By creating an account, you agree to our:
            - Terms of Service
            - Privacy Policy
            - Rental Agreement Terms
        """)
        agree_terms = st.checkbox("I agree to the Terms and Conditions")
        
        if st.form_submit_button("Create Account"):
            if not all([full_name, email, phone, password, confirm_password, driving_license]):
                st.error("Please fill in all required fields")
                return
            
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            
            if not agree_terms:
                st.error("Please agree to the Terms and Conditions")
                return
            
            # Check if email already exists
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE email = ?', (email,))
            if c.fetchone():
                st.error("Email already registered")
                conn.close()
                return
            
            try:
                # Process profile picture if uploaded
                profile_pic_data = None
                if profile_pic:
                    profile_pic_data = save_uploaded_image(profile_pic)
                
                # Insert new user
                c.execute('''
                    INSERT INTO users 
                    (email, password, full_name, phone, address, 
                     driving_license, profile_pic, role, account_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'user', 'active')
                ''', (
                    email,
                    hash_password(password),
                    full_name,
                    phone,
                    address,
                    driving_license,
                    profile_pic_data
                ))
                
                conn.commit()
                st.success("Registration successful! Please login.")
                
                # Send welcome email (implement this function based on your email service)
                # send_welcome_email(email, full_name)
                
                # Redirect to login page
                st.session_state.page = "login"
                st.experimental_rerun()
                
            except Exception as e:
                st.error(f"Registration failed: {str(e)}")
            finally:
                conn.close()

def show_reset_password_page():
    st.title("Reset Password")
    
    step = st.session_state.get('reset_password_step', 1)
    
    if step == 1:
        with st.form("reset_password_step1"):
            email = st.text_input("Enter your email address")
            if st.form_submit_button("Send Reset Link"):
                # Check if email exists
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('SELECT id FROM users WHERE email = ?', (email,))
                user = c.fetchone()
                conn.close()
                
                if user:
                    # Generate and store reset token
                    reset_token = hashlib.sha256(os.urandom(32)).hexdigest()
                    st.session_state.reset_token = reset_token
                    st.session_state.reset_email = email
                    
                    # In a real application, send this token via email
                    # For demo, we'll just move to next step
                    st.session_state.reset_password_step = 2
                    st.experimental_rerun()
                else:
                    st.error("Email not found")
    
    elif step == 2:
        with st.form("reset_password_step2"):
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Reset Password"):
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                    return
                
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute(
                        'UPDATE users SET password = ? WHERE email = ?',
                        (hash_password(new_password), st.session_state.reset_email)
                    )
                    conn.commit()
                    conn.close()
                    
                    st.success("Password reset successful!")
                    
                    # Clear reset session data
                    del st.session_state.reset_password_step
                    del st.session_state.reset_token
                    del st.session_state.reset_email
                    
                    # Redirect to login
                    st.session_state.page = "login"
                    st.experimental_rerun()
                    
                except Exception as e:
                    st.error(f"Password reset failed: {str(e)}")

def show_browse_page():
    st.title("Available Vehicles")
    
    # Search and Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search = st.text_input("Search Vehicles", placeholder="Enter make, model, or year")
    with col2:
        category = st.selectbox("Category", ["All", "Luxury", "Sports", "SUV", "Electric"])
    with col3:
        price_range = st.slider("Price Range (AED/day)", 0, 2000, (200, 1000))
    with col4:
        location = st.selectbox("Location", ["All", "Dubai Marina", "Downtown Dubai", "Palm Jumeirah"])
    
    # Get vehicles from database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    query = '''
        SELECT v.*, u.full_name as owner_name, u.rating as owner_rating
        FROM vehicles v
        JOIN users u ON v.owner_id = u.id
        WHERE v.status = 'available'
    '''
    params = []
    
    if search:
        query += """ AND (
            v.make LIKE ? OR v.model LIKE ? OR v.year LIKE ?
        )"""
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])
    
    if category != "All":
        query += " AND v.category = ?"
        params.append(category)
    
    if location != "All":
        query += " AND v.location = ?"
        params.append(location)
    
    query += f" AND v.daily_rate BETWEEN {price_range[0]} AND {price_range[1]}"
    query += " ORDER BY v.created_at DESC"
    
    c.execute(query, params)
    vehicles = c.fetchall()
    conn.close()
    
    if not vehicles:
        st.info("No vehicles found matching your criteria.")
        return
    
    # Display vehicles in a grid
    cols = st.columns(3)
    for idx, vehicle in enumerate(vehicles):
        with cols[idx % 3]:
            st.markdown(f"""
                <div class="car-card">
                    <img src="data:image/jpeg;base64,{vehicle[11].split(',')[0] if vehicle[11] else ''}"
                         style="width:100%; height:200px; object-fit:cover; border-radius:8px;">
                    <h3>{vehicle[2]} {vehicle[3]} ({vehicle[4]})</h3>
                    <p class="price">AED {vehicle[6]}/day</p>
                    <p>{vehicle[7]}</p>
                    <p><small>Owner: {vehicle[-2]} ({'⭐' * int(vehicle[-1]) if vehicle[-1] else 'New'})</small></p>
                    <div class="features">
                        {json.loads(vehicle[10]).get('highlights', '')}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("View Details", key=f"view_{vehicle[0]}"):
                st.session_state.selected_vehicle = vehicle[0]
                st.session_state.page = "vehicle_details"
                st.experimental_rerun()
            
            if st.button("Book Now", key=f"book_{vehicle[0]}"):
                st.session_state.selected_vehicle = vehicle[0]
                st.session_state.page = "booking"
                st.experimental_rerun()

def show_vehicle_details():
    if 'selected_vehicle' not in st.session_state:
        st.error("No vehicle selected")
        st.session_state.page = "browse"
        st.experimental_rerun()
        return

    # Fetch vehicle details
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT v.*, u.full_name as owner_name, u.email as owner_email
        FROM vehicles v
        JOIN users u ON v.owner_id = u.id
        WHERE v.id = ?
    ''', (st.session_state.selected_vehicle,))
    
    vehicle = c.fetchone()
    
    if not vehicle:
        st.error("Vehicle not found")
        conn.close()
        st.session_state.page = "browse"
        st.experimental_rerun()
        return

    # Back button
    if st.button("← Back to Browse"):
        st.session_state.page = "browse"
        st.experimental_rerun()

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        # Vehicle images
        if vehicle[11]:  # images column
            images = vehicle[11].split(',')
            image_cols = st.columns(len(images))
            for idx, img in enumerate(images):
                with image_cols[idx]:
                    st.image(
                        f"data:image/jpeg;base64,{img}",
                        caption=f"Image {idx + 1}",
                        use_column_width=True
                    )

        # Vehicle information
        st.title(f"{vehicle[2]} {vehicle[3]} ({vehicle[4]})")
        st.subheader(f"AED {vehicle[6]:,.2f} per day")

        # Specifications
        st.markdown("### Specifications")
        specs = json.loads(vehicle[8])  # specs column
        cols = st.columns(2)
        with cols[0]:
            st.write("🚗 Make:", vehicle[2])
            st.write("📅 Year:", vehicle[4])
            st.write("⚙️ Transmission:", specs.get('transmission', 'N/A'))
        with cols[1]:
            st.write("🏎️ Model:", vehicle[3])
            st.write("🌍 Category:", vehicle[7])
            st.write("⛽ Fuel Type:", specs.get('fuel_type', 'N/A'))

        # Features and amenities
        st.markdown("### Features & Amenities")
        features = specs.get('features', [])
        feature_cols = st.columns(3)
        for idx, feature in enumerate(features):
            with feature_cols[idx % 3]:
                st.write(f"✓ {feature}")

        # Description
        st.markdown("### Description")
        st.write(vehicle[6])

    with col2:
        # Booking widget
        st.markdown("""
            <div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <h3>Book this vehicle</h3>
            </div>
        """, unsafe_allow_html=True)

        with st.form("booking_form"):
            # Date selection
            pickup_date = st.date_input(
                "Pickup Date",
                min_value=datetime.now().date(),
                value=datetime.now().date()
            )
            return_date = st.date_input(
                "Return Date",
                min_value=pickup_date,
                value=pickup_date + timedelta(days=1)
            )

            # Location
            location = st.selectbox(
                "Pickup Location",
                ["Dubai Marina", "Downtown Dubai", "Palm Jumeirah", "Dubai Mall"]
            )

            # Additional services
            st.markdown("### Additional Services")
            insurance = st.checkbox("Insurance (AED 50/day)")
            driver = st.checkbox("Driver (AED 200/day)")
            delivery = st.checkbox("Car Delivery (AED 100)")

            # Calculate total
            days = (return_date - pickup_date).days + 1
            base_price = vehicle[6] * days
            insurance_cost = 50 * days if insurance else 0
            driver_cost = 200 * days if driver else 0
            delivery_cost = 100 if delivery else 0
            total_cost = base_price + insurance_cost + driver_cost + delivery_cost

            # Display cost breakdown
            st.markdown("### Cost Breakdown")
            st.write(f"Base Rate ({days} days): AED {base_price:,.2f}")
            if insurance:
                st.write(f"Insurance: AED {insurance_cost:,.2f}")
            if driver:
                st.write(f"Driver Service: AED {driver_cost:,.2f}")
            if delivery:
                st.write(f"Delivery Fee: AED {delivery_cost:,.2f}")
            st.markdown(f"### Total: AED {total_cost:,.2f}")

            # Submit button
            submitted = st.form_submit_button("Book Now")
            if submitted:
                if not st.session_state.user_data:
                    st.warning("Please login to book this vehicle")
                    st.session_state.page = "login"
                    st.experimental_rerun()
                else:
                    try:
                        # Create booking record
                        c.execute('''
                            INSERT INTO bookings 
                            (user_id, vehicle_id, start_date, end_date, 
                             pickup_location, total_amount, insurance,
                             driver_service, delivery_service)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            st.session_state.user_data['id'],
                            vehicle[0],
                            pickup_date.strftime('%Y-%m-%d'),
                            return_date.strftime('%Y-%m-%d'),
                            location,
                            total_cost,
                            insurance,
                            driver,
                            delivery
                        ))
                        conn.commit()

                        # Send notifications
                        create_notification(
                            st.session_state.user_data['id'],
                            f"Booking confirmed for {vehicle[2]} {vehicle[3]}",
                            "booking_confirmation"
                        )
                        create_notification(
                            vehicle[1],  # owner_id
                            f"New booking for your {vehicle[2]} {vehicle[3]}",
                            "new_booking"
                        )

                        st.success("Booking confirmed! Check your email for details.")
                        st.session_state.page = "my_bookings"
                        st.experimental_rerun()

                    except Exception as e:
                        st.error(f"Booking failed: {str(e)}")
                    finally:
                        conn.close()

    # Reviews section
    st.markdown("### Customer Reviews")
    c.execute('''
        SELECT r.*, u.full_name, u.profile_pic
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.vehicle_id = ?
        ORDER BY r.created_at DESC
    ''', (vehicle[0],))
    
    reviews = c.fetchall()
    
    if not reviews:
        st.info("No reviews yet for this vehicle.")
    else:
        for review in reviews:
            with st.container():
                col1, col2 = st.columns([1, 5])
                with col1:
                    if review[7]:  # profile_pic
                        st.image(
                            f"data:image/jpeg;base64,{review[7]}",
                            width=50
                        )
                with col2:
                    st.markdown(f"""
                        <div style='background-color: white; padding: 10px; border-radius: 5px;'>
                            <p><strong>{review[6]}</strong> • {'⭐' * review[4]}</p>
                            <p>{review[5]}</p>
                            <small>{review[3].split()[0]}</small>
                        </div>
                    """, unsafe_allow_html=True)

        # Add review if user has rented this vehicle
        if st.session_state.user_data:
            c.execute('''
                SELECT id FROM bookings 
                WHERE user_id = ? AND vehicle_id = ? AND status = 'completed'
                LIMIT 1
            ''', (st.session_state.user_data['id'], vehicle[0]))
            
            if c.fetchone():
                with st.form("review_form"):
                    st.markdown("### Write a Review")
                    rating = st.slider("Rating", 1, 5, 5)
                    comment = st.text_area("Your Review")
                    
                    if st.form_submit_button("Submit Review"):
                        try:
                            c.execute('''
                                INSERT INTO reviews 
                                (user_id, vehicle_id, rating, comment)
                                VALUES (?, ?, ?, ?)
                            ''', (
                                st.session_state.user_data['id'],
                                vehicle[0],
                                rating,
                                comment
                            ))
                            conn.commit()
                            st.success("Review submitted successfully!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error submitting review: {str(e)}")

    conn.close()

def show_booking_confirmation(booking_id):
    st.title("Booking Confirmed!")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get booking details with vehicle and user information
    c.execute('''
        SELECT b.*, v.make, v.model, v.year, u.full_name, u.email
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        JOIN users u ON b.user_id = u.id
        WHERE b.id = ?
    ''', (booking_id,))
    
    booking = c.fetchone()
    conn.close()
    
    if not booking:
        st.error("Booking not found")
        return

    # Display confirmation
    st.markdown(f"""
        <div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h2>🎉 Your booking is confirmed!</h2>
            <p>Booking reference: #{booking[0]}</p>
        </div>
    """, unsafe_allow_html=True)

    # Booking details
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Vehicle Details")
        st.write(f"**Vehicle:** {booking[11]} {booking[12]} ({booking[13]})")
        st.write(f"**Pickup Date:** {booking[3]}")
        st.write(f"**Return Date:** {booking[4]}")
        st.write(f"**Location:** {booking[5]}")
        
    with col2:
        st.markdown("### Payment Details")
        st.write(f"**Total Amount:** AED {booking[6]:,.2f}")
        st.write(f"**Payment Status:** {booking[7]}")
        
        # Additional services
        services = []
        if booking[8]:  # insurance
            services.append("Insurance")
        if booking[9]:  # driver_service
            services.append("Driver Service")
        if booking[10]:  # delivery_service
            services.append("Car Delivery")
            
        if services:
            st.write("**Additional Services:**")
            for service in services:
                st.write(f"- {service}")

    # Next steps
    st.markdown("### Next Steps")
    st.markdown("""
        1. Check your email for the booking confirmation
        2. Present your driver's license at pickup
        3. Complete the vehicle inspection
        4. Enjoy your ride!
    """)

    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("View Booking Details"):
            st.session_state.page = "my_bookings"
            st.experimental_rerun()
    with col2:
        if st.button("Download Invoice"):
            # Implement invoice download
            pass
    with col3:
        if st.button("Contact Support"):
            st.session_state.page = "support"
            st.experimental_rerun()

def create_notification(user_id, message, notification_type):
    """Create a new notification for a user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO notifications 
            (user_id, message, type, read)
            VALUES (?, ?, ?, FALSE)
        ''', (user_id, message, notification_type))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating notification: {str(e)}")

def show_my_bookings():
    st.title("My Bookings")
    
    tabs = st.tabs(["Upcoming", "Past", "Cancelled"])
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    with tabs[0]:
        show_booking_list(c, "upcoming")
    with tabs[1]:
        show_booking_list(c, "past")
    with tabs[2]:
        show_booking_list(c, "cancelled")
    
    conn.close()

def show_booking_list(cursor, booking_type):
    today = datetime.now().date()
    
    if booking_type == "upcoming":
        query = '''
            SELECT 
                b.*,
                v.make, v.model, v.year, v.images,
                v.daily_rate, v.category,
                u.full_name as owner_name, u.phone as owner_phone
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.id
            JOIN users u ON v.owner_id = u.id
            WHERE b.user_id = ? 
            AND date(b.start_date) >= ?
            AND b.status != 'cancelled'
            ORDER BY b.start_date ASC
        '''
        cursor.execute(query, (st.session_state.user_data['id'], today))
    
    elif booking_type == "past":
        query = '''
            SELECT 
                b.*,
                v.make, v.model, v.year, v.images,
                v.daily_rate, v.category,
                u.full_name as owner_name, u.phone as owner_phone
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.id
            JOIN users u ON v.owner_id = u.id
            WHERE b.user_id = ? 
            AND date(b.end_date) < ?
            AND b.status != 'cancelled'
            ORDER BY b.end_date DESC
        '''
        cursor.execute(query, (st.session_state.user_data['id'], today))
    
    else:  # cancelled
        query = '''
            SELECT 
                b.*,
                v.make, v.model, v.year, v.images,
                v.daily_rate, v.category,
                u.full_name as owner_name, u.phone as owner_phone
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.id
            JOIN users u ON v.owner_id = u.id
            WHERE b.user_id = ? 
            AND b.status = 'cancelled'
            ORDER BY b.created_at DESC
        '''
        cursor.execute(query, (st.session_state.user_data['id'],))
    
    bookings = cursor.fetchall()
    
    if not bookings:
        st.info(f"No {booking_type} bookings found.")
        return
    
    for booking in bookings:
        with st.container():
            st.markdown("""
                <div style='background-color: white; padding: 20px; border-radius: 10px; 
                          margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Display vehicle image
                if booking['images']:
                    primary_image = booking['images'].split(',')[0]
                    st.image(
                        f"data:image/jpeg;base64,{primary_image}",
                        caption=f"{booking['make']} {booking['model']}",
                        use_column_width=True
                    )
            
            with col2:
                # Vehicle and booking details
                st.subheader(f"{booking['make']} {booking['model']} ({booking['year']})")
                
                # Status badge with appropriate color
                status_colors = {
                    'confirmed': 'green',
                    'pending': 'orange',
                    'completed': 'blue',
                    'cancelled': 'red'
                }
                status_color = status_colors.get(booking['status'], 'grey')
                
                st.markdown(f"""
                    <span style='background-color: {status_color}; color: white; 
                              padding: 5px 10px; border-radius: 15px; font-size: 0.8em;'>
                        {booking['status'].upper()}
                    </span>
                """, unsafe_allow_html=True)
                
                # Booking details
                col1, col2 = st.columns(2)
                with col1:
                    st.write("📅 **Pickup Date:**", booking['start_date'])
                    st.write("📍 **Location:**", booking['pickup_location'])
                    st.write("💰 **Total Amount:** AED", f"{booking['total_amount']:,.2f}")
                
                with col2:
                    st.write("📅 **Return Date:**", booking['end_date'])
                    st.write("🚗 **Category:**", booking['category'])
                    st.write("📱 **Owner Contact:**", booking['owner_phone'])
                
                # Additional services
                if any([booking['insurance'], booking['driver_service'], 
                       booking['delivery_service']]):
                    st.markdown("#### Additional Services:")
                    services = []
                    if booking['insurance']:
                        services.append("🛡️ Insurance")
                    if booking['driver_service']:
                        services.append("👨‍✈️ Driver Service")
                    if booking['delivery_service']:
                        services.append("🚚 Car Delivery")
                    st.write(" | ".join(services))
                
                # Action buttons based on booking status
                if booking['status'] == 'pending':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Cancel Booking", key=f"cancel_{booking['id']}"):
                            if cancel_booking(booking['id']):
                                st.success("Booking cancelled successfully!")
                                st.experimental_rerun()
                    with col2:
                        if st.button("Modify Booking", key=f"modify_{booking['id']}"):
                            st.session_state.booking_to_modify = booking['id']
                            st.session_state.page = "modify_booking"
                            st.experimental_rerun()
                
                elif booking['status'] == 'completed':
                    # Check if user has already reviewed
                    cursor.execute('''
                        SELECT id FROM reviews 
                        WHERE booking_id = ? AND user_id = ?
                    ''', (booking['id'], st.session_state.user_data['id']))
                    
                    if not cursor.fetchone():  # No review yet
                        if st.button("Write Review", key=f"review_{booking['id']}"):
                            st.session_state.booking_to_review = booking['id']
                            st.session_state.page = "write_review"
                            st.experimental_rerun()
                
                # Download invoice button for all bookings
                if st.button("Download Invoice", key=f"invoice_{booking['id']}"):
                    generate_invoice(booking)
            
            st.markdown("</div>", unsafe_allow_html=True)

def cancel_booking(booking_id):
    """Cancel a booking and update the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get booking details first
        c.execute('''
            SELECT b.*, v.make, v.model, u.email as owner_email
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.id
            JOIN users u ON v.owner_id = u.id
            WHERE b.id = ?
        ''', (booking_id,))
        
        booking = c.fetchone()
        
        if not booking:
            st.error("Booking not found")
            return False
        
        # Check if cancellation is allowed (e.g., not too close to pickup date)
        pickup_date = datetime.strptime(booking['start_date'], '%Y-%m-%d').date()
        if (pickup_date - datetime.now().date()).days < 1:
            st.error("Cancellation is not allowed within 24 hours of pickup")
            return False
        
        # Update booking status
        c.execute('''
            UPDATE bookings 
            SET status = 'cancelled',
                cancellation_date = CURRENT_TIMESTAMP,
                cancellation_reason = 'Customer cancelled'
            WHERE id = ?
        ''', (booking_id,))
        
        # Create notifications for both user and owner
        create_notification(
            st.session_state.user_data['id'],
            f"Your booking for {booking['make']} {booking['model']} has been cancelled",
            "booking_cancelled"
        )
        
        create_notification(
            booking['owner_email'],
            f"Booking cancelled for your {booking['make']} {booking['model']}",
            "booking_cancelled"
        )
        
        conn.commit()
        return True
    
    except Exception as e:
        st.error(f"Error cancelling booking: {str(e)}")
        return False
    finally:
        conn.close()

def generate_invoice(booking):
    """Generate and download PDF invoice for a booking"""
    try:
        from fpdf import FPDF
        
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Luxury Car Rentals - Invoice', 0, 1, 'C')
        pdf.line(10, 30, 200, 30)
        
        # Booking details
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"Booking Reference: #{booking['id']}", 0, 1)
        pdf.cell(0, 10, f"Vehicle: {booking['make']} {booking['model']} ({booking['year']})", 0, 1)
        pdf.cell(0, 10, f"Dates: {booking['start_date']} to {booking['end_date']}", 0, 1)
        
        # Cost breakdown
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Cost Breakdown:', 0, 1)
        pdf.set_font('Arial', '', 12)
        
        days = (datetime.strptime(booking['end_date'], '%Y-%m-%d') - 
                datetime.strptime(booking['start_date'], '%Y-%m-%d')).days + 1
        
        pdf.cell(0, 10, f"Daily Rate: AED {booking['daily_rate']:,.2f} x {days} days", 0, 1)
        
        if booking['insurance']:
            pdf.cell(0, 10, "Insurance: AED 50.00 per day", 0, 1)
        if booking['driver_service']:
            pdf.cell(0, 10, "Driver Service: AED 200.00 per day", 0, 1)
        if booking['delivery_service']:
            pdf.cell(0, 10, "Car Delivery: AED 100.00", 0, 1)
        
        pdf.line(10, pdf.get_y() + 5, 200, pdf.get_y() + 5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"Total Amount: AED {booking['total_amount']:,.2f}", 0, 1)
        
        # Save the PDF
        pdf_output = pdf.output(dest='S').encode('latin1')
        
        # Create download button
        st.download_button(
            label="Download Invoice",
            data=pdf_output,
            file_name=f"invoice_{booking['id']}.pdf",
            mime="application/pdf"
        )
        
    except Exception as e:
        st.error(f"Error generating invoice: {str(e)}")

def show_modify_booking():
    if 'booking_to_modify' not in st.session_state:
        st.error("No booking selected for modification")
        st.session_state.page = "my_bookings"
        st.experimental_rerun()
        return
    
    booking_id = st.session_state.booking_to_modify
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get booking details
    c.execute('''
        SELECT b.*, v.make, v.model, v.year, v.daily_rate, v.owner_id,
               u.full_name as owner_name, u.email as owner_email
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        JOIN users u ON v.owner_id = u.id
        WHERE b.id = ?
    ''', (booking_id,))
    
    booking = c.fetchone()
    
    if not booking:
        st.error("Booking not found")
        conn.close()
        st.session_state.page = "my_bookings"
        st.experimental_rerun()
        return
    
    st.title(f"Modify Booking - {booking['make']} {booking['model']}")
    
    with st.form("modify_booking_form"):
        # Original booking details for reference
        st.info(f"""
            Original Booking Details:
            - Vehicle: {booking['make']} {booking['model']} ({booking['year']})
            - Pickup: {booking['start_date']}
            - Return: {booking['end_date']}
            - Location: {booking['pickup_location']}
            - Total Amount: AED {booking['total_amount']:,.2f}
        """)
        
        # New dates
        col1, col2 = st.columns(2)
        with col1:
            new_pickup = st.date_input(
                "New Pickup Date",
                value=datetime.strptime(booking['start_date'], '%Y-%m-%d').date(),
                min_value=datetime.now().date()
            )
        with col2:
            new_return = st.date_input(
                "New Return Date",
                value=datetime.strptime(booking['end_date'], '%Y-%m-%d').date(),
                min_value=new_pickup
            )
        
        # New location
        locations = ["Dubai Marina", "Downtown Dubai", "Palm Jumeirah", "Dubai Mall"]
        new_location = st.selectbox(
            "New Pickup Location",
            locations,
            index=locations.index(booking['pickup_location'])
        )
        
        # Additional services
        st.markdown("### Additional Services")
        col1, col2 = st.columns(2)
        with col1:
            new_insurance = st.checkbox(
                "Insurance (AED 50/day)", 
                value=booking['insurance']
            )
            new_driver = st.checkbox(
                "Driver Service (AED 200/day)", 
                value=booking['driver_service']
            )
        with col2:
            new_delivery = st.checkbox(
                "Car Delivery (AED 100)", 
                value=booking['delivery_service']
            )
            new_vip = st.checkbox(
                "VIP Service (AED 300)", 
                value=booking.get('vip_service', False)
            )
        
        # Calculate new total
        days = (new_return - new_pickup).days + 1
        base_price = booking['daily_rate'] * days
        insurance_cost = 50 * days if new_insurance else 0
        driver_cost = 200 * days if new_driver else 0
        delivery_cost = 100 if new_delivery else 0
        vip_cost = 300 if new_vip else 0
        new_total = base_price + insurance_cost + driver_cost + delivery_cost + vip_cost
        
        # Display cost breakdown
        st.markdown("### Cost Breakdown")
        st.write(f"Base Rate ({days} days): AED {base_price:,.2f}")
        if new_insurance:
            st.write(f"Insurance: AED {insurance_cost:,.2f}")
        if new_driver:
            st.write(f"Driver Service: AED {driver_cost:,.2f}")
        if new_delivery:
            st.write(f"Delivery: AED {delivery_cost:,.2f}")
        if new_vip:
            st.write(f"VIP Service: AED {vip_cost:,.2f}")
        
        st.markdown(f"### New Total: AED {new_total:,.2f}")
        
        # Show price difference
        price_difference = new_total - booking['total_amount']
        if price_difference != 0:
            color = "green" if price_difference < 0 else "red"
            st.markdown(f"""
                <div style='color: {color}; font-weight: bold;'>
                    Price Difference: {'-' if price_difference < 0 else '+'}AED {abs(price_difference):,.2f}
                </div>
            """, unsafe_allow_html=True)
        
        # Special requests or notes
        modification_notes = st.text_area(
            "Special Requests or Notes",
            placeholder="Any special requests or notes for the modification..."
        )
        
        if st.form_submit_button("Update Booking"):
            try:
                # Check if dates are available
                c.execute('''
                    SELECT COUNT(*) FROM bookings
                    WHERE vehicle_id = ?
                    AND id != ?
                    AND status = 'confirmed'
                    AND (
                        (start_date BETWEEN ? AND ?) OR
                        (end_date BETWEEN ? AND ?) OR
                        (? BETWEEN start_date AND end_date)
                    )
                ''', (
                    booking['vehicle_id'],
                    booking_id,
                    new_pickup.strftime('%Y-%m-%d'),
                    new_return.strftime('%Y-%m-%d'),
                    new_pickup.strftime('%Y-%m-%d'),
                    new_return.strftime('%Y-%m-%d'),
                    new_pickup.strftime('%Y-%m-%d')
                ))
                
                if c.fetchone()[0] > 0:
                    st.error("Selected dates are not available. Please choose different dates.")
                    return
                
                # Update booking
                c.execute('''
                    UPDATE bookings 
                    SET start_date = ?,
                        end_date = ?,
                        pickup_location = ?,
                        total_amount = ?,
                        insurance = ?,
                        driver_service = ?,
                        delivery_service = ?,
                        vip_service = ?,
                        modification_notes = ?,
                        last_modified = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    new_pickup.strftime('%Y-%m-%d'),
                    new_return.strftime('%Y-%m-%d'),
                    new_location,
                    new_total,
                    new_insurance,
                    new_driver,
                    new_delivery,
                    new_vip,
                    modification_notes,
                    booking_id
                ))
                
                # Create modification history record
                c.execute('''
                    INSERT INTO booking_modifications 
                    (booking_id, modified_by, old_start_date, new_start_date,
                     old_end_date, new_end_date, old_amount, new_amount,
                     modification_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    booking_id,
                    st.session_state.user_data['id'],
                    booking['start_date'],
                    new_pickup.strftime('%Y-%m-%d'),
                    booking['end_date'],
                    new_return.strftime('%Y-%m-%d'),
                    booking['total_amount'],
                    new_total,
                    modification_notes
                ))
                
                # Create notifications
                create_notification(
                    st.session_state.user_data['id'],
                    f"Your booking for {booking['make']} {booking['model']} has been modified.",
                    "booking_modified"
                )
                
                create_notification(
                    booking['owner_id'],
                    f"Booking modification for your {booking['make']} {booking['model']}.",
                    "booking_modified"
                )
                
                # Send email notifications (implement based on your email service)
                # send_booking_modification_email(booking['email'], booking_id, new_details)
                # send_booking_modification_email(booking['owner_email'], booking_id, new_details)
                
                conn.commit()
                st.success("Booking updated successfully!")
                
                # Clear the modification state and return to bookings
                del st.session_state.booking_to_modify
                st.session_state.page = "my_bookings"
                st.experimental_rerun()
                
            except Exception as e:
                st.error(f"Error updating booking: {str(e)}")
            finally:
                conn.close()

def create_notification(user_id, message, notification_type):
    """Create a notification for a user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO notifications 
            (user_id, message, type, read_status, created_at)
            VALUES (?, ?, ?, FALSE, CURRENT_TIMESTAMP)
        """, (user_id, message, notification_type))
        
        conn.commit()
    except Exception as e:
        print(f"Error creating notification: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def show_notifications():
    """Display user notifications"""
    st.title("Notifications")
    
    if 'user_data' not in st.session_state:
        st.warning("Please login to view notifications")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Get all notifications for the user
        c.execute("""
            SELECT * FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (st.session_state.user_data['id'],))
        
        notifications = c.fetchall()
        
        if not notifications:
            st.info("No notifications")
            return
        
        # Mark all as read option
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Mark All as Read"):
                c.execute("""
                    UPDATE notifications
                    SET read_status = TRUE
                    WHERE user_id = ? AND read_status = FALSE
                """, (st.session_state.user_data['id'],))
                conn.commit()
                st.success("All notifications marked as read")
                st.experimental_rerun()
        
        # Display notifications
        for notif in notifications:
            with st.container():
                st.markdown(f"""
                    <div style='background-color: {"#f8f9fa" if notif[4] else "#e3f2fd"}; 
                              padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
                        <div style='display: flex; justify-content: space-between;'>
                            <span>{notif[2]}</span>
                            <small>{notif[5]}</small>
                        </div>
                        <div style='margin-top: 5px; font-size: 0.9em; color: #666;'>
                            Type: {notif[3]}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if not notif[4]:  # if not read
                    if st.button("Mark as Read", key=f"read_{notif[0]}"):
                        c.execute("""
                            UPDATE notifications
                            SET read_status = TRUE
                            WHERE id = ?
                        """, (notif[0],))
                        conn.commit()
                        st.experimental_rerun()
    
    except Exception as e:
        st.error(f"Error loading notifications: {str(e)}")
    finally:
        conn.close()


def setup_notifications_table():
    """Create the notifications table in the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                type TEXT NOT NULL,
                read_status BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create index for faster notification lookups
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_user 
            ON notifications(user_id, read_status)
        """)
        
        conn.commit()
    except Exception as e:
        print(f"Error setting up notifications table: {str(e)}")
    finally:
        conn.close()

def get_unread_notifications_count(user_id):
    """Get the count of unread notifications for a user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            SELECT COUNT(*) FROM notifications
            WHERE user_id = ? AND read_status = FALSE
        """, (user_id,))
        
        count = c.fetchone()[0]
        return count
    except Exception as e:
        print(f"Error counting notifications: {str(e)}")
        return 0
    finally:
        if 'conn' in locals():
            conn.close()



# Initialize the application
if __name__ == "__main__":
    # Initialize database if it doesn't exist
    if not os.path.exists(DB_PATH):
        setup_database()
    
    # Load user session
    if 'user_data' not in st.session_state:
        if 'session_token' in st.session_state:
            verify_session(st.session_state.session_token)
    
    # Page routing
    if not hasattr(st.session_state, 'page'):
        st.session_state.page = 'home'
    
    # Display current page
    page_mapping = {
        'home': show_home_page,
        'login': show_login_page,
        'register': show_register_page,
        'browse': show_browse_page,
        'vehicle_details': show_vehicle_details,
        'my_bookings': show_my_bookings,
        'modify_booking': show_modify_booking,
        'notifications': show_notifications
    }
    
    current_page = st.session_state.page
    if current_page in page_mapping:
        page_mapping[current_page]()
    else:
        st.error("Page not found")
        st.session_state.page = 'home'
        st.experimental_rerun()
