import subprocess
import json
import os
from datetime import datetime

class DockerManager:
    def __init__(self, containers_file="containers.json"):
        self.containers_file = containers_file
        self.containers = self.load_containers()

    def load_containers(self):
        if os.path.exists(self.containers_file):
            with open(self.containers_file, "r") as f:
                data = json.load(f)
                for info in data.values():
                    info["start_time"] = datetime.fromisoformat(info["start_time"])
                return data
        return {}

    def save_containers(self):
        data = {}
        for k, v in self.containers.items():
            data[k] = {
                "image": v["image"],
                "start_time": v["start_time"].isoformat(),
                "port": v["port"],
                "time_limit": v["time_limit"]}
            
        with open(self.containers_file, "w") as f:
            json.dump(data, f)

    def create_container(self, image, port, ram, cpu, time_limit):
        image = image.lower()
        if image == "apache":
            image = "httpd"
        cmd = [
            "docker",
            "run",
            "-d",
            "-p",
            f"{port}:80",
            "--memory",
            f"{ram * 1024}m",
            "--cpus",
            str(cpu),
            image,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                container_id = result.stdout.strip()[:15]
                self.containers[container_id] = {
                    "image": image,
                    "start_time": datetime.now(),
                    "port": port,
                    "time_limit": time_limit,
                }
                self.save_containers()
                return container_id, f"Контейнер {image} запущен! Доступ: http://localhost:{port}"
            else:
                return None, f"Ошибка: {result.stderr}"
        except FileNotFoundError:
            return None, "Ошибка: Docker не установлен или не найден"

    def stop_container(self, container_id):
        try:
            subprocess.run(["docker", "stop", container_id], capture_output=True, text=True)
            subprocess.run(["docker", "rm", container_id], capture_output=True, text=True)
            del self.containers[container_id]
            self.save_containers()
            return container_id, f"Контейнер {container_id} остановлен"
        except subprocess.CalledProcessError as e:
            return None, f"Ошибка остановки: {e.stderr}"

