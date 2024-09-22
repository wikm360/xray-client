import requests
import base64
import os

def get_sub ():
    url = ""
    headers = {"user-agent":"v2rayNG"}
    r = requests.get(url=url , headers=headers)
    text = r.text
    decoded_bytes = base64.b64decode(text)
    decoded_str = decoded_bytes.decode('utf-8')
    list_configs = decoded_str.split("\n")
    print(list_configs)


def list_subs() :
    path = "./subs"
    directories = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    count = 0
    if directories :
        for sub in directories :
            print(f"{count} - {sub}")
        print("'add' for add new sub link")
        print("'exit' for back to main menu")
    choose = input("Enter yout choose (sub name) : ").lower()
    if choose == "add" :
        get_sub()
    elif choose == "exit" :
        pass # back to main menu
    else :
        if choose :
            if choose in directories :
                list_configs(choose)
            else :
                print("plese enter valid option ...")
            pass
        else :
            print("please choose one option ...")
            list_subs()
    return directories

def list_configs(choose) :
    path_config = f"./subs/{choose}"
    json_files = [f for f in os.listdir(path_config) if f.endswith('.json') and os.path.isfile(os.path.join(path_config, f))]
    if json_files :
        for config in json_files :
            print(config)
        print("'exit' for back to main menu")
        choose_2 = input("Enter yout choose (sub name) : ").lower()
        if choose_2 == "exit" :
            pass # back to main menu
        else :
            if choose :
                if choose in json_files :
                    with open ("./select.txt" , "w") as f :
                        f.write(choose + "\n" + choose_2)
                else :
                    print("lease Enter valid config")
    else :
        print("Not config detected ...")

list_subs()