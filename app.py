import streamlit as st
import requests
import base64

st.title("🧠 Memoraid Face Recognition Demo")

image = st.camera_input("Capture Image")
if image:
    b64 = base64.b64encode(image.read()).decode()
    res = requests.post("http://127.0.0.1:8000/api/recognize", json={"image": b64})
    st.json(res.json())
