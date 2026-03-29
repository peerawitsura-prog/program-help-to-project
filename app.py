import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Research Platform", layout="centered")
st.title("🧪 Advanced Research Platform")
st.write("Formulation + UV-Vis + AI + Kinetics + Soil + Database")

# ================= DATABASE =================
conn = sqlite3.connect("research.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS experiments (
id INTEGER PRIMARY KEY AUTOINCREMENT,
date TEXT,
pbsa REAL,
lignin REAL,
release TEXT
)""")
conn.commit()

# ================= UV-VIS =================
st.header("🟢 UV-Vis Calibration")

cal_data = st.text_area("Calibration (ppm,abs)",
"""1,0.1
2,0.22
3,0.35
4,0.48
5,0.60""")

if st.button("Generate Calibration"):
    lines = cal_data.split("\n")
    conc, absorb = [], []

    for l in lines:
        c1, a1 = l.split(",")
        conc.append(float(c1))
        absorb.append(float(a1))

    conc = np.array(conc)
    absorb = np.array(absorb)

    m, b = np.polyfit(conc, absorb, 1)

    st.session_state["m"] = m
    st.session_state["b"] = b

    st.write(f"Equation: A = {m:.4f}C + {b:.4f}")

# ================= RELEASE =================
st.header("🔴 Release Data")

data = st.text_area("Time(hr),Abs",
"""1,0.2
2,0.35
3,0.5""")

V = st.number_input("Volume (mL)", value=20.0)
m_fert = st.number_input("Fertilizer mass (g)", value=0.07)

if st.button("Calculate Release") and "m" in st.session_state:

    time, release = [], []

    for l in data.split("\n"):
        t, a = l.split(",")
        t = float(t)
        a = float(a)

        C = (a - st.session_state["b"]) / st.session_state["m"]
        R = (C * V / m_fert) * 100

        time.append(t)
        release.append(R)

    df = pd.DataFrame({"Time": time, "Release": release})
    st.dataframe(df)

    # plot
    fig, ax = plt.subplots()
    ax.plot(time, release, marker='o')
    ax.set_xlabel("Time")
    ax.set_ylabel("% Release")
    st.pyplot(fig)

    st.session_state["release"] = df

# ================= KINETICS =================
st.header("⚡ Kinetics Fitting")

if "release" in st.session_state:

    df = st.session_state["release"]
    t = np.array(df["Time"])
    R = np.array(df["Release"])

    # Zero order
    m0, b0 = np.polyfit(t, R, 1)
    pred0 = m0*t + b0
    r2_0 = 1 - np.sum((R-pred0)**2)/np.sum((R-np.mean(R))**2)

    # First order
    lnR = np.log(R + 1e-6)
    m1, b1 = np.polyfit(t, lnR, 1)
    pred1 = np.exp(m1*t + b1)
    r2_1 = 1 - np.sum((R-pred1)**2)/np.sum((R-np.mean(R))**2)

    st.write(f"Zero-order R² = {r2_0:.4f}")
    st.write(f"First-order R² = {r2_1:.4f}")

# ================= AI PREDICTION =================
st.header("🤖 AI Predict Release")

pbsa_input = st.number_input("PBSA (%)", value=30.0)
lignin_input = st.number_input("Lignin (%)", value=10.0)

if st.button("Predict"):

    # simple regression assumption
    time = np.linspace(0, 30, 20)
    rate = 0.5 + (lignin_input/20)

    pred = 100*(1-np.exp(-rate*time/30))

    fig, ax = plt.subplots()
    ax.plot(time, pred)
    ax.set_xlabel("Time")
    ax.set_ylabel("% Release")
    st.pyplot(fig)

# ================= CONDUCTIVITY =================
st.header("🟡 Conductivity")

cond_data = st.text_area("Time,Conductivity",
"""1,100
2,150
3,200""")

if st.button("Plot Conductivity"):

    t, cval = [], []

    for l in cond_data.split("\n"):
        a, b = l.split(",")
        t.append(float(a))
        cval.append(float(b))

    fig, ax = plt.subplots()
    ax.plot(t, cval, marker='o')
    ax.set_xlabel("Time")
    ax.set_ylabel("Conductivity")
    st.pyplot(fig)

# ================= SOIL =================
st.header("🟤 Soil Degradation")

soil_data = st.text_area("Day,Score(0-5)",
"""1,0
3,1
7,2""")

if st.button("Plot Soil"):

    d, s = [], []

    for l in soil_data.split("\n"):
        a, b = l.split(",")
        d.append(float(a))
        s.append(float(b))

    fig, ax = plt.subplots()
    ax.plot(d, s, marker='o')
    ax.set_xlabel("Day")
    ax.set_ylabel("Degradation Score")
    st.pyplot(fig)

# ================= SAVE =================
st.header("💾 Save Experiment")

if st.button("Save to Database") and "release" in st.session_state:

    c.execute("INSERT INTO experiments (date, pbsa, lignin, release) VALUES (?,?,?,?)",
              (str(datetime.now()), pbsa_input, lignin_input,
               st.session_state["release"].to_json()))
    conn.commit()

    st.success("Saved!")

# ================= VIEW =================
st.header("📊 Database")

rows = c.execute("SELECT * FROM experiments").fetchall()

for r in rows:
    st.write(r)
