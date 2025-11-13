import streamlit as st
import pandas as pd
from pymongo import MongoClient
import datetime

# --- MONGODB CONNECTION ---
@st.cache_resource
def get_database():
    """Connect to MongoDB using Streamlit secrets."""
    uri = st.secrets["mongo"]["uri"]  # ✅ Correct usage
    client = MongoClient(uri)
    db = client["shipping_portal"]
    return db

# Connect to DB
db = get_database()
users_collection = db["users"]
shipments_collection = db["shipments"]
# --- ENSURE ADMIN USER EXISTS ---
if not users_collection.find_one({"user_id": "admin"}):
    users_collection.insert_one({
        "user_id": "admin",
        "name": "Administrator",
        "password": "admin123",
        "role": "Admin"
    })


# --- HELPER FUNCTIONS ---
def create_user(user_id, name, password):
    """Create a new user in the database."""
    if users_collection.find_one({"user_id": user_id}):
        st.warning("⚠️ User ID already exists!")
    else:
        users_collection.insert_one({
            "user_id": user_id,
            "name": name,
            "password": password,
            "role": "user"
        })
        st.success(f"✅ User '{name}' created successfully!")


def validate_user(user_id, password):
    """Validate login credentials."""
    return users_collection.find_one({"user_id": user_id, "password": password})


def add_shipment(user_id, weight, address):
    """Add a new shipment for a user."""
    shipment = {
        "user_id": user_id,
        "weight": weight,
        "address": address,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    shipments_collection.insert_one(shipment)
    st.success("📦 Shipment added successfully!")


# --- STREAMLIT UI CONFIG ---
st.set_page_config(page_title="Shipping Portal", layout="centered")
st.title("📦 Shipping Portal Login")

# --- INITIALIZE SESSION STATE ---
if "role" not in st.session_state:
    st.session_state["role"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

# --- LOGIN FORM ---
role = st.selectbox("Select Role", ["User", "Admin"])
user_id = st.text_input("User ID")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user = validate_user(user_id, password)
    if user:
        if role == "Admin" and user["user_id"].lower() == "admin":
            st.session_state["role"] = "Admin"
            st.session_state["user_id"] = user_id
            st.success("✅ Logged in as Admin")
        elif role == "User":
            st.session_state["role"] = "User"
            st.session_state["user_id"] = user_id
            st.success("✅ Logged in as User")
        else:
            st.error("🚫 Invalid role for this user!")
    else:
        st.error("❌ Invalid credentials!")

# --- ADMIN DASHBOARD ---
if st.session_state["role"] == "Admin":
    st.header("👨‍💼 Admin Dashboard")

    st.subheader("Create New User")
    new_id = st.text_input("New User ID")
    new_name = st.text_input("Full Name")
    new_pass = st.text_input("New Password", type="password")

    if st.button("Create User"):
        create_user(new_id, new_name, new_pass)

    st.subheader("📋 Registered Users")
    all_users = list(users_collection.find({}, {"_id": 0, "password": 0}))
    if all_users:
        st.dataframe(pd.DataFrame(all_users))
    else:
        st.info("No users found yet.")

# --- USER DASHBOARD ---
elif st.session_state["role"] == "User":
    st.header("📦 User Shipment Form")
    weight = st.number_input("Enter Package Weight (kg)", min_value=0.1)
    address = st.text_area("Enter Shipping Address")

    if st.button("Submit Shipment"):
        add_shipment(st.session_state["user_id"], weight, address)

    st.subheader("📜 Your Shipments")
    shipments = list(shipments_collection.find(
        {"user_id": st.session_state["user_id"]}, {"_id": 0}
    ))
    if shipments:
        st.dataframe(pd.DataFrame(shipments))
    else:
        st.info("No shipments yet.")

# --- LOGOUT ---
if st.session_state["role"] is not None:
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()  # ✅ Updated (not experimental)

