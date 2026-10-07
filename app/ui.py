import os
import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Kestrel Returns Risk", layout="centered")
st.title("Kestrel Returns Risk")
st.caption("Enter an order before dispatch to see how likely it is to be returned.")

with st.form("order"):
    c1, c2 = st.columns(2)
    order_id = c1.text_input("Order ID", "DEMO-0001")
    placed = c2.text_input("Order placed at", "2026-07-01 10:30")
    customer_id = c1.text_input("Customer ID", "KC100001")
    sku = c2.text_input("SKU", "KH-RH-01")
    channel = c1.selectbox("Sales channel", ["app", "web", "marketplace", "partner_outlet"])
    payment = c2.selectbox("Payment mode", ["prepaid_upi", "prepaid_card", "cod", "emi"], index=2)
    discount = c1.number_input("Discount %", 0.0, 100.0, 15.0)
    qty = c2.number_input("Quantity", 1, 50, 1)
    value = c1.number_input("Order value (Rs)", 0.0, 1_000_000.0, 3000.0)
    days = c2.number_input("Promised delivery days", 0, 60, 6)
    pincode = c1.number_input("Delivery pincode (0 if none)", 0, 999999, 440001)
    gift = c2.selectbox("Gift", ["N", "Y"])
    prior_orders = c1.number_input("Customer prior orders", 0, 500, 3)
    prior_returns = c2.number_input("Customer prior returns", 0, 500, 2)
    go = st.form_submit_button("Predict")

if go:
    payload = {"order_id": order_id, "order_placed_at": placed, "customer_id": customer_id, "sku": sku,
               "sales_channel": channel, "payment_mode": payment, "discount_pct": discount, "qty": int(qty),
               "order_value_inr": value, "promised_delivery_days": int(days), "delivery_pincode": int(pincode),
               "is_gift": gift, "customer_prior_orders": int(prior_orders), "customer_prior_returns": int(prior_returns)}
    try:
        r = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
        data = r.json()
    except requests.exceptions.RequestException:
        st.error("The prediction service is not reachable. Start the API and try again.")
        st.stop()
    except ValueError:
        st.error("The service returned an unexpected response.")
        st.stop()
    if r.status_code != 200:
        st.error(data.get("error", "Something went wrong."))
        st.stop()
    st.subheader("Return risk")
    st.metric("Probability of return", f"{data['return_probability']:.0%}")
    st.write(f"Risk level: **{data['risk_level']}**")
    action = "Call the customer to confirm before dispatch" if data["decision"] == "CALL_BEFORE_DISPATCH" else "Dispatch normally"
    st.write(f"Recommended action: **{action}**")
    st.write("Why:")
    for reason in data["reasons"]:
        st.write(f"- {reason}")
