
import math
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SmartRation AI", page_icon="🍱", layout="wide")

# -----------------------------
# SmartRation AI — hackathon MVP
# Decision chain: Predict → Prepare → Buy → Risk → Act → Learn
# -----------------------------

RECIPES = {
    "Rice": {"unit":"kg", "per_meal":0.055, "price":55, "shelf_days":30},
    "Vegetables": {"unit":"kg", "per_meal":0.0735, "price":70, "shelf_days":7},
    "Curd": {"unit":"kg", "per_meal":0.0506, "price":85, "shelf_days":5},
    "Oil": {"unit":"L", "per_meal":0.0098, "price":135, "shelf_days":90},
}
DEFAULT_STOCK = {
    "Rice": 20.0, "Vegetables": 14.0, "Curd": 12.0, "Oil": 3.0
}
DEFAULT_INCOMING = {
    "Rice": 8.0, "Vegetables": 5.0, "Curd": 0.0, "Oil": 2.0
}
DEFAULT_EXPIRY_DAYS = {
    "Rice": 30, "Vegetables": 3, "Curd": 2, "Oil": 70
}

def round_up_pack(qty, pack):
    return math.ceil(max(0, qty) / pack) * pack if pack > 0 else max(0, qty)

def forecast(attendance, weekend, event, trend, recent_actuals):
    base = max(1, attendance * 0.92)
    weekend_factor = 1.07 if weekend else 1.0
    event_factor = 1.12 if event else 1.0
    trend_factor = 1 + trend / 100
    history = np.array(recent_actuals, dtype=float)
    hist_factor = np.mean(history[-3:]) / np.mean(history) if len(history) >= 3 and np.mean(history) else 1.0
    demand = base * weekend_factor * event_factor * trend_factor * hist_factor
    confidence = "HIGH" if len(history) >= 7 and np.std(history) / np.mean(history) < 0.12 else "MEDIUM"
    return int(round(demand)), confidence

def decision_chain(demand, buffer_pct, stock, incoming, expiry_days, attendance_delta=0):
    # Preparation
    prepared = int(math.ceil(demand * (1 + buffer_pct/100)))
    rows = []
    total_purchase = 0.0
    total_risk = 0.0

    for item, spec in RECIPES.items():
        required = prepared * spec["per_meal"]
        usable = stock[item]
        inbound = incoming[item]
        need = max(0, required - usable - inbound)

        pack = {"Rice": 5, "Vegetables": 5, "Curd": 2, "Oil": 1}[item]
        purchase = round_up_pack(need, pack)
        leftover = max(0, usable - required)

        expiry_risk = 0.0
        if expiry_days[item] <= 3 and leftover > 0:
            expiry_risk = leftover * spec["price"]
        slow_risk = leftover * spec["price"] * 0.25 if leftover > 0 else 0
        money_risk = expiry_risk + slow_risk

        if expiry_days[item] <= 2 and leftover > 0:
            action = "USE FIRST / REVIEW"
        elif purchase > 0:
            action = "BUY NOW"
        elif leftover > required * 0.35:
            action = "DO NOT BUY"
        else:
            action = "MONITOR"

        total_purchase += purchase * spec["price"]
        total_risk += money_risk

        rows.append({
            "Item": item,
            "Required": round(required,2),
            "Usable stock": round(usable,2),
            "Incoming": round(inbound,2),
            "Purchase": round(purchase,2),
            "Expiry days": expiry_days[item],
            "Money at risk": round(money_risk,0),
            "Action": action
        })
    return prepared, pd.DataFrame(rows), total_purchase, total_risk

if "history" not in st.session_state:
    st.session_state.history = []
if "approved" not in st.session_state:
    st.session_state.approved = []

st.title("🍱 SmartRation AI")
st.caption("AI-powered Demand, Inventory & Decision Intelligence • Predict → Prepare → Buy → Risk → Act → Learn")

with st.sidebar:
    st.header("Scenario")
    attendance = st.slider("Expected attendance", 100, 1000, 540, 10)
    weekend = st.toggle("Weekend", True)
    event = st.toggle("College event", True)
    trend = st.slider("Recent demand trend (%)", -20, 30, 3)
    buffer_pct = st.slider("Preparation buffer (%)", 0, 15, 3)
    st.divider()
    st.subheader("What-if")
    attendance_delta = st.slider("Attendance change (%)", -30, 40, 0)
    supplier_delay = st.toggle("Supplier delayed")
    extra_stock = st.slider("Extra usable stock (kg/L equivalent)", 0, 50, 0)

# Synthetic recent history, intentionally visible as demo data
recent = [480, 495, 510, 505, 470, 500, 515, 490, 505, 520]
demand, confidence = forecast(
    attendance * (1 + attendance_delta/100),
    weekend, event, trend, recent
)

stock = DEFAULT_STOCK.copy()
incoming = DEFAULT_INCOMING.copy()
expiry = DEFAULT_EXPIRY_DAYS.copy()

if supplier_delay:
    incoming = {k: v*0.35 for k,v in incoming.items()}
for k in stock:
    stock[k] += extra_stock / len(stock)

prepared, plan, purchase_value, risk_value = decision_chain(
    demand, buffer_pct, stock, incoming, expiry, attendance_delta
)

# Top KPIs
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Expected meals", f"{demand:,}", f"{confidence} confidence")
c2.metric("Prepare", f"{prepared:,} meals")
c3.metric("Buy", f"₹{purchase_value:,.0f}")
c4.metric("Money at risk", f"₹{risk_value:,.0f}")
c5.metric("Open actions", str((plan["Action"] != "MONITOR").sum()))

