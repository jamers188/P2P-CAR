import streamlit as st
import sqlite3
import hashlib
import os

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_login(email, password):
    """Verify user credentials with detailed logging"""
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        
        # Hash the input password
        hashed_password = hash_password(password)
        
        # Fetch user details
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        
        # Detailed logging
        st.write("Login Attempt Details:")
        st.write(f"Input Email: {email}")
        st.write(f"Input Hashed Password: {hashed_password}")
        
        if user:
            st.write(f"Stored User Details: {user}")
            st.write(f"Stored Hashed Password: {user[2]}")  # Assuming password is at index 2
            
            # Compare passwords
            if user[2] == hashed_password:
                conn.close()
                return True
            else:
                st.error("Password does not match")
        else:
            st.error(f"No user found with email: {email}")
        
        conn.close()
        return False
    except Exception as e:
        st.error(f"Login verification error: {e}")
        return False

def main():
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
    
    # Show all registered users (for debugging)
    try:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        c.execute('SELECT id, email FROM users')
        users = c.fetchall()
        st.write("Registered Users:")
        for user in users:
            st.write(f"ID: {user[0]}, Email: {user[1]}")
        conn.close()
    except Exception as e:
        st.error(f"Error reading database: {e}")

if __name__ == "__main__":
    main()
