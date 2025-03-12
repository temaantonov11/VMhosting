import streamlit as st
import subprocess
from datetime import datetime, timedelta
import json
import os
from QEMUManager import *
from DockerManager import *
import threading


docker_manager = DockerManager()


my_port = 8080
name = "my_vm"

def stop_vm_after_timeLimit(vm, time_limit):
    time.sleep(time_limit * 60)
    try:
        vm.stopVM()
        st.wirte(f"VM остановлена по истечению времени лимита ({time_limit}минут)")
    except Exception as _ex:
        log.error("Failed stop with time limit")

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
            
            log.info(f"vm_created: {st.session_state.vm_created}")

            if not st.session_state.vm_created:
                st.session_state.vm.createVM(name, cpu, ram*1024, disk, "alpinelinux3.19.qcow2")
                st.session_state.vm_created = True
                st.write("VM создана")
            

            log.info(f"vm_created: {st.session_state.vm_created}")

           
        except Exception as _ex:
            st.error(f"Error: {_ex}")

if st.session_state.get("vm_created", False):
    
    st.subheader("Управление VM")
    
    if 'ip' not in st.session_state:
        ip = st.session_state.vm.getIP()
        st.write(f"IP адрес виртуальной машины: {ip}")
     
    stop_thread = threading.Thread(
                target=stop_vm_after_timeLimit,
                args=(st.session_state.vm, time_limit)
                )
    stop_thread.daemon = True
    stop_thread.start()
    
             
    if 'start_time' not in st.session_state:
        st.session_state.start_time = datetime.now()

    
    if st.button("Обновить информацию о VM"):

        elapsed_time = (datetime.now() - st.session_state.start_time).total_seconds() / 60
        remaining_time = max(0, time_limit - elapsed_time)
        st.write(f"Оставшееся время до остановки VM: {remaining_time:.1f} минут")

        cpu_load = st.session_state.vm.get_cpu_usage()
        memory_usage = st.session_state.vm.get_memory_usage()
        disk_usage = st.session_state.vm.get_disk_usage()

        if cpu_load is not None:
            st.write(f"Нагрузка на CPU: {cpu_load} ns")
        if memory_usage is not None:
            st.write(f"Использование RAM: {memory_usage:.2f} MB")
        if disk_usage is not None:
            read_bytes, write_bytes = disk_usage
            st.write(f"Использовано диска: Прочитано {read_bytes} байт, Записано {write_bytes} байт")
    
    if st.button("Остановить VM"):
        try:
            st.session_state.vm.stopVM()
            st.session_state.vm_created = False
            st.write("VM остановлена")
        except Exception as _ex:
            st.error(f"Ошибка остановки VM: {_ex}")    
          

st.subheader("Список запущенных контейнеров")
if docker_manager.containers:
    for container_id, info in list(docker_manager.containers.items()):
        current_time = (datetime.now() - info["start_time"]).total_seconds() / 60
        st.write(f"ID: {container_id}, Образ: {info['image']}, Работает: {current_time:.1f} мин, Порт: {info['port']}")
        
        if current_time > info["time_limit"]:
            id, message = docker_manager.stop_container(container_id)
            if id:
                st.write(f"{message}, превышен лимит времени ({info["time_limit"]} мин)")
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