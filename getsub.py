import requests
import base64

url = ""
headers = {"user-agent":"v2rayNG"}
r = requests.get(url=url , headers=headers)
text = r.text
decoded_bytes = base64.b64decode(text)
decoded_str = decoded_bytes.decode('utf-8')
list_configs = decoded_str.split("\n")
print(list_configs)