import platform
import os

def os_det():
    system_os = platform.system()
    if system_os == "Windows":
        version = platform.version()
        if version.startswith("6.1"):
            return "win7"
        return "win"
    elif system_os == "Linux":
        return "linux"
    elif system_os == "Darwin":
        return "macos"

OS_SYS = os_det()

XRAY_PATH=f"./core/{OS_SYS}/xray"
APP_VERSION = "4.3-11"
ROOT = "./"
CORE_PATH = "./core"
SAVE_PATH = "./core.zip"
URL_CHECK = f'https://netplusshop.ir/core/{OS_SYS}/index.html'
DOWNLOAD_URL = f'https://netplusshop.ir/core/{OS_SYS}/core.zip'
REPO_URL = "https://github.com/wikm360/xray-client/releases/latest"
PROXY_IP  =  "127.0.0.1"
PROXY_PORT = 1080
API = "127.0.0.1:10085"

def xray_version():
    if os.path.exists(CORE_PATH) :
        with open (f"{CORE_PATH}/version.txt" , "r") as file :
            v = file.readline()
            return v
    else:
        return "Not Found"
    
XRAY_VERSION = xray_version()