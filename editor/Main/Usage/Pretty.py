import json
import urllib.request

def Pretty(code: str) -> str:
    url = "https://encode64.com/api/lua-formatter"
    payload = {
        "source": code,
        "options": {
            "actionMode": "format",
            "liveMode": True
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        return data["formatted"]
