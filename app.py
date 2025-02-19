import streamlit as st
import pandas as pd
import sqlite3
import os
import hashlib
import json
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from web3 import Web3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import jwt
from cryptography.fernet import Fernet
from PIL import Image
import io
import base64
from dotenv import load_dotenv

load_dotenv()

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER")))
contract_address = os.getenv("CONTRACT_ADDRESS")

# AI Recommender System
class CarRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.matrix = None
        self.car_ids = []
        
    def train(self, cars):
        features = []
        for car in cars:
            text = f"{car['model']} {car['category']} {car['engine']} {car['features']}"
            features.append(text)
            self.car_ids.append(car['id'])
        self.matrix = self.vectorizer.fit_transform(features)
        
    def recommend(self, favorite_car_id, n=5):
        try:
            idx = self.car_ids.index(favorite_car_id)
            sim_scores = cosine_similarity(self.matrix[idx], self.matrix)
            similar_indices = np.argsort(sim_scores[0])[::-1][1:n+1]
            return [self.car_ids[i] for i in similar_indices]
        except:
            return []

# Blockchain Integration
class RentalContract:
    ABI = json.loads(os.getenv("CONTRACT_ABI"))
    
    def __init__(self):
        self.contract = w3.eth.contract(
            address=contract_address,
            abi=self.ABI
        )
    
    def create_agreement(self, booking_id, terms):
        try:
            tx = self.contract.functions.createAgreement(
                booking_id,
                json.dumps(terms)
            ).build_transaction({
                'chainId': 5,  # Goerli testnet
                'gas': 200000,
                'nonce': w3.eth.get_transaction_count(os.getenv("WALLET_ADDRESS")),
            })
            signed_tx = w3.eth.account.sign_transaction(tx, os.getenv("PRIVATE_KEY"))
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return tx_hash.hex()
        except Exception as e:
            print(f"Blockchain error: {e}")
            return None

# Web3 Authentication
class Web3Auth:
    def __init__(self):
        self.nonce_storage = {}
        
    def generate_nonce(self, email):
        nonce = Fernet.generate_key().decode()
        self.nonce_storage[email] = nonce
        return nonce
    
    def verify_signature(self, email, signature):
        nonce = self.nonce_storage.get(email)
        if not nonce:
            return False
        message = f"Auth Request: {nonce}"
        try:
            address = w3.eth.account.recover_message(
                text=message,
                signature=signature
            )
            return address
        except:
            return False

