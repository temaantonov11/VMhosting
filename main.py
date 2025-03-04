import streamlit as st
import requests

st.title("Хостинг-провайдер")
type = st.selectbox(
    "Тип",
    ["Виртуалка", "Контейнер"]
)

if type == "Виртуалка":
    resource = st.selectbox("ОС для виртуалки", ["Ubuntu", "Fedora"])
else:  # Контейнер
    resource = st.selectbox("Образ для контейнера", ["Nginx", "Apache"])

ram = st.slider("Объём RAM (ГБ)", 1, 32, 4)
cpu = st.slider("Количество vCPU", 1, 16, 2)
disk = st.slider("Дисковое пространство (ГБ)", 10, 100, 15)

if st.button("Создать"):
    # payload = {"type": type, "resource": resourse}
    #response = requests.post("http://localhost:8000/create", json=payload)
    #st.write(response.json()["details"])
    pass
