#xray.exe run -c config.json

import json
import base64
import urllib.parse
import re

def split_address_port(address_port):
    if address_port.startswith('['):
        match = re.match(r'\[([^\]]+)\]:(\d+)', address_port)
        if match:
            return match.group(1), match.group(2)
    else:
        return address_port.split(':')

def extract_name_vmess(config):
    return config.get('ps', "Unnamed Config")

import base64
import json

def decode_vmess(link):
    try:
        # پاک کردن پیشوند vmess و دیکود کردن base64
        link = link.replace("vmess://", "")
        decoded_bytes = base64.b64decode(link)
        decoded_str = decoded_bytes.decode('utf-8')
        config = json.loads(decoded_str)
        
        config_name = extract_name_vmess(config)

        # استخراج آدرس و پورت با مقادیر پیش‌فرض
        address = config.get('add', '')
        port = config.get('port', '')
        address, port = split_address_port(f"{address}:{port}")

        # تنظیمات اولیه stream با مقادیر پیش‌فرض
        stream_settings = {
            "network": config.get('net', 'tcp'),
            "security": "none"
        }

        # پیکربندی بر اساس نوع شبکه
        network_type = config.get('net', 'tcp')
        
        if network_type == "tcp":
            stream_settings["tcpSettings"] = {
                "header": {
                    "type": config.get('type', 'none'),
                    "request": {
                        "version": "1.1",
                        "method": "GET",
                        "path": config.get('path', ["/"]),
                        "headers": {
                            "Host": [config.get('host', "")],
                            "User-Agent": [config.get('ua', "")],
                            "Accept-Encoding": ["gzip, deflate"],
                            "Connection": ["keep-alive"],
                            "Pragma": "no-cache"
                        }
                    }
                }
            }

        elif network_type == "ws":
            stream_settings["wsSettings"] = {
                "path": config.get('path', ""),
                "headers": {
                    "Host": config.get('host', "")
                }
            }

        elif network_type == "kcp":
            stream_settings["kcpSettings"] = {
                "header": {
                    "type": config.get('type', 'none')
                }
            }

        elif network_type == "splithttp":
            stream_settings["splithttpSettings"] = {
                "host": config.get('host', ""),
                "path": config.get('path', "/"),
                "xmux": {"maxConcurrency": 4, "cMaxLifetimeMs": 10000}
            }

        elif network_type == "httpupgrade":
            stream_settings["network"] = "httpupgrade"
            stream_settings["httpupgradeSettings"] = {
                "host": config.get('host', ""),
                "path": config.get('path', "/")
            }

        # تنظیمات TLS
        if config.get('tls') == "tls":
            stream_settings["security"] = "tls"
            stream_settings["tlsSettings"] = {
                "serverName": config.get('sni', ""),
                "fingerprint": config.get('fp', ""),
                "alpn": config.get('alpn', ["http/1.1"]),
                "allowInsecure": bool(config.get('allowInsecure', 1))
            }

        xray_config = {
            "log": {"loglevel": "info"},
            "inbounds": [{
                "tag": "socks",
                "port": 1080,
                "listen": "127.0.0.1",
                "protocol": "socks",
                "sniffing": {
                    "enabled": True,
                    "destOverride": ["http", "tls"],
                    "routeOnly": False
                },
                "settings": {
                    "auth": "noauth",
                    "udp": True,
                    "allowTransparent": False
                }
            }],
            "outbounds": [{
                "protocol": "vmess",
                "settings": {
                    "vnext": [{
                        "address": address,
                        "port": int(port) if port else 443,
                        "users": [{
                            "id": config.get('id', ''),
                            "alterId": int(config.get('aid', 0)),
                            "security": config.get('scy', 'auto'),
                            "level": config.get('level', 8),
                            "encryption": config.get('encryption', ''),
                            "flow": config.get('flow', '')
                        }]
                    }]
                },
                "streamSettings": stream_settings,
                "tag": "proxy"
            }],
            "dns": {
                "hosts": {
                    "dns.google": "8.8.8.8"
                },
                "servers": [
                    {
                        "address": "223.5.5.5",
                        "domains": ["wikm.ir"]
                    },
                    "1.1.1.1",
                    "8.8.8.8",
                    "https://dns.google/dns-query",
                    {
                        "address": "223.5.5.5",
                        "domains": [address] if address else []
                    }
                ]
            },
            "routing": {
                "domainStrategy": "AsIs",
                "rules": [
                    {
                        "type": "field",
                        "inboundTag": ["api"],
                        "outboundTag": "api"
                    },
                    {
                        "type": "field",
                        "port": "443",
                        "network": "udp",
                        "outboundTag": "block"
                    },
                    {
                        "type": "field",
                        "port": "0-65535",
                        "outboundTag": "proxy"
                    }
                ]
            }
        }

        return json.dumps(xray_config, indent=4), config_name
        
    except Exception as e:
        return json.dumps({"error": str(e)}), "error_config"




def decode_vless(link):
    link = link.replace("vless://", "")
    parts = link.split('@')
    uuid = parts[0]
    remaining = parts[1]
    address_port, params = remaining.split('?')
    address, port = split_address_port(address_port)
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

    elif stream_settings['network'] == "splithttp":
        stream_settings["splithttpSettings"] = {
            "host": query_params.get('host', [""])[0],
            "path": query_params.get('path', ["/"])[0],
            "xmux" :{"maxConcurrency": 4, "cMaxLifetimeMs": 10000}
        }

    elif stream_settings["network"] == "ws":
        stream_settings["wsSettings"] = {
            "path": query_params.get('path', ["/"])[0],
            "headers": {
                "Host": query_params.get('host', [""])[0],
                "User-Agent": query_params.get('ua', [""])[0]
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
            "allowInsecure": query_params.get('allowInsecure', ['true'])[0].lower() == 'true'
        }

    xray_config = {
        "log": {"loglevel": "info"},
        "inbounds": [{
            "tag": "socks", "port": 1080, "listen": "127.0.0.1" , "protocol": "socks" , "sniffing": {"enabled": True ,"destOverride": ["http","tls"],"routeOnly": False} , "settings": {"auth": "noauth", "udp": True , "allowTransparent": False}
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
        }],
        "dns": {
            "hosts": {
            "dns.google": "8.8.8.8"
            },
            "servers": [
            {
                "address": "223.5.5.5",
                "domains": [
                "wikm.ir"
                ]
            },
            "1.1.1.1",
            "8.8.8.8",
            "https://dns.google/dns-query",
            {
                "address": "223.5.5.5",
                "domains": [
                address
                ]
            }
            ]
        },
        "routing": {
            "domainStrategy": "AsIs",
            "rules": [
            {
                "type": "field",
                "inboundTag": [
                "api"
                ],
                "outboundTag": "api"
            },
            {
                "type": "field",
                "port": "443",
                "network": "udp",
                "outboundTag": "block"
            },
            {
                "type": "field",
                "port": "0-65535",
                "outboundTag": "proxy"
            }
            ]
        }
    }
    return json.dumps(xray_config, indent=4)

def convert (config) :
    link = config

    print(link)

    if link.startswith("vmess://"):
        config_json , config_name = decode_vmess(link)
    elif link.startswith("vless://"):
        config_json = decode_vless(link)
        config_name = link.split('#')[-1]
    elif link == "False" :  
        config_json = "False"
        config_name = "False"
        

    print("Generated Xray Configuration:")
    print(config_json)

    # with open("xray_config.json", "w") as f:
    #     f.write(config_json)

    # print("Configuration saved to 'xray_config.json'")

    return config_json , config_name

# convert(input("Enter : "))