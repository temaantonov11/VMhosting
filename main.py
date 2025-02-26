import streamlit
import requests

streamlit.title("Хостинг-провайдер")
type = streamlit.selectbox("Тип", ["Виртуалка", "Контейнер"])
resourse = ''
if type == "Виртуалка":
    resourse = streamlit.selectbox("ОС для виртуалки", ["Ubuntu", "Fedora"])
else:  # Контейнер
    resourse = streamlit.selectbox("Образ для контейнера", ["Nginx", "Apache"])

if streamlit.button("Создать"):
    payload = {"type": type, "resource": resourse}
    #response = requests.post("http://localhost:8000/create", json=payload)
    #st.write(response.json()["details"])
