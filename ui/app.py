import streamlit as st
import requests
from streamlit_option_menu import option_menu

# ---------------- CONFIG ----------------
AUTH_URL = "http://auth-service"
USER_URL = "http://user-service"
PRODUCT_URL = "http://product-service"
ORDER_URL = "http://order-service"

st.set_page_config(page_title="Microservices Hub", layout="wide", page_icon="🚀")

# ---------------- STYLING ----------------
st.markdown("""
<style>
.main { background-color: #0e1117; }
.stButton>button {
    width: 100%;
    border-radius: 6px;
    height: 3em;
    background-color: #ff4b4b;
    color: white;
}
.stTextInput>div>div>input { border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# ---------------- API HELPER ----------------
def api_request(method, url, token=None, data=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        if method == "GET":
            res = requests.get(url, headers=headers)
        else:
            res = requests.post(url, json=data, headers=headers)

        if res.status_code in [200, 201]:
            try:
                return True, res.json()
            except:
                return True, res.text
        else:
            return False, f"{res.status_code}: {res.text}"

    except Exception as e:
        return False, str(e)

# ---------------- LOGIN PAGE ----------------
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("🚀 Microservices Portal")

        tab1, tab2 = st.tabs(["Login", "Register"])

        # LOGIN
        with tab1:
            user = st.text_input("Username", key="login_user")
            pwd = st.text_input("Password", type="password", key="login_pwd")

            if st.button("Login"):
                success, res = api_request(
                    "POST",
                    f"{AUTH_URL}/login",
                    data={"username": user, "password": pwd}
                )

                if success:
                    st.session_state.token = res["token"]
                    st.session_state.username = res.get("username", user)
                    st.session_state.user_id = res.get("user_id")
                    st.rerun()
                else:
                    st.error(res)

        # REGISTER
        with tab2:
            new_user = st.text_input("New Username", key="reg_user")
            new_pwd = st.text_input("New Password", type="password", key="reg_pwd")

            if st.button("Register"):
                success, res = api_request(
                    "POST",
                    f"{AUTH_URL}/register",
                    data={"username": new_user, "password": new_pwd}
                )

                if success:
                    st.success("User created! Please login.")
                else:
                    st.error(res)

# ---------------- MAIN APP ----------------
def main_app():
    token = st.session_state.token
    username = st.session_state.username

    # NAVBAR
    selected = option_menu(
        menu_title=None,
        options=["Users", "Products", "Orders", "Logout"],
        icons=["people", "box-seam", "cart4", "box-arrow-right"],
        orientation="horizontal"
    )

    st.caption(f"Logged in as: **{username}**")

    # LOGOUT
    if selected == "Logout":
        st.session_state.clear()
        st.rerun()

    # ---------------- USERS ----------------
    if selected == "Users":
        st.header("👤 Users")

        if st.button("Refresh Users"):
            success, res = api_request("GET", f"{USER_URL}/users", token)

            if success:
                st.dataframe(res, use_container_width=True)
            else:
                st.error(res)

    # ---------------- PRODUCTS ----------------
    elif selected == "Products":
        st.header("📦 Products")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Add Product")

            name = st.text_input("Name")
            price = st.number_input("Price", min_value=0)

            if st.button("Create"):
                success, res = api_request(
                    "POST",
                    f"{PRODUCT_URL}/products",
                    token,
                    {"name": name, "price": int(price)}
                )

                if success:
                    st.success("Product added")
                else:
                    st.error(res)

        with col2:
            st.subheader("All Products")

            if st.button("Load Products"):
                success, res = api_request("GET", f"{PRODUCT_URL}/products", token)

                if success:
                    st.dataframe(res, use_container_width=True)
                else:
                    st.error(res)

    # ---------------- ORDERS ----------------
    elif selected == "Orders":
        st.header("🛒 Orders")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Create Order")

            # ❌ Removed user_id input
            product_id = st.number_input("Product ID", min_value=1)

            if st.button("Place Order"):
                success, res = api_request(
                    "POST",
                    f"{ORDER_URL}/orders",
                    token,
                    {"product_id": int(product_id)}   # ✅ FIX
                )

                if success:
                    st.success("Order created")
                    st.json(res)
                else:
                    st.error(res)

        with col2:
            st.subheader("Order History")

            if st.button("Load Orders"):
                success, res = api_request("GET", f"{ORDER_URL}/orders", token)

                if success:
                    st.dataframe(res, use_container_width=True)
                else:
                    st.error(res)

# ---------------- ROUTING ----------------
if "token" not in st.session_state:
    login_page()
else:
    main_app()