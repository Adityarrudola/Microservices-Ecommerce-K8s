import streamlit as st
import requests

# ✅ Internal service URLs (Kubernetes DNS)
AUTH_URL = "http://auth-service"
USER_URL = "http://user-service"
PRODUCT_URL = "http://product-service"
ORDER_URL = "http://order-service"

st.set_page_config(page_title="Microservices Dashboard", layout="wide")

st.title("🚀 Microservices Dashboard")

# ---------------- LOGIN ----------------
st.sidebar.header("🔐 Login")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    res = requests.post(
        f"{AUTH_URL}/login",
        json={"username": username, "password": password}
    )

    if res.status_code == 200:
        try:
            st.session_state.token = res.json()["token"]
            st.success("Logged in!")
        except:
            st.error("Invalid response from auth service")
            st.write(res.text)
    else:
        st.error(f"Login failed ({res.status_code})")
        st.write(res.text)

# ---------------- AUTH CHECK ----------------
if "token" not in st.session_state:
    st.warning("Please login first")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

# ---------------- LAYOUT ----------------
col1, col2 = st.columns(2)

# ---------------- USERS ----------------
with col1:
    st.subheader("👤 Users")

    if st.button("Get Users"):
        res = requests.get(f"{USER_URL}/users", headers=headers)

        if res.status_code == 200:
            try:
                st.json(res.json())
            except:
                st.write(res.text)
        else:
            st.error(f"Error {res.status_code}")
            st.write(res.text)

# ---------------- PRODUCTS ----------------
with col2:
    st.subheader("📦 Products")

    product_name = st.text_input("Product Name")
    price = st.number_input("Price", min_value=0)

    if st.button("Add Product"):
        res = requests.post(
            f"{PRODUCT_URL}/products",
            json={"name": product_name, "price": int(price)},
            headers=headers
        )

        if res.status_code == 200:
            try:
                st.json(res.json())
            except:
                st.write(res.text)
        else:
            st.error(f"Error {res.status_code}")
            st.write(res.text)

# ---------------- ORDERS ----------------
st.subheader("🛒 Orders")

user_id = st.number_input("User ID", min_value=1)
product_id = st.number_input("Product ID", min_value=1)

if st.button("Create Order"):
    res = requests.post(
        f"{ORDER_URL}/orders",
        json={"user_id": int(user_id), "product_id": int(product_id)},
        headers=headers
    )

    if res.status_code == 200:
        try:
            st.json(res.json())
        except:
            st.write(res.text)
    else:
        st.error(f"Error {res.status_code}")
        st.write(res.text)