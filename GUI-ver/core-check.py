import os
import requests
import zipfile
from bs4 import BeautifulSoup
import platform

def os_det():
    system_os = platform.system()
    if system_os == "Windows":
        return "win"
    elif system_os == "Linux":
        return "linux"
    elif system_os == "Darwin":
        return "macos"

os_sys = os_det()
root = "./"
core_path = "./core"
save_path  = "./core.zip"
url_ckeck = f'https://netplusshop.ir/core/{os_sys}/index.html'
download_url =  f'https://netplusshop.ir/core/{os_sys}/core.zip'

def check_ver () :

    response = requests.get(url_ckeck)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        version_text = soup.find(string=lambda text: text and "v=" in text)
        
        if version_text:
            latest_version = version_text.split("v=")[1].strip()
            print("Version:", latest_version)
        else:
            print("Version not found.")
    else:
        print("Failed to retrieve the page.")

    current_version_file = os.path.join(core_path, "version.txt")
    if os.path.exists(current_version_file):
        with open(current_version_file, "r") as file:
            current_version = file.read().strip()
    else:
        current_version = None

    if current_version != latest_version:
        print(f"update Finde {latest_version}")
        update_core(current_version_file ,  latest_version)
    else :
        print("core updated .")



def update_core(current_version_file , latest_version):
    try:
        download_core(download_url, save_path)
        with zipfile.ZipFile(save_path, 'r') as zip_ref:
            zip_ref.extractall(root)
        os.remove(save_path)
        if current_version_file and latest_version == "install" :
            pass
        else  :
            with open(current_version_file, "w") as file:
                file.write(latest_version)

        print("core updated succesfully")
    except Exception as e:
        print(f"Error in update core : {e}")


def download_core(download_url, save_path):
    try:
        response = requests.get(download_url, stream=True)
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print(f"Download core successfull")
    except Exception as e:
        print(f"Error in download core: {e}")


def main () :
    if not os.path.exists(core_path):
        print(f"core not installed")
        update_core("install" , "install")
    else :
        print("mmd")
        check_ver()

main()