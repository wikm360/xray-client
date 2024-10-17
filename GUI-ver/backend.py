import os
import json
import base64
import requests
import subprocess
import platform
from pathlib import Path
import convert
import shutil
import time
import re
import sys
import ctypes
import threading


class XrayBackend:
    def __init__(self):
        self.os_sys = self.os_det()
        self.xray_process = None
        self.singbox_process = None
        self.version = "4.0"
        self.xray_version = "1.8.24"
        self.log_callback = None
        self.close_event = threading.Event()

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
                config_json, config_name = convert.convert(config)
                if config_name != "False":
                    with open(f"./subs/{name}/{count}.json", "w") as f:
                        f.write(config_json)
                    dict_name[count] = config_name

        with open(f"./subs/{name}/list.json", "w", encoding="utf-8") as f:
            json.dump(dict_name, f, ensure_ascii=False, indent=4)
        with open(f"./subs/{name}/url.txt", "w", encoding="utf-8") as f:
            f.write(url)

    def update_subscription(self, profile):
        path = f"./subs/{profile}/url.txt"
        with open(path, "r") as f:
            url = f.read().strip()
        self.import_subscription(profile, url)

    def delete_subscription(self, profile):
        directory_path = f"./subs/{profile}"
        folder_path = Path(directory_path)
        if folder_path.exists() and folder_path.is_dir():
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    pass
                    # self.log(f"Error {file_path}: {e}")
            
            shutil.rmtree(directory_path)
            
            # self.log(f"Previous {profile} sub deleted")

    def ping_config(self, profile, config_num, ping_type):
        config_path = f"./subs/{profile}/{config_num}.json"
        
        if ping_type == "Tcping":
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                address = config['outbounds'][0]['settings']['vnext'][0]['address']
                ping_cmd = ['ping', '-n', '1', '-w', '1000', address] if self.os_sys == "win" else ['ping', '-c', '1', '-W', '1', address]
                
                if os.name == 'nt':
                    result = subprocess.Popen(ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    result = subprocess.Popen(ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = result.communicate()
                if result.returncode == 0:
                    time_p = stdout.split('time=')[1].split()[0]
                    return f"{time_p}"
                else:
                    return "Timeout"
                    
            except Exception as e:
                return f"Error: {str(e)}"

        elif ping_type == "Real-delay":
            if self.xray_process:
                self.stop_xray()

            self.run(config_path , "proxy")
            time.sleep(2)
            try:
                s_time = time.time()
                response = requests.get('http://gstatic.com/generate_204', proxies={"http": "http://127.0.0.1:1080"})
                e_time = time.time()
                if 200 <= response.status_code < 300:
                    delay_ms = (e_time - s_time) * 1000
                    return f"{delay_ms:.2f} ms"
                else:
                    return "Timeout"
            except :
                self.stop_xray()
                return f"Timeout"
            finally:
                self.stop_xray()

    def write_sing_box_config (self , dest) :
        def is_ip(address):
            ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
            return ip_pattern.match(address) is not None
        
        file_path = f"./core/{self.os_sys}/singbox-config.json"
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        if is_ip(dest):
            for rule in data['dns']['rules']:
                if 'domain' in rule:
                    del rule['domain']
            data['dns']['rules'] = [
                {
                    "server": "remote",
                    "clash_mode": "Global"
                },
                {
                    "server": "local_local",
                    "clash_mode": "Direct"
                }
            ]
        else :
            domain_found = False
            for rule in data['dns']['rules']:
                if 'domain' in rule:
                    rule['domain'] = [dest]
                    domain_found = True
                    break
            
            if not domain_found:
                data['dns']['rules'].insert(0, {
                    "server": "local_local",
                    "domain": [dest]
                })
        
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
        print("singbox-config write success")

    def run_tun(self , config_path) :
        with open(config_path, 'r') as file:
            data = json.load(file)
        dest = data['outbounds'][0]['settings']['vnext'][0]['address']
        
        self.write_sing_box_config(dest)

        try :
            singbox_path = f"./core/{self.os_sys}/sing-box"
            creation_flags = subprocess.CREATE_NO_WINDOW if self.os_sys == "win" else 0
            self.singbox_process = subprocess.Popen(
                [singbox_path, 'run', '-c', f'./core/{self.os_sys}/singbox-config.json'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creation_flags
            )
            self.log("Sing-box is running with config: ./singbox-config.json")
            threading.Thread(target=self.read_process_output, args=(self.singbox_process, "Sing-box"), daemon=True).start()
        except Exception as e :
            return f"Error starting Xray or Sing-box: {str(e)}"

    def run (self , connfig_path , type = "proxy") :
        def is_admin():
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False   
        
        def run_as_admin(argv=None):
            if argv is None:
                argv = sys.argv
            if hasattr(sys, '_MEIPASS'):
                # Support pyinstaller wrapped program.
                arguments = map(str, argv[1:])
            else:
                arguments = map(str, argv)
            argument_line = u' '.join(arguments)
            executable = sys.executable
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, argument_line, None, 1)
            return ret > 32
        
        if type == "tun" :
            if not is_admin() :
                print("Restarting with admin privileges...")
                if run_as_admin() :
                    self.log("Successfully restarted with admin privileges.")
                    self.close_event.set()
                    # os._exit(0)
                else :
                    self.log("Faild to start with Admin")
                    sys.exit(1)
                return "starting with Admin"
            else :
                self.log("Running with admin privileges.")
                self.run_xray(connfig_path)
                self.run_tun(connfig_path)
        else :
            self.run_xray(connfig_path)
                
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
            self.log("Xray is running with config: " + config_path)
            
            threading.Thread(target=self.read_process_output, args=(self.xray_process, "Xray"), daemon=True).start()

            return "Xray Running"
        
        except Exception as e:
            return f"Error starting Xray or Sing-box: {str(e)}"

    def read_process_output(self, process, name):
        for line in process.stdout:
            if line:
                self.log(f"{name}: {line.strip()}")
        for line in process.stderr:
            if line:
                self.log(f"{name} Error: {line.strip()}")

    def stop_xray(self):
        if self.xray_process:
            self.xray_process.terminate()
            self.xray_process = None
            self.log("Xray has been stopped.")
        if self.singbox_process:
            self.singbox_process.terminate()
            self.singbox_process = None
            self.log("Sing-box has been stopped.")
        return "Xray and Sing-box are not running."

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)