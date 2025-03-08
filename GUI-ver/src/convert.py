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

def decode_vmess(link):
    try:
        link = link.replace("vmess://", "")
        decoded_bytes = base64.b64decode(link)
        decoded_str = decoded_bytes.decode('utf-8')
        config = json.loads(decoded_str)
        
        config_name = extract_name_vmess(config)

        address = config.get('add', '')
        port = config.get('port', '')
        address, port = split_address_port(f"{address}:{port}")

        stream_settings = {
            "network": config.get('net', 'tcp'),
            "security": "none"
        }

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

        elif network_type == "splithttp":
            stream_settings["splithttpSettings"] = {
                "host": config.get('host', ""),
                "path": config.get('path', "/"),
                "xmux": {"maxConcurrency": 4, "cMaxLifetimeMs": 10000}
            }

        elif network_type == "grpc":
            stream_settings["grpcSettings"] = {
                "serviceName": config.get('path', ""),
                "authority": config.get('host', ""),
                "health_check_timeout": 20,
                "idle_timeout": 60,
                "multiMode": False
            }
        elif network_type == "httpupgrade":
            stream_settings["network"] = "httpupgrade"
            stream_settings["httpupgradeSettings"] = {
                "host": config.get('host', ""),
                "path": config.get('path', "/")
            }

        elif network_type == "kcp":
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
                "allowInsecure": bool(config.get('allowInsecure', 1))
            }

        if config.get('security', '') == "reality":
            stream_settings["security"] = "reality"
            stream_settings["realitySettings"] = {
                "allowInsecure": bool(config.get('allowInsecure', 1)),
                "fingerprint": config.get('fingerprint', 'chrome'),
                "serverName": config.get('serverName', ''),
                "show": bool(config.get('show', False))
            }

        # Base Xray configuration with API and Stats support
        xray_config = {
            "log": {"loglevel": "info"},
            "api": {
                "tag": "api",
                "services": ["HandlerService", "LoggerService", "StatsService"]
            },
            "stats": {},
            "policy": {
                "levels": {
                    "0": {
                        "statsUserUplink": True,
                        "statsUserDownlink": True
                    }
                },
                "system": {
                    "statsInboundUplink": True,
                    "statsInboundDownlink": True,
                    "statsOutboundUplink": True,
                    "statsOutboundDownlink": True
                }
            },
            "inbounds": [
                {
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
                },
                {
                    "tag": "api",
                    "port": 10085,
                    "listen": "127.0.0.1",
                    "protocol": "dokodemo-door",
                    "settings": {
                        "address": "127.0.0.1"
                    }
                }
            ],
            "outbounds": [
                {
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
                },
                {
                    "protocol": "freedom",
                    "settings": {},
                    "tag": "direct"
                },
                {
                    "protocol": "blackhole",
                    "settings": {},
                    "tag": "block"
                }
            ],
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

    def get_param(key, default):
        return query_params.get(key, [default])[0]

    stream_settings = {
        "network": get_param('type', 'tcp')
    }

    if stream_settings["network"] == "tcp":
        stream_settings["tcpSettings"] = {
            "header": {
                "type": get_param('headerType', 'none')
            }
        }
    elif stream_settings["network"] == "splithttp":
        stream_settings["splithttpSettings"] = {
            "host": get_param('host', ""),
            "path": get_param('path', "/"),
            "xmux": {"maxConcurrency": 4, "cMaxLifetimeMs": 10000}
        }
    elif stream_settings["network"] == "ws":
        stream_settings["wsSettings"] = {
            "path": get_param('path', "/"),
            "headers": {
                "Host": get_param('host', "")
            }
        }
    elif stream_settings["network"] == "httpupgrade":
        stream_settings["httpupgradeSettings"] = {
            "path": get_param('path', "/"),
            "host": get_param('host', "")
        }
    elif stream_settings["network"] == "xhttp":
        extra_settings = {}
        if 'extra' in query_params:
            try:
                extra_json = urllib.parse.unquote(query_params['extra'][0])
                extra_settings = json.loads(extra_json)
            except Exception as e:
                print(f"Error parsing extra parameter: {e}")
        
        xhttp_settings = {
            "mode": get_param('mode', "packet-up"),
            "path": get_param('path', "/"),
            "host": get_param('host', "")
        }
        
        extra_field = {}
        if extra_settings:
            if 'scMaxEachPostBytes' in extra_settings:
                extra_field["scMaxEachPostBytes"] = extra_settings['scMaxEachPostBytes']
            if 'scMinPostsIntervalMs' in extra_settings:
                extra_field["scMinPostsIntervalMs"] = extra_settings['scMinPostsIntervalMs']
            if 'xPaddingBytes' in extra_settings:
                extra_field["xPaddingBytes"] = extra_settings['xPaddingBytes']
            if 'noGRPCHeader' in extra_settings:
                extra_field["noGRPCHeader"] = extra_settings['noGRPCHeader']
            if 'xmux' in extra_settings:
                extra_field["xmux"] = extra_settings['xmux']
        
        if extra_field:
            xhttp_settings["extra"] = extra_field
            
        stream_settings["xhttpSettings"] = xhttp_settings

    elif stream_settings["network"] == "kcp":
        stream_settings["kcpSettings"] = {
            "header": {
                "type": get_param('headerType', 'none')
            }
        }

    elif stream_settings["network"] == "grpc":
        stream_settings["grpcSettings"] = {
            "serviceName": get_param('serviceName', ""),
            "authority": get_param('authority', ""),
            "health_check_timeout": 20,
            "idle_timeout": 60,
            "multiMode": False
        }

    if get_param('security', 'none') == "reality":
        stream_settings["security"] = "reality"
        stream_settings["realitySettings"] = {
            "allowInsecure": get_param('allowInsecure', 'false').lower() == 'true',
            "fingerprint": get_param('fp', ""),
            "publicKey": get_param('pbk', ""),
            "serverName": get_param('sni', ""),
            "shortId": get_param('sid', ""),
            "show": False
        }

    elif get_param('security', 'none') == "tls":
        stream_settings["security"] = "tls"
        stream_settings["tlsSettings"] = {
            "serverName": get_param('sni', ""),
            "fingerprint": get_param('fp', ""),
            "alpn": get_param('alpn', "http/1.1").split(','),
            "allowInsecure": get_param('allowInsecure', 'false').lower() == 'true' or get_param('allowInsecure', '0') == '1'
        }

    # Base Xray configuration with API and Stats support
    xray_config = {
        "log": {"loglevel": "info"},
        "api": {
            "tag": "api",
            "services": ["HandlerService", "LoggerService", "StatsService"]
        },
        "stats": {},
        "policy": {
            "levels": {
                "0": {
                    "statsUserUplink": True,
                    "statsUserDownlink": True
                }
            },
            "system": {
                "statsInboundUplink": True,
                "statsInboundDownlink": True,
                "statsOutboundUplink": True,
                "statsOutboundDownlink": True
            }
        },
        "inbounds": [
            {
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
            },
            {
                "tag": "api",
                "port": 10085,
                "listen": "127.0.0.1",
                "protocol": "dokodemo-door",
                "settings": {
                    "address": "127.0.0.1"
                }
            }
        ],
        "outbounds": [
            {
                "protocol": "vless",
                "settings": {
                    "vnext": [{
                        "address": address,
                        "port": int(port),
                        "users": [{"id": uuid, "encryption": "none"}]
                    }]
                },
                "streamSettings": stream_settings,
                "tag": "proxy"
            },
            {
                "protocol": "freedom",
                "settings": {},
                "tag": "direct"
            },
            {
                "protocol": "blackhole",
                "settings": {},
                "tag": "block"
            }
        ],
        "dns": {
            "servers": ["1.1.1.1", "8.8.8.8"]
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
    return json.dumps(xray_config, indent=4)

def convert(config):
    link = config
    config_json = None
    config_name = None

    print(link)

    if link.startswith("vmess://"):
        config_json, config_name = decode_vmess(link)
    elif link.startswith("vless://"):
        config_json = decode_vless(link)
        config_name = link.split('#')[-1] if '#' in link else "Unnamed Config"
    elif link == "False":  
        config_json = "False"
        config_name = "False"
        
    print("Generated Xray Configuration:")
    print(config_json)

    # with open("xray_config.json", "w") as f:
    #     f.write(config_json)

    # print("Configuration saved to 'xray_config.json'")

    return config_json, config_name

# Example usage
if __name__ == "__main__":
    # Example VMess link
    vmess_link = "vmess://eyJhZGQiOiJleGFtcGxlLmNvbSIsInBvcnQiOiI0NDMiLCJpZCI6ImFiYyIsImFpZCI6IjAiLCJzY3kiOiJhdXRvIiwibmV0IjoidGNwIiwicHMiOiJNeSBWMWVzcyJ9"
    config_json, config_name = convert(vmess_link)