# Database Setup
def setup_database():
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Users table with Web3 fields
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            wallet_address TEXT UNIQUE,
            nonce TEXT,
            profile_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add blockchain fields to bookings
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY,
            contract_hash TEXT,
            blockchain_status TEXT DEFAULT 'pending'
        )
    ''')
    
    # Add AI training data field
    c.execute('''
        CREATE TABLE IF NOT EXISTS car_listings (
            id INTEGER PRIMARY KEY,
            ai_features TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Metaverse Showroom Component
def metaverse_showroom(car_model):
    st.markdown(f"""
        <div style="height: 600px; border-radius: 15px; overflow: hidden;">
            <iframe 
                style="width: 100%; height: 100%; border: none;"
                allow="xr-spatial-tracking"
                src="https://app.vectary.com/p/5zs6Jm8Ufz40wCiqeRgQKk?model={car_model}"
            ></iframe>
        </div>
    """, unsafe_allow_html=True)

# Enhanced Car Details with Metaverse
def show_car_details(car):
    # ... [Previous car details code] ...
    
    with st.expander("🚀 Metaverse Experience"):
        metaverse_showroom(car['model'])
        st.write("Explore the vehicle in our virtual showroom")
        
        if st.button("Enter VR Mode"):
            st.session_state.vr_mode = True
            st.rerun()

# AI-Powered Recommendations
def show_recommendations():
    conn = sqlite3.connect('car_rental.db')
    c = conn.cursor()
    
    # Get user's last booking
    c.execute('''
        SELECT car_id FROM bookings 
        WHERE user_email = ?
        ORDER BY created_at DESC LIMIT 1
    ''', (st.session_state.user_email,))
    last_car = c.fetchone()
    
    if last_car:
        c.execute('SELECT * FROM car_listings')
        all_cars = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
        
        recommender = CarRecommender()
        recommender.train(all_cars)
        
        recommended_ids = recommender.recommend(last_car[0])
        
        st.markdown("### AI Recommendations")
        cols = st.columns(4)
        for i, car_id in enumerate(recommended_ids):
            c.execute('SELECT * FROM car_listings WHERE id = ?', (car_id,))
            car = c.fetchone()
            with cols[i % 4]:
                display_car_card(car)

# Web3 Authentication Page
def web3_login():
    st.markdown("## Web3 Authentication")
    web3_auth = Web3Auth()
    
    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("Enter email")
        if st.button("Generate Auth Request"):
            nonce = web3_auth.generate_nonce(email)
            st.session_state.auth_nonce = nonce
            st.info(f"Sign this message in your wallet: {nonce}")
            
    with col2:
        signature = st.text_input("Enter signed message")
        if st.button("Verify Signature"):
            if 'auth_nonce' in st.session_state:
                address = web3_auth.verify_signature(email, signature)
                if address:
                    conn = sqlite3.connect('car_rental.db')
                    c = conn.cursor()
                    c.execute('SELECT * FROM users WHERE email = ?', (email,))
                    user = c.fetchone()
                    
                    if not user:
                        c.execute('''
                            INSERT INTO users (email, wallet_address, nonce)
                            VALUES (?, ?, ?)
                        ''', (email, address, st.session_state.auth_nonce))
                        conn.commit()
                    
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.rerun()

# Blockchain Rental Agreement
def create_blockchain_agreement(booking_id, terms):
    contract = RentalContract()
    tx_hash = contract.create_agreement(booking_id, terms)
    
    if tx_hash:
        conn = sqlite3.connect('car_rental.db')
        c = conn.cursor()
        c.execute('''
            UPDATE bookings 
            SET contract_hash = ?, blockchain_status = 'pending'
            WHERE id = ?
        ''', (tx_hash, booking_id))
        conn.commit()
        return True
    return False

# Main Application Flow
def main():
    st.set_page_config(
        page_title="Luxury Car Rentals 2025",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    setup_database()
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'vr_mode' not in st.session_state:
        st.session_state.vr_mode = False
    
    if st.session_state.vr_mode:
        show_vr_experience()
    else:
        if not st.session_state.logged_in:
            web3_login()
        else:
            show_main_interface()

def show_main_interface():
    st.sidebar.title("Navigation")
    menu = ["Browse Cars", "My Bookings", "Metaverse Showroom", "AI Assistant"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Browse Cars":
        show_car_listings()
    elif choice == "My Bookings":
        show_user_bookings()
    elif choice == "Metaverse Showroom":
        show_metaverse_dashboard()
    elif choice == "AI Assistant":
        show_ai_assistant()

def show_metaverse_dashboard():
    st.title("Virtual Showroom")
    metaverse_showroom("all")
    
    st.markdown("""
        <div style="margin-top: 20px;">
            <h3>Virtual Experience Features:</h3>
            <ul>
                <li>360° Vehicle Inspection</li>
                <li>Augmented Reality Test Drive</li>
                <li>NFT Gallery Integration</li>
                <li>Multiplayer Showroom</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

def show_ai_assistant():
    st.title("AI Rental Assistant")
    
    with st.chat_message("assistant"):
        st.write("How can I help you today?")
    
    if prompt := st.chat_input("Ask about vehicles, pricing, or availability"):
        with st.chat_message("user"):
            st.write(prompt)
        
        # AI response generation would be implemented here
        with st.chat_message("assistant"):
            st.write("Here are some options that match your needs:")
            show_recommendations()

if __name__ == "__main__":
    main()
