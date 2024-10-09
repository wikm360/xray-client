import requests
import time 

def Ping(proxy_port):
    try :
        s_time = time.time()
        response = requests.get('http://gstatic.com/generate_204', proxies={"http":f"http://127.0.0.1:{proxy_port}"})
        e_time = time.time()
    except :
        return -1
    if response.status_code <300 and response.status_code > 199:
        return e_time - s_time
    else:
        return -1
    
print(Ping(1080))