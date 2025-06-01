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
from collections import deque

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
        self._process_output_buffer = deque(maxlen=100)
        self._output_lock = threading.Lock()
        self.xray_path = XRAY_PATH  # Path to xray executable
        self.server = API        # Xray API server address
        self._last_bytes_sent = 0   # Last recorded upload bytes
        self._last_bytes_recv = 0   # Last recorded download bytes
        self._last_traffic_check = time.time()  # Last time traffic was checked

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
        def add_api_stats_config(config):
            """Add API, stats and policy settings to config if missing"""
            base_additions = {
                "api": {
                    "tag": "api",
                    "services": ["HandlerService", "LoggerService", "StatsService"]
                },
                "stats": {},
                "policy": {
                    "levels": {
                        "0": {
                            "statsUserUplink": True,
                            "statsUserDownlink": True
                        }
                    },
                    "system": {
                        "statsInboundUplink": True,
                        "statsInboundDownlink": True,
                        "statsOutboundUplink": True,
                        "statsOutboundDownlink": True
                    }
                }
            }

            # Add API inbound if missing
            api_inbound = {
                "tag": "api",
                "port": 10085,
                "listen": "127.0.0.1", 
                "protocol": "dokodemo-door",
                "settings": {
                    "address": "127.0.0.1"
                }
            }

            if "inbounds" not in config:
                config["inbounds"] = []
            
            if not any(inb.get("tag") == "api" for inb in config["inbounds"]):
                config["inbounds"].append(api_inbound)

            # Add other base components if missing
            for key, value in base_additions.items():
                if key not in config:
                    config[key] = value

            # Add API routing rule if missing
            if "routing" not in config:
                config["routing"] = {"rules": []}
            
            api_rule = {
                "type": "field",
                "inboundTag": ["api"],
                "outboundTag": "api"
            }

            if not any(rule.get("inboundTag") == ["api"] for rule in config["routing"].get("rules", [])):
                config["routing"]["rules"].insert(0, api_rule)

            return config

        try:
            directory_path = f"./subs/{name}"
            Path(directory_path).mkdir(parents=True, exist_ok=True)

            if isinstance(url, str):
                if url.startswith("http"):
                    # HTTP(S) subscription
                    useragent = str(self.useragant())
                    headers = {"user-agent": useragent}
                    response = requests.get(url=url, headers=headers, timeout=10)
                    response.raise_for_status()
                    text = response.text

                    if text.strip().startswith("["):
                        # Custom JSON array config
                        self.log("Custom config array detected...")
                        configs = json.loads(text)
                        dict_name = {}
                        
                        for count, config in enumerate(configs):
                            try:
                                # Add required components if missing
                                config = add_api_stats_config(config)
                                
                                # Update inbound ports
                                for inbound in config.get("inbounds", []):
                                    if inbound.get("tag") == "socks":
                                        inbound["port"] = 1080
                                    elif inbound.get("tag") == "api":
                                        inbound["port"] = 10085

                                config_name = config.get("remarks", f"Config {count + 1}")
                                config_json = json.dumps(config, indent=4)

                                with open(f"{directory_path}/{count}.json", "w") as f:
                                    f.write(config_json)
                                dict_name[count] = config_name
                            except Exception as e:
                                self.log(f"Error processing config {count}: {str(e)}")
                                continue

                    else:
                        # Base64 encoded subscription
                        try:
                            decoded_str = base64.b64decode(text).decode('utf-8')
                            configs = [x.strip() for x in decoded_str.split("\n") if x.strip()]
                            dict_name = {}
                            
                            for count, config in enumerate(configs):
                                try:
                                    config_json, config_name = convert.convert(config)
                                    if config_json and config_name != "False":
                                        with open(f"{directory_path}/{count}.json", "w") as f:
                                            f.write(config_json)
                                        dict_name[count] = config_name
                                except Exception as e:
                                    self.log(f"Error converting config {count}: {str(e)}")
                                    continue
                        except Exception as e:
                            self.log(f"Error decoding base64: {str(e)}")
                            return

                elif url.startswith("{"):
                    # Single JSON config
                    try:
                        config = json.loads(url)
                        config = add_api_stats_config(config)
                        
                        # Update inbound ports
                        for inbound in config.get("inbounds", []):
                            if inbound.get("tag") == "socks":
                                inbound["port"] = 1080
                            elif inbound.get("tag") == "api":
                                inbound["port"] = 10085

                        config_name = config.get("remarks", ''.join(random.choices(string.ascii_letters, k=8)))
                        config_json = json.dumps(config, indent=4)
                        
                        with open(f"{directory_path}/0.json", "w") as f:
                            f.write(config_json)
                        dict_name = {0: config_name}
                    except json.JSONDecodeError as e:
                        self.log(f"Invalid JSON config: {str(e)}")
                        return
                        
                else:
                    # Single vmess/vless config
                    try:
                        config_json, config_name = convert.convert(url)
                        if config_json and config_name != "False":
                            with open(f"{directory_path}/0.json", "w") as f:
                                f.write(config_json)
                            dict_name = {0: config_name}
                        else:
                            self.log("Config not supported or invalid")
                            return
                    except Exception as e:
                        self.log(f"Error converting config: {str(e)}")
                        return

                # Save config list and URL
                with open(f"{directory_path}/list.json", "w", encoding="utf-8") as f:
                    json.dump(dict_name, f, ensure_ascii=False, indent=4)
                
                with open(f"{directory_path}/url.txt", "w", encoding="utf-8") as f:
                    f.write(url)
            else:
                self.log("URL must be a string")

        except Exception as e:
            self.log(f"Error in import_subscription: {str(e)}")
            if os.path.exists(directory_path):
                shutil.rmtree(directory_path)

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
        try:
            # کش کردن نتایج پینگ برای 30 ثانیه
            cache_key = f"{profile}_{config_num}_{ping_type}"
            current_time = time.time()
            
            if hasattr(self, '_ping_cache'):
                if cache_key in self._ping_cache:
                    result, timestamp = self._ping_cache[cache_key]
                    if current_time - timestamp < 30:
                        return result
            else:
                self._ping_cache = {}

            result = self._do_ping(profile, config_num, ping_type)
            self._ping_cache[cache_key] = (result, current_time)
            return result
        
        except Exception as e:
            return f"Error: {str(e)}"

    def _change_config_port(self, config_path, new_port):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Store original ports
            original_ports = []
            for inbound in config['inbounds']:
                original_ports.append(inbound['port'])
                inbound['port'] = new_port
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            return original_ports
        except Exception as e:
            self.log(f"Error changing port: {str(e)}")
            return None

    def _restore_config_ports(self, config_path, original_ports):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            for i, inbound in enumerate(config['inbounds']):
                inbound['port'] = original_ports[i]
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            self.log(f"Error restoring ports: {str(e)}")

    def _do_ping(self, profile, config_num, ping_type):
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
            # Generate random port
            random_port = random.randint(10000, 65000)
            original_ports = self._change_config_port(config_path, random_port)
            
            if original_ports is None:
                return "Error: Could not change ports"

            try:
                self.run_xray(config_path)
                time.sleep(1)
                
                s_time = time.time()
                try:
                    response = requests.get('http://gstatic.com/generate_204', 
                                         proxies={"http": f"http://127.0.0.1:{random_port}"}, 
                                         timeout=2)
                except requests.exceptions.Timeout:
                    return "Timeout"
                e_time = time.time()
                
                if 200 <= response.status_code < 300:
                    delay_ms = (e_time - s_time) * 1000
                    return f"{delay_ms:.2f} ms"
                else:
                    return "Timeout"
            except:
                self.stop_xray()
                return "Timeout"
            finally:
                self.stop_xray()
                self._restore_config_ports(config_path, original_ports)

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
            # xray_path = f"./core/{self.os_sys}/xray"
            creation_flags = subprocess.CREATE_NO_WINDOW if self.os_sys == "win" else 0
            
            self.xray_process = subprocess.Popen(
                [XRAY_PATH, '-config', config_path],
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
        def _read_stream(stream):
            for line in iter(stream.readline, ''):
                with self._output_lock:
                    if len(line.strip()) > 0:
                        self._process_output_buffer.append(f"{name}: {line.strip()}")
                        if self.log_callback:
                            self.log_callback(self._process_output_buffer[-1])
                time.sleep(0.01)

        threading.Thread(target=_read_stream, args=(process.stdout,), daemon=True).start()
        threading.Thread(target=_read_stream, args=(process.stderr,), daemon=True).start()

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
            
        # Reset traffic stats and last values when stopping Xray
        self._last_bytes_sent = 0
        self._last_bytes_recv = 0
        self._last_traffic_check = time.time()
        
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

    def _get_xray_traffic(self, stat_name):
            """Helper function to get traffic stats from Xray"""
            try:
                creation_flags = subprocess.CREATE_NO_WINDOW if self.os_sys == "win" else 0
                result = subprocess.run(
                    [self.xray_path, "api", "stats", f"--server={self.server}", f"-name={stat_name}"],
                    capture_output=True,
                    text=True,
                    creationflags=creation_flags
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    return data.get("stat", {}).get("value", 0)
                else:
                    print(f"Error fetching {stat_name}: {result.stderr}")
                    return 0
            except Exception as e:
                print(f"Error: {e}")
                return 0

    def get_system_traffic(self):
        """Get traffic statistics from Xray for the proxy connection"""
        try:
            # Get current traffic stats from Xray
            bytes_sent = self._get_xray_traffic("outbound>>>proxy>>>traffic>>>uplink")
            bytes_recv = self._get_xray_traffic("outbound>>>proxy>>>traffic>>>downlink")
            
            # Get current time and calculate time difference
            current_time = time.time()
            time_delta = current_time - self._last_traffic_check
            
            # Calculate speeds (bytes per second)
            upload_speed = (bytes_sent - self._last_bytes_sent) / time_delta if time_delta > 0 else 0
            download_speed = (bytes_recv - self._last_bytes_recv) / time_delta if time_delta > 0 else 0
            
            # Update last values
            self._last_bytes_sent = bytes_sent
            self._last_bytes_recv = bytes_recv
            self._last_traffic_check = current_time
            
            # Return traffic stats in the same format as the original
            return {
                'speed': (upload_speed, download_speed),  # (upload speed, download speed) in bytes/second
                'total': (bytes_sent, bytes_recv)         # (total sent, total received) in bytes
            }
            
        except Exception as e:
            print(f"Error getting Xray traffic: {str(e)}")
            return {
                'speed': (0, 0),
                'total': (0, 0)
            }

    def get_traffic_stats(self):
        """Get current traffic statistics"""
        return self.get_system_traffic()

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)