import streamlit as st
import subprocess
from datetime import datetime, timedelta
import json
import os
from QEMUManager import *
from DockerManager import *


docker_manager = DockerManager()


my_port = 8080
name = "my_vm"

st.title("Хостинг-провайдер")
type = st.selectbox(
    "Тип",
    ["Виртуалка", "Контейнер"]
)

if type == "Виртуалка":
    resource = st.selectbox("ОС для виртуалки", ["Alpine"])
    name = st.text_input("Название VM: ")
else:
    resource = st.selectbox("Образ для контейнера", ["Nginx", "Apache"])
    my_port = st.slider("Порт для контейнера",8080,9000,8080)


ram = st.slider("Объём RAM (ГБ)", 1, 32, 1)
cpu = st.slider("Количество vCPU", 1, 16, 1)
disk = st.slider("Дисковое пространство (ГБ)", 1, 100, 1)
time_limit = st.slider("Лимит времени (минут)", 1, 60, 1)

if st.button("Создать"):
    if type == "Контейнер":
        container_id, message = docker_manager.create_container(resource, my_port, ram, cpu, time_limit)
        st.write(message)
        if container_id:
            st.write(f"ID контейнера: {container_id}")
    else:
        try: 
            if 'vm' not in st.session_state:
                st.session_state.vm = QEMUMananger()
            if 'vm_created' not in st.session_state:
                st.session_state.vm_created = False

            if not st.session_state.vm_created:
                st.session_state.vm.createVM(name, cpu, ram*1024, disk, "alpinelinux3.19.qcow2")
                st.session_state.vm_created = True
                st.write("VM создана")
                
            if st.session_state.vm_created:
                ip = st.session_state.vm.getIP()
                st.write(f"IP адрес виртуальной машины: {ip}")
            if st.session_state.vm_created:
                if st.button("Остановить VM"):
                    st.write("VM остановлена")
                    st.session_state.vm.stopVM()
                    st.session_state.vm_created = False
        except Exception as _ex:
            st.error(f"Error: {_ex}")
            

st.subheader("Список запущенных контейнеров")
if docker_manager.containers:
    for container_id, info in list(docker_manager.containers.items()):
        current_time = (datetime.now() - info["start_time"]).total_seconds() / 60
        st.write(f"ID: {container_id}, Образ: {info['image']}, Работает: {current_time:.1f} мин, Порт: {info['port']}")
        
        if current_time > info["time_limit"]:
            id, message = docker_manager.stop_container(container_id)
            if id:
                st.write(f"{message}, превышен лимит времени ({time_limit} мин)")
            else:
                st.write(message)
else:
    st.write("Нет запущенных контейнеров")

if docker_manager.containers:
    stop_id = st.selectbox("Выберите контейнер для остановки", list(docker_manager.containers.keys()))
    if st.button("Остановить"):
        id, message = docker_manager.stop_container(container_id)
        if id:
            st.write(f"{message} вручную")
        else:
            st.write(message)