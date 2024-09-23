import requests
import base64
import json
import os
import shutil

def get_sub ():
    url = input("Please Enter your  URL link (sub) : ")
    sub_name  = input("Please Enter your sub name : ")
    headers = {"user-agent":"v2rayNG"}
    r = requests.get(url=url , headers=headers)
    text = r.text
    decoded_bytes = base64.b64decode(text)
    decoded_str = decoded_bytes.decode('utf-8')
    list_configs = decoded_str.split("\n")
    
    # check if sub folder exist -> delete all files in it
    directory_path = f"./subs/{sub_name}"
    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"error {file_path}: {e}")
        print(f"previous {sub_name} sub delted ...")
    
    #if sub folder does not exist -> create directory for it 
    directories = [d for d in os.listdir("./subs/") if os.path.isdir(os.path.join("./subs/", d))]
    if sub_name not in directories :
        os.mkdir(f"./subs/{sub_name}")
    count = 0
    dict_name = {}
    for config in list_configs:
        import convert
        config_json , config_name = convert.convert(config)
        if config_name == "False" :
            break
        # if "/" in config_name :
        #     li = config_name.split("/")
        #     config_name = ""
        #     for l in li  :
        #         config_name += l

        with open (f"./subs/{sub_name}/{count}.json" , "w") as f :
            f.writelines(config_json)
        
        dict_name[count] = config_name
        count += 1
    
    with open (f"./subs/{sub_name}/list.json" , "w" , encoding="utf-8") as f :
        json.dump(dict_name, f, ensure_ascii=False, indent=4)


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

get_sub()