import requests
import base64
import json
import os
import shutil
import subprocess
import signal
import sys
import platform
from pathlib import Path
import convert
from const import *
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import zipfile
from tqdm import tqdm
from colorama import init, Fore, Style, Back

sub_select = ""
update_available = False
latest_version = None
app_latest_version = None

init(autoreset=True)

def print_banner():
    """Print a colorful banner for XC (Xray Client)"""
    banner = r"""
    {}
        ██╗  ██╗ ██████╗
        ╚██╗██╔╝██╔════╝
        ╚███╔╝ ██║     
        ██╔██╗ ██║     
        ██╔╝ ██╗╚██████╗
        ╚═╝  ╚═╝ ╚═════╝
                
    {}  Xray Client CLI {}
    {}====================={}
    """.format(
        Fore.CYAN, 
        Fore.YELLOW, 
        Fore.GREEN + f"v{APP_VERSION}" + Style.RESET_ALL, 
        Fore.MAGENTA, 
        Style.RESET_ALL
    )
    print(banner)

def signal_handler(sig, frame):
    print(Fore.RED + 'You pressed Ctrl+C! Terminating Xray...' + Style.RESET_ALL)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def check_ver():
    try:
        response = requests.get(REPO_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        version_text = soup.find(string=lambda text: text and "Release" in text)
        app_latest_version = version_text.split(" ")[2].split("v")[1]
    except requests.RequestException as e:
        print(Fore.RED + f"Error fetch repo : {e}" + Style.RESET_ALL)
    
    if app_latest_version != APP_VERSION:
        print(Fore.YELLOW + "...Update Available..." + Style.RESET_ALL)
        print(Fore.GREEN + "Please Go to the Github Page and download the latest Version ..." + Style.RESET_ALL)
        print(Fore.CYAN + "https://github.com/wikm360/xray-client/releases/latest" + Style.RESET_ALL)

    try:
        response = requests.get(URL_CHECK, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        version_text = soup.find(string=lambda text: text and "v=" in text)
        
        if version_text:
            latest_version = version_text.split("v=")[1].strip()
            print(Fore.GREEN + f"Latest Version of Core is : {latest_version}" + Style.RESET_ALL)
        else:
            raise ValueError("Version information not found on the page")

        if not os.path.exists(CORE_PATH) or XRAY_VERSION != latest_version:
            print(Fore.YELLOW + "Core Not Found ..." + Style.RESET_ALL)
            print(Fore.GREEN + "Download Core Starting..." + Style.RESET_ALL)
            try:
                download_core()
                extract_core()
                finalize_update()
            
            except Exception as e:
                print(Fore.RED + f"ERROR : {e}" + Style.RESET_ALL)
    
        else:
            print(Fore.GREEN + "Core is up to date." + Style.RESET_ALL)
            return

    except RequestException as e:
        print(Fore.RED + f"Network error: {e}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Error checking for updates: {e}" + Style.RESET_ALL)

def import_subscription(name, url):
    directory_path = f"./subs/{name}"
    folder_path = Path(directory_path)

    if folder_path.exists() and folder_path.is_dir() :
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Error {file_path}: {e}")
        print(f"Previous {name} sub deleted ...")
    if "https" in url :
        headers = {"user-agent": "XC(Xray-Client)"}
        r = requests.get(url=url, headers=headers)
        text = r.text
        decoded_bytes = base64.b64decode(text)
        decoded_str = decoded_bytes.decode('utf-8')
        list_configs = decoded_str.split("\n")

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
    else  :
        config  = url
        directory_path = f"./subs/{name}"
        Path(directory_path).mkdir(parents=True, exist_ok=True)

        if config.strip():
            config_json, config_name = convert.convert(config)
            if config_name != "False":
                with open(f"./subs/{name}/0.json", "w") as f:
                    f.write(config_json)
        with open(f"./subs/{name}/list.json", "w", encoding="utf-8") as f:
            json.dump({0:config_name}, f, ensure_ascii=False, indent=4)
        with open(f"./subs/{name}/url.txt", "w", encoding="utf-8") as f:
            f.write(url)

def get_sub():
    url = input("Please Enter your URL link (sub): ")
    sub_name = input("Please Enter your sub name: ")
    import_subscription(sub_name , url)

def list_subs():
    global sub_select
    path = "./subs"
    try :
        directories = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    except :
        Path(path).mkdir(parents=True, exist_ok=True)
    directories = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    if directories:
        for i, sub in enumerate(directories, 1):
            print(f"{i} - {sub}")
        print("'add' for add new sub link")
        print("'exit' for back to main menu")
        print("'del' for deleted a subscription (The selected sub will be deleted)")
    else :
        print("No Sub detected ...")
        print("'add' for add new sub link")
        print("'exit' for back to main menu")
    choose = input("Enter your choice (sub name): ").lower()
    if choose == "add":
        get_sub()
    elif choose == "exit":
        pass  # back to main menu
    
    elif choose == "del" :
        directory_path = f"./subs/{sub_select}"
        folder_path = Path(directory_path)

        if folder_path.exists() and folder_path.is_dir():
            try:
                shutil.rmtree(folder_path)
                print(f"Previous {sub_select} sub deleted ...")
            except Exception as e:
                print(f"Error while deleting {folder_path}: {e}")
        else:
            print(f"Folder {sub_select} does not exist.")
    
    else:
        if choose in directories:
            list_configs(choose)
        else:
            print("Please enter a valid option ...")
            list_subs()

def list_configs(sub_name):
    path_json = f"./subs/{sub_name}"
    list_file = [f for f in os.listdir(path_json) if f.endswith('.json') and f == "list.json"]
    if list_file:
        print(f"List of configs for {sub_name}:")
        with open(path_json+"/list.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        for key , value in data.items() :
            print(f"{key} - {value}")
        print("'exit' for back to main menu")
        choose_2 = input("Enter the config number to select: ").lower()
        if choose_2 == "exit":
            pass
        else:
            try:
                config_index = int(choose_2)
                if 0 <= config_index < len(data):
                    with open(f"./core/{OS_SYS}/select.txt", "w") as f:
                        f.write(f"./subs/{sub_name}/{config_index}.json")
                    print(f"Config {config_index} selected.")
                else:
                    print("Please enter a valid config number.")
                    list_configs(sub_name)
            except ValueError:
                print("Invalid input. Please enter a number.")
                list_configs(sub_name)
    else:
        print("No configs detected ...")

def run_xray():
    with open(f"./core/{OS_SYS}/select.txt", "r") as f:
        config_path = f.read().strip()
    print(f"Running Xray with config: {config_path}")
    xray_path = f"./core/{OS_SYS}/xray"
    subprocess.Popen([xray_path, '-config', config_path])

def download_core():
    """Download a file with a progress bar."""
    try:
        response = requests.get(DOWNLOAD_URL, stream=True, timeout=30)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))

        with open(SAVE_PATH, 'wb') as file, tqdm(
            total=total_size, unit='B', unit_scale=True, desc="Downloading Core"
        ) as bar:
            for data in response.iter_content(1024):
                size = file.write(data)
                bar.update(size)

        print("Download completed!")
    except requests.RequestException as e:
        print(f"Error downloading file: {e}")
        sys.exit(1)

def extract_core():
    print("Extracting...")
    
    try:
        with zipfile.ZipFile(SAVE_PATH, 'r') as zip_ref:
            zip_ref.extractall(ROOT)
        
        os.remove(SAVE_PATH)
    except Exception as e:
        raise Exception(f"Extraction failed: {str(e)}")

def finalize_update():
    try:
        print("Update Complete Successfull")

        if OS_SYS == "linux"  :
            os.chmod("./core/linux/xray", 0o755)
            os.chmod("./core/linux/sing-box", 0o755)


    except Exception as e:
        raise Exception(f"Failed to finalize update: {str(e)}")

def install_requirements(requirements_file="requirements.txt"):
    if not os.path.exists(requirements_file):
        print(f"file {requirements_file} does not find.")
        return
    
    try:
        print(f"Checking for Requirements : {requirements_file}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
        print("Requirements Innstalled")
    except subprocess.CalledProcessError as e:
        print(f"Error in installign : {e}")
    except Exception as e:
        print(f"unexpected : {e}")

def main_menu():
    install_requirements()
    # Clear screen for a clean start
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Print banner at the start
    print_banner()
    
    check_ver()
        
    while True:
        global sub_select
        sub_select = ""
        config_select = ""
        print(Fore.CYAN + f"## OS detected = {OS_SYS} ##" + Style.RESET_ALL)

        select_path = f"./core/{OS_SYS}/select.txt"
        with open (select_path  , "r") as f:
            data = f.readlines()
            if data:
                select = data[0].split("/")
                sub_select = select[2]
                config_select = select[3].split(".")[0]

        print("\n" + Fore.YELLOW + "Main Menu:" + Style.RESET_ALL)
        print(Fore.GREEN + "1. Add new subscription" + Style.RESET_ALL)
        if sub_select or config_select:
            print(Fore.GREEN + f"2. List of subscriptions / change sub or config " + 
                  Fore.MAGENTA + f"(selected = {sub_select} -> {config_select})" + Style.RESET_ALL)
        else: 
            print(Fore.GREEN + "2. List of subscriptions / change sub or config" + Style.RESET_ALL)
        print(Fore.GREEN + "3. Run" + Style.RESET_ALL)
        print(Fore.RED + "4. Exit" + Style.RESET_ALL)
        
        choice = input(Fore.CYAN + "Choose an option: " + Style.RESET_ALL).lower()
        
        if choice == "1":
            get_sub()
        elif choice == "2":
            list_subs()
        elif choice == "3":
            run_xray()
        elif choice == "4":
            print(Fore.YELLOW + "Goodbye! 👋" + Style.RESET_ALL)
            break
        else:
            print(Fore.RED + "Invalid choice, please try again." + Style.RESET_ALL)

if __name__ == "__main__":
    main_menu()
