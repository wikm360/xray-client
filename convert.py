#xray.exe run -c config.json

import json
import base64
import urllib.parse

def decode_vmess(link):
    link = link.replace("vmess://", "")
    decoded_bytes = base64.b64decode(link)
    decoded_str = decoded_bytes.decode('utf-8')
    config = json.loads(decoded_str)

    stream_settings = {
        "network": config['net']
    }

    if config['net'] == "tcp":
        stream_settings["tcpSettings"] = {
            "header": {
                "type": config.get('type', 'none'),
                "request": {
                    "version": "1.1",
                    "method": "GET",
                    "path": config.get('path', ["/"]),
                    "headers": {
                        "Host": config.get('host', [""]),
                        "User-Agent": config.get('ua', [""]),
                        "Accept-Encoding": config.get('accept-encoding', ["gzip, deflate"]),
                        "Connection": config.get('connection', ["keep-alive"]),
                        "Pragma": config.get('pragma', "no-cache")
                    }
                }
            }
        }

    elif config['net'] == "ws":
        stream_settings["wsSettings"] = {
            "path": config.get('path', ""),
            "headers": {
                "Host": config.get('host', "")
            }
        }

    elif config['net'] == "kcp":
        stream_settings["kcpSettings"] = {
            "header": {
                "type": config.get('type', 'none')
            }
        }

    if config.get('tls') == "tls":
        stream_settings["security"] = "tls"
        stream_settings["tlsSettings"] = {
            "serverName": config.get('sni', ""),
            "fingerprint": config.get('fp', ""),
            "alpn": config.get('alpn', ["http/1.1"]),
            "allowInsecure": config.get('allowInsecure', False)
        }

    xray_config = {
        "log": {"loglevel": "info"},
        "inbounds": [{
            "port": 1080, "protocol": "socks", "settings": {"auth": "noauth", "udp": True}
        }],
        "outbounds": [{
            "protocol": "vmess",
            "settings": {
                "vnext": [{
                    "address": config['add'], "port": int(config['port']),
                    "users": [{"id": config['id'], "alterId": int(config['aid']), "security": config['scy']}]
                }]
            },
            "streamSettings": stream_settings
        }]
    }
    return json.dumps(xray_config, indent=4)


def decode_vless(link):
    link = link.replace("vless://", "")
    parts = link.split('@')
    uuid = parts[0]
    remaining = parts[1]
    address_port, params = remaining.split('?')
    address, port = address_port.split(':')
    query_params = urllib.parse.parse_qs(params)

    stream_settings = {
        "network": query_params.get('type', ['tcp'])[0]
    }

    if stream_settings["network"] == "tcp":
        stream_settings["tcpSettings"] = {
            "header": {
                "type": query_params.get('headerType', ['none'])[0],
                "request": {
                    "path": query_params.get('path', ["/"]),
                    "headers": {
                        "Host": query_params.get('host', [""]),
                        "User-Agent": query_params.get('ua', [""]),
                        "Accept-Encoding": query_params.get('accept-encoding', ["gzip, deflate"]),
                        "Connection": query_params.get('connection', ["keep-alive"]),
                        "Pragma": query_params.get('pragma', "no-cache")
                    }
                }
            }
        }

    if query_params.get('security', ['none'])[0] == "tls":
        stream_settings["security"] = "tls"
        stream_settings["tlsSettings"] = {
            "serverName": query_params.get('sni', [""])[0],
            "fingerprint": query_params.get('fp', [""])[0],
            "alpn": query_params.get('alpn', ["http/1.1"])
        }

    elif stream_settings["network"] == "kcp":
        stream_settings["kcpSettings"] = {
            "header": {
                "type": query_params.get('headerType', ['none'])[0]
            }
        }

    if query_params.get('security', ['none'])[0] == "tls":
        stream_settings["security"] = "tls"
        stream_settings["tlsSettings"] = {
            "serverName": query_params.get('sni', [""])[0],
            "fingerprint": query_params.get('fp', [""])[0],
            "alpn": query_params.get('alpn', ["http/1.1"]),
            "allowInsecure": query_params.get('allowInsecure', ['false'])[0].lower() == 'true'
        }

    xray_config = {
        "log": {"loglevel": "info"},
        "inbounds": [{
            "port": 1080, "protocol": "socks", "settings": {"auth": "noauth", "udp": True}
        }],
        "outbounds": [{
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": address, "port": int(port),
                    "users": [{"id": uuid, "encryption": "none"}]
                }]
            },
            "streamSettings": stream_settings
        }]
    }
    return json.dumps(xray_config, indent=4)

link = input("Enter vmess, vless, ss, or trojan link: ")

if link.startswith("vmess://"):
    config_json = decode_vmess(link)
elif link.startswith("vless://"):
    config_json = decode_vless(link)

print("Generated Xray Configuration:")
print(config_json)

with open("xray_config.json", "w") as f:
    f.write(config_json)

print("Configuration saved to 'xray_config.json'")