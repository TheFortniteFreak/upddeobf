import re

def RCom(script):
    script = re.sub(r'--\[\[.*?\]\]', '', script, flags=re.DOTALL)

    script = re.sub(r'--(?!\[).*$', '', script, flags=re.MULTILINE)

    return script
