import platform

def os_det():
    system_os = platform.system()
    if system_os == "Windows":
        return "win"
    elif system_os == "Linux":
        return "linux"
    elif system_os == "Darwin":
        return "macos"

OS_SYS = os_det()

APP_VERSION = "4.1-55"
XRAY_VERSION = "1.8.24"
ROOT = "./"
CORE_PATH = "./core"
SAVE_PATH = "./core.zip"
URL_CHECK = f'https://netplusshop.ir/core/{OS_SYS}/index.html'
DOWNLOAD_URL = f'https://netplusshop.ir/core/{OS_SYS}/core.zip'
REPO_URL = "https://github.com/wikm360/xray-client/releases/latest"