st.divider()

tabs = st.tabs(["🧠 Decision Center", "📦 Preparation & Procurement", "⚠️ Risk", "🔮 What-if", "🧾 Approval & Learning"])

with tabs[0]:
    st.subheader("SmartRation Decision Graph")
    st.markdown("**DEMAND → PREPARE → BUY → RISK → ACTION → LEARN**")
    st.info(
        f"Forecast: **{demand} meals**. The model increased demand because of "
        f"{'weekend' if weekend else 'weekday'}, {'event' if event else 'no event'}, and a {trend}% trend."
    )
    st.dataframe(plan[["Item","Purchase","Money at risk","Action","Expiry days"]], use_container_width=True, hide_index=True)

    actions = []
    for _, r in plan.iterrows():
        if r["Action"] == "BUY NOW":
            actions.append(f"🛒 Buy **{r['Purchase']} {RECIPES[r['Item']]['unit']} {r['Item']}**")
        elif r["Action"] == "USE FIRST / REVIEW":
            actions.append(f"⏳ Use **{r['Item']}** first — expiry is approaching")
        elif r["Action"] == "DO NOT BUY":
            actions.append(f"🛑 Do not reorder **{r['Item']}** — stock is sufficient")
    st.subheader("Daily AI Action Center")
    for a in actions or ["✅ No urgent action. Monitor the plan."]:
        st.markdown(a)

with tabs[1]:
    st.subheader("Preparation Intelligence")
    st.write(f"Expected demand × recipe/BOM × operating buffer = **{prepared} meals planned**")
    st.dataframe(plan[["Item","Required","Usable stock","Incoming","Purchase"]], use_container_width=True, hide_index=True)
    st.subheader("Procurement logic")
    st.code("Purchase Need = Requirement − Usable Current Stock − Confirmed Incoming")
    st.caption("Pack-size constraints are applied to avoid fractional purchases.")

with tabs[2]:
    st.subheader("Inventory Risk & Money-at-Risk")
    risk_table = plan[["Item","Expiry days","Money at risk","Action"]].copy()
    st.dataframe(risk_table, use_container_width=True, hide_index=True)
    if risk_value:
        st.warning(f"Potential exposure in this demo scenario: ₹{risk_value:,.0f}. This is an illustrative model output, not a measured saving.")
    else:
        st.success("No material expiry/slow-moving exposure detected in this scenario.")
    st.caption("Food-safety rules must override automated actions. Expiry is never treated as an automatic discount signal.")

with tabs[3]:
    st.subheader("What-if Simulator")
    st.write("Change one assumption and the decision chain propagates.")
    col1,col2 = st.columns(2)
    with col1:
        st.metric("Current forecast", f"{demand} meals")
        st.metric("Current purchase value", f"₹{purchase_value:,.0f}")
    with col2:
        alt_att = attendance * (1 + attendance_delta/100)
        alt_demand, alt_conf = forecast(alt_att, weekend, event, trend, recent)
        alt_prepared, alt_plan, alt_purchase, alt_risk = decision_chain(alt_demand, buffer_pct, stock, incoming, expiry, attendance_delta)
        st.metric("What-if forecast", f"{alt_demand} meals", f"{alt_demand-demand:+d}")
        st.metric("What-if purchase value", f"₹{alt_purchase:,.0f}", f"₹{alt_purchase-purchase_value:+,.0f}")
    st.dataframe(alt_plan[["Item","Purchase","Money at risk","Action"]], use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("Explainable AI + Human Approval")
    st.write("The AI recommends. The operator stays in control.")
    recommendation = "Maintain current preparation plan"
    reason = "Demand signals are balanced."
    if demand < attendance * 0.88:
        recommendation = "Reduce tomorrow's preparation"
        reason = "Recent demand is below attendance-adjusted baseline."
    elif demand > attendance * 0.98:
        recommendation = "Increase tomorrow's preparation"
        reason = "Attendance, event and trend signals indicate higher demand."
    st.success(f"**Recommendation:** {recommendation}")
    st.write(f"**Why:** {reason}")
    st.write(f"**Confidence:** {confidence.title()}")
    b1,b2,b3 = st.columns(3)
    if b1.button("✓ APPROVE", use_container_width=True):
        st.session_state.approved.append({"decision": recommendation, "forecast": demand, "status":"Approved"})
        st.success("Decision approved and logged.")
    if b2.button("✎ EDIT", use_container_width=True):
        st.session_state.approved.append({"decision": "Edited by operator", "forecast": demand, "status":"Edited"})
        st.info("Edited decision logged.")
    if b3.button("× REJECT", use_container_width=True):
        st.session_state.approved.append({"decision": recommendation, "forecast": demand, "status":"Rejected"})
        st.warning("Recommendation rejected and logged.")

    st.subheader("Learning Loop")
    actual = st.number_input("Enter actual meals served", min_value=0, max_value=2000, value=max(0, demand-30), step=10)
    if st.button("Record actual outcome"):
        error = actual - demand
        st.session_state.history.append({"Predicted": demand, "Actual": actual, "Error": error, "Context": f"weekend={weekend}, event={event}"})
        st.success(f"Outcome recorded. Forecast error = {error:+d} meals.")
    if st.session_state.history:
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True, hide_index=True)

st.divider()
st.caption("SmartRation AI • ZEPHYR 2026 • Prototype / demo data • Safety and business rules remain authoritative.")
