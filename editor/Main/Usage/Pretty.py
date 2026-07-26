import json
import urllib.request
import urllib.error

def Pretty(code: str) -> str:
    url = "https://encode64.com/api/lua-formatter"
    payload = {
        "source": code,
        "options": {
            "actionMode": "format",
            "liveMode": True
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://encode64.com/'
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            formatted_code = data.get("formatted") or data.get("result")
            
            if formatted_code is not None:
                return formatted_code
                
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        print(f"Format API failed: {e}")
        
    return code 
