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
import random
import string
from const import *

class XrayBackend:
    def __init__(self):
        self.os_sys = OS_SYS
        self.xray_process = None
        self.singbox_process = None
        self.version = APP_VERSION
        self.xray_version = XRAY_VERSION
        self.log_callback = None
        self.close_event = threading.Event()
        self.useragant = lambda: json.load(open("./setting.json", "r"))["useragent"]

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
        if isinstance (url , str)  :
            if url.startswith("http"):
                useragent = str(self.useragant())
                headers = {"user-agent": useragent}
                r = requests.get(url=url, headers=headers)
                text = r.text
                if "[" in text :
                    #  custom
                    self.log("Custom config Detect ...")
                    data = r.json()
                    dict_name = {}
                    count = 0
                    for config in data :
                        directory_path = f"./subs/{name}"
                        Path(directory_path).mkdir(parents=True, exist_ok=True)

                        try :
                            del config["dns"]
                        except Exception as e:
                            self.log(f"Faild in delete dns Parse Json ...{e}")
                        try :
                            config["inbounds"][0]["port"] = 1080
                            config["inbounds"][1]["port"] = 1081
                        except Exception as e :
                            self.log(f"Faild in chenge port Json ...  {e}")
                        config_name = config["remarks"]
                        config_json = json.dumps(config , indent=4)

                        if config_name != "False":
                            with open(f"./subs/{name}/{count}.json", "w") as f:
                                f.write(config_json)
                            dict_name[count] = config_name
                            count += 1
                    with open(f"./subs/{name}/list.json", "w", encoding="utf-8") as f:
                        json.dump(dict_name, f, ensure_ascii=False, indent=4)
                    with open(f"./subs/{name}/url.txt", "w", encoding="utf-8") as f:
                        f.write(url)
                    
                else :    
                    decoded_bytes = base64.b64decode(text)
                    decoded_str = decoded_bytes.decode('utf-8')
                    list_configs = decoded_str.split("\n")

                    directory_path = f"./subs/{name}"
                    Path(directory_path).mkdir(parents=True, exist_ok=True)

                    dict_name = {}
                    for count, config in enumerate(list_configs):
                        if config.strip():
                            config_json, config_name = convert.convert(config)
                            if config_json == None :
                                continue
                            if config_name != "False":
                                with open(f"./subs/{name}/{count}.json", "w") as f:
                                    f.write(config_json)
                                dict_name[count] = config_name

                    with open(f"./subs/{name}/list.json", "w", encoding="utf-8") as f:
                        json.dump(dict_name, f, ensure_ascii=False, indent=4)
                    with open(f"./subs/{name}/url.txt", "w", encoding="utf-8") as f:
                        f.write(url)
            
            # one costum config
            elif "{" in url :
                if url.strip():
                    directory_path = f"./subs/{name}"
                    Path(directory_path).mkdir(parents=True, exist_ok=True)

                    data = json.loads(url)
                    try :
                        del data["dns"]
                    except Exception as e:
                        self.log(f"Faild in delete dns Parse Json ...{e}")
                    try :
                        data["inbounds"][0]["port"] = 1080
                        data["inbounds"][1]["port"] = 1081
                    except Exception as e :
                        self.log(f"Faild in chenge port Json ...  {e}")

                    def generate_random_word(length=8):
                        return ''.join(random.choices(string.ascii_letters, k=length))
                    
                    config_name = data.get("remarks", generate_random_word())
                    config_json = json.dumps(data , indent=4)

                    if config_name != "False":
                        with open(f"./subs/{name}/0.json", "w") as f:
                            f.write(config_json)
                with open(f"./subs/{name}/list.json", "w", encoding="utf-8") as f:
                    json.dump({0:config_name}, f, ensure_ascii=False, indent=4)
                with open(f"./subs/{name}/url.txt", "w", encoding="utf-8") as f:
                    f.write(url)

            #one vmess or vless config
            else  :
                config  = url
                directory_path = f"./subs/{name}"
                Path(directory_path).mkdir(parents=True, exist_ok=True)

                if config.strip():
                    config_json, config_name = convert.convert(config)
                    if config_json == None :
                        self.log("Config Not Support")
                    if config_name != "False":
                        with open(f"./subs/{name}/0.json", "w") as f:
                            f.write(config_json)
                with open(f"./subs/{name}/list.json", "w", encoding="utf-8") as f:
                    json.dump({0:config_name}, f, ensure_ascii=False, indent=4)
                with open(f"./subs/{name}/url.txt", "w", encoding="utf-8") as f:
                    f.write(url)

        else :
            self.log("URL not  String ...")

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

            self.run(config_path , "ping")
            time.sleep(1)
            try:
                s_time = time.time()
                try :
                    response = requests.get('http://gstatic.com/generate_204', proxies={"http": "http://127.0.0.1:1080"} , timeout=2)
                except requests.exceptions.Timeout:
                    return "Timeout"
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

    def remove_tun_interface(self):
        import wmi
        import pythoncom
        try:
            pythoncom.CoInitialize()
            c = wmi.WMI()
            
            for interface in c.Win32_NetworkAdapter():
                print(interface)
                if "wintun userspace tunnel" in interface.Name.lower():
                    interface.Disable()
                    return True
                    
            pythoncom.CoUninitialize()
        except Exception as e:
            print(f"Error: {e}")
            return False
        return False

    def run(self, config_path, type="proxy", sudo_password=None):
        def is_admin_windows():
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False
            
        def run_as_admin_windows(argv=None):
            if argv is None:
                argv = sys.argv
            if hasattr(sys, '_MEIPASS'):
                arguments = map(str, argv[1:])
            else:
                arguments = map(str, argv)
            argument_line = u' '.join(arguments)
            executable = sys.executable
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, argument_line, None, 1)
            return ret > 32

        def is_root_linux():
            return os.geteuid() == 0

        def run_as_root_linux(password):
            args = ['sudo', '-S'] + [sys.executable] + sys.argv
            env = os.environ.copy()
            try:
                process = subprocess.Popen(
                    args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    universal_newlines=True
                )
                stdout, stderr = process.communicate(input=password + '\n')
                if process.returncode == 0:
                    return True, "Successfully restarted with root privileges."
                else:
                    return False, f"Failed to start with root privileges. Error: {stderr}"
            except Exception as e:
                return False, f"Error occurred: {str(e)}"

        if type == "tun":
            if self.os_sys == "linux":
                if not is_root_linux():
                    if sudo_password is None:
                        return "Sudo password is required for TUN mode on Linux."
                    self.log("Rinning XC with Admin ...")
                    success, message = run_as_root_linux(sudo_password)
                    if success:
                        self.close_event.set()
                    return message
                else:
                    self.log("Running with root privileges.")
                    self.run_xray(config_path)
                    self.run_tun(config_path)
                    return "Successfully"
            elif self.os_sys == "win":
                if not is_admin_windows():
                    print("Restarting with admin privileges...")
                    if run_as_admin_windows():
                        self.log("Successfully restarted with admin privileges.")
                        # sys.exit(0)
                        self.close_event.set()
                    else:
                        self.log("Failed to start with Admin")
                        sys.exit(1)
                    return "starting with Admin"
                else :
                    self.run_xray(config_path)
                    self.run_tun(config_path)
                    return "Successfully"
            else:
                self.log("Unsupported OS for TUN mode")
                return "Unsupported OS for TUN mode"
        else:
            self.run_xray(config_path)
            if type == "proxy" :
                if OS_SYS == "win" :
                    self.set_system_proxy(PROXY_IP , PROXY_PORT)
                if OS_SYS == "linux" :
                    self.set_gnome_proxy(PROXY_IP , PROXY_PORT)

        return "Xray started successfully"
                
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

            return "Xray started successfully"
        
        except Exception as e:
            return f"Error starting Xray or Sing-box: {str(e)}"

    def run_tun(self , config_path) :
        if OS_SYS == "win" or OS_SYS == "win7" :
            r = self.remove_tun_interface()
            if r :
                self.log("previous interfaces Deleted  ...")
            else  :
                self.log("Interfaces Not Found to Delete")
        singbox_config_path = f'./core/{OS_SYS}/singbox-config.json'
        try:
            with open(singbox_config_path, "r") as file:
                data = json.load(file)

            interface_name = data["inbounds"][0]["interface_name"]

            match = re.match(r"tun(\d+)", interface_name)
            if match:
                current_number = int(match.group(1))
                new_number = current_number + 1
                new_interface_name = f"tun{new_number}"
            else:
                new_interface_name = "tun0"

            data["inbounds"][0]["interface_name"] = new_interface_name

            with open(singbox_config_path, "w") as file:
                json.dump(data, file, indent=4)

            self.log(f"TUN interface changed: {new_interface_name}")

        except FileNotFoundError:
            self.log(f"File Not Found : {singbox_config_path}")
        except KeyError as e:
            self.log(f"parametr not found : {e}")
        except json.JSONDecodeError:
            self.log("Error in Read JSON.")

        
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

    def read_process_output(self, process, name):
        for line in process.stdout:
            if line:
                self.log(f"{name}: {line.strip()}")
        for line in process.stderr:
            if line:
                self.log(f"{name} Error: {line.strip()}")

    def stop_xray(self):
        if OS_SYS == "win" :
            self.disable_system_proxy()
        if OS_SYS == "linux":
            self.disable_gnome_proxy()
        if self.xray_process:
            self.xray_process.terminate()
            self.xray_process = None
            self.log("Xray has been stopped.")
        if self.singbox_process:
            self.singbox_process.terminate()
            self.singbox_process = None
            self.log("Sing-box has been stopped.")
        return "Xray and Sing-box are not running."

    def set_system_proxy(self , proxy_ip, proxy_port):
        import winreg
        try:
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)

                proxy_value = f"{proxy_ip}:{proxy_port}"
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_value)

            self.log(f"Proxy set to {proxy_value} successfully.")
        except Exception as e:
            self.log(f"Error setting proxy: {e}")

    def disable_system_proxy(self):
        import winreg
        try:
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)

            self.log("Proxy disabled successfully")
        except Exception as e:
            self.log(f"Error disabling proxy: {e}")


    def set_gnome_proxy(self , proxy_ip, proxy_port):
        try:
            subprocess.run([
                "gsettings", "set", "org.gnome.system.proxy", "mode", "'manual'"
            ], check=True)
            subprocess.run([
                "gsettings", "set", "org.gnome.system.proxy.http", "host", f"'{proxy_ip}'"
            ], check=True)
            subprocess.run([
                "gsettings", "set", "org.gnome.system.proxy.http", "port", str(proxy_port)
            ], check=True)

            subprocess.run([
                "gsettings", "set", "org.gnome.system.proxy.https", "host", f"'{proxy_ip}'"
            ], check=True)
            subprocess.run([
                "gsettings", "set", "org.gnome.system.proxy.https", "port", str(proxy_port)
            ], check=True)

            subprocess.run([
                "gsettings", "set", "org.gnome.system.proxy", "ignore-hosts", "['']"
            ], check=True)

            self.log(f"Proxy set to {proxy_ip}:{proxy_port} successfully.")
        except Exception as e:
            self.log(f"Error setting proxy: {e}")

    def disable_gnome_proxy(self):
        try:
            subprocess.run([
                "gsettings", "set", "org.gnome.system.proxy", "mode", "'none'"
            ], check=True)
            self.log("Proxy disabled successfully")
        except Exception as e:
            self.log(f"Error disabling proxy: {e}")

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)