import os
import json
import base64
import requests
import subprocess
import threading
import platform
from pathlib import Path


class XrayBackend:
    def __init__(self):
        self.os_sys = self.os_det()
        self.xray_process = None
        self.version = "3.0"  # Update this with your actual version

    def os_det(self):
        system_os = platform.system()
        if system_os == "Windows":
            return "win"
        elif system_os == "Linux":
            return "linux"
        elif system_os == "Darwin":
            return "macos"

    def get_system_info(self):
        return {
            "OS": platform.system(),
            "OS Version": platform.version(),
            "Machine": platform.machine(),
            "Processor": platform.processor()
        }

    def get_profiles(self):
        profiles = []
        path = "./subs"
        if os.path.exists(path):
            for sub in os.listdir(path):
                if os.path.isdir(os.path.join(path, sub)):
                    profiles.append(sub)
        return profiles

    def get_configs(self, profile):
        configs = []
        path_json = f"./subs/{profile}/list.json"
        if os.path.exists(path_json):
            with open(path_json, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
            for key, value in data.items():
                configs.append(f"{key} - {value}")
        return configs

    def import_subscription(self, name, url):
        headers = {"user-agent": "XC(Xray-Client)"}
        r = requests.get(url=url, headers=headers)
        text = r.text
        decoded_bytes = base64.b64decode(text)
        decoded_str = decoded_bytes.decode('utf-8')
        list_configs = decoded_str.split("\n")

        directory_path = f"./subs/{name}"
        Path(directory_path).mkdir(parents=True, exist_ok=True)

        dict_name = {}
        for count, config in enumerate(list_configs):
            if config.strip():
                config_json, config_name = self.convert(config)
                if config_name != "False":
                    with open(f"./subs/{name}/{count}.json", "w") as f:
                        f.write(config_json)
                    dict_name[count] = config_name

        with open(f"./subs/{name}/list.json", "w", encoding="utf-8") as f:
            json.dump(dict_name, f, ensure_ascii=False, indent=4)
        with open(f"./subs/{name}/url.txt", "w", encoding="utf-8") as f:
            f.write(url)

    def convert(self, config):
        # Implement your conversion logic here
        # This is a placeholder implementation
        return json.dumps({"config": config}), "Config Name"

    def update_subscription(self, profile):
        path = f"./subs/{profile}/url.txt"
        with open(path, "r") as f:
            url = f.read().strip()
        self.import_subscription(profile, url)

    def delete_subscription(self, profile):
        directory_path = f"./subs/{profile}"
        os.system(f"rm -rf {directory_path}")

    def ping_config(self, profile, config_num):
        config_path = f"./subs/{profile}/{config_num}.json"
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            address = config['outbounds'][0]['settings']['vnext'][0]['address']
            ping_cmd = ['ping', '-n', '1', '-w', '1000', address] if self.os_sys == "win" else ['ping', '-c', '1', '-W', '1', address]
            result = subprocess.run(ping_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                time = result.stdout.split('time=')[1].split()[0]
                return f"{time}ms"
            else:
                return "Timeout"
        except Exception as e:
            return f"Error: {str(e)}"

    def run_xray(self, config_path):
        try:
            xray_path = f"./core/{self.os_sys}/xray"
            creation_flags = subprocess.CREATE_NO_WINDOW if self.os_sys == "win" else 0
            self.xray_process = subprocess.Popen(
                [xray_path, '-config', config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creation_flags
            )
            return f"Xray is running with config: {config_path}"
        except Exception as e:
            return f"Error starting Xray: {str(e)}"

    def stop_xray(self):
        if self.xray_process:
            self.xray_process.terminate()
            self.xray_process = None
            return "Xray has been stopped."
        return "Xray is not running."

    def read_xray_logs(self):
        while self.xray_process:
            output = self.xray_process.stdout.readline()
            if output == '' and self.xray_process.poll() is not None:
                break
            if output:
                yield output.strip()