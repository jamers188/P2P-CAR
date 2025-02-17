import streamlit as st
import sqlite3
import hashlib
import os

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_database():
    """Create a simple database with an admin user"""
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Drop and recreate users table
    c.execute('DROP TABLE IF EXISTS users')
    
    c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')
    
    # Create admin user
    admin_email = 'admin@luxuryrentals.com'
    admin_password = hash_password('admin123')
    
    c.execute('''
        INSERT INTO users (email, password, role) 
        VALUES (?, ?, ?)
    ''', (admin_email, admin_password, 'admin'))
    
    conn.commit()
    conn.close()
    print("Database setup complete")

def verify_login(email, password):
    """Verify user credentials"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Hash the input password
        hashed_password = hash_password(password)
        
        # Check credentials
        c.execute('SELECT * FROM users WHERE email = ? AND password = ?', 
                  (email, hashed_password))
        user = c.fetchone()
        
        conn.close()
        
        return user is not None
    except Exception as e:
        st.error(f"Login error: {e}")
        return False

def main():
    # Ensure database exists
    if not os.path.exists('car_rental.db'):
        setup_database()
    
    st.title("Login Page")
    
    # Login form
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        # Validate inputs
        if not email or not password:
            st.error("Please enter both email and password")
            return
        
        # Attempt login
        if verify_login(email, password):
            st.success("Login Successful!")
            # You would typically set session state here
            st.write("Login would proceed")
        else:
            st.error("Invalid email or password")

    # Debug information
    st.markdown("### Debug Information")
    st.write(f"Database file exists: {os.path.exists('car_rental.db')}")
    
    # Optional: Show database contents (for debugging)
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        c.execute('SELECT email FROM users')
        users = c.fetchall()
        st.write("Registered Users:", users)
        conn.close()
    except Exception as e:
        st.error(f"Error reading database: {e}")

if __name__ == "__main__":
    main()
