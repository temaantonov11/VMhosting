import streamlit as st
import subprocess
from datetime import datetime, timedelta
import json
import os
from QEMUManager import *


def load_containers():
    if os.path.exists("containers.json"):
        with open("containers.json", "r") as f:
            data = json.load(f)
            for info in data.values():
                info["start_time"] = datetime.fromisoformat(info["start_time"])
            return data
    return {}

def save_containers(containers):
    data = {k: {"image": v["image"], "start_time": v["start_time"].isoformat()} for k, v in containers.items()}
    with open("containers.json", "w") as f:
        json.dump(data, f)


containers = load_containers()
my_port = 8080

st.title("Хостинг-провайдер")
type = st.selectbox(
    "Тип",
    ["Виртуалка", "Контейнер"]
)

if type == "Виртуалка":
    resource = st.selectbox("ОС для виртуалки", ["Alpine"])
else:  # Контейнер
    resource = st.selectbox("Образ для контейнера", ["Nginx", "Apache"])
    my_port = st.slider("Порт для контейнера",8080,9000,8080)

name = st.text_input("Название VM: ")
ram = st.slider("Объём RAM (ГБ)", 1, 32, 1)
cpu = st.slider("Количество vCPU", 1, 16, 1)
disk = st.slider("Дисковое пространство (ГБ)", 1, 100, 1)
time_limit = st.slider("Лимит времени (минут)", 1, 60, 1)

if st.button("Создать"):
    if type == "Контейнер":
        image = resource.lower() 
        if image == "apache":
            image = "httpd"
        cmd = [
            "docker", "run", "-d", "-p", f"{my_port}:80",
            "--memory", f"{ram * 1024}m",
            "--cpus", str(cpu), image]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                container_id = result.stdout.strip()[:15]
                containers[container_id] = {"image": resource, "start_time": datetime.now()}
                save_containers(containers)
                st.write(f"Контейнер {resource} запущен! Доступ: http://localhost:{my_port}")
                st.write(f"ID контейнера: {container_id}")
            else:
                st.write(f"Ошибка: {result.stderr}")
        except FileNotFoundError:
            st.write("Ошибка: Docker не установлен или не найден")
    else:
        try: 
            if 'vm' not in st.session_state:
                st.session_state.vm = QEMUMananger()
            if 'vm_created' not in st.session_state:
                st.session_state.vm_created = False
            
            log.info(f"vm_created: {st.session_state.vm_created}")

            if not st.session_state.vm_created:
                st.session_state.vm.createVM(name, cpu, ram*1024, disk, "alpinelinux3.19.qcow2")
                st.session_state.vm_created = True
                st.write("VM создана")
            
            log.info(f"vm_created: {st.session_state.vm_created}")

            if st.session_state.vm_created:
                if 'ip' not in st.session_state:
                    ip = st.session_state.vm.getIP()
                st.write(f"IP адрес виртуальной машины: {ip}")
        except Exception as _ex:
            st.error(f"Error: {_ex}")

if st.session_state.get("vm_created", False):
        if st.button("Остановить VM"):
            try:
                st.session_state.vm.stopVM()
                st.session_state.vm_created = False
                st.write("VM остановлена")
            except Exception as _ex:
                st.error(f"Ошибка остановки VM: {_ex}")    
            

st.subheader("Список запущенных контейнеров")
if containers:
    for container_id, info in list(containers.items()):
        current_time = (datetime.now() - info["start_time"]).total_seconds() / 60
        st.write(f"ID: {container_id}, Образ: {info['image']}, Работает: {current_time:.1f} мин")
        
        if current_time > time_limit:
            try:
                subprocess.run(["docker", "stop", container_id], capture_output=True, text=True)
                subprocess.run(["docker", "rm", container_id], capture_output=True, text=True)
                del containers[container_id]
                save_containers(containers)
                st.write(f"Контейнер {container_id} остановлен: превышен лимит времени ({time_limit} мин)")
            except subprocess.CalledProcessError as e:
                st.write(f"Ошибка остановки {container_id}: {e.stderr}")
else:
    st.write("Нет запущенных контейнеров")

if containers:
    stop_id = st.selectbox("Выберите контейнер для остановки", list(containers.keys()))
    if st.button("Остановить"):
        try:
            subprocess.run(["docker", "stop", stop_id], capture_output=True, text=True)
            subprocess.run(["docker", "rm", stop_id], capture_output=True, text=True)
            del containers[stop_id]
            save_containers(containers)
            st.write(f"Контейнер {stop_id} остановлен вручную")
        except subprocess.CalledProcessError as e:
            st.write(f"Ошибка: {e.stderr}")