import json
import urllib.request
import urllib.error

def NIntPretty(code):
    saved = {}
    counter = 0

    def protect(m):
        nonlocal counter
        key = f"___LUA_LITERAL_{counter}___"
        saved[key] = m.group(0)
        counter += 1
        return key

    code = re.sub(
        r"""
        "(?:\\.|[^"\\])*"
        |
        '(?:\\.|[^'\\])*'
        |
        --\[\[.*?\]\]
        |
        --[^\n]*
        |
        \[\[.*?\]\]
        """,
        protect,
        code,
        flags=re.VERBOSE | re.DOTALL
    )

    tokens = re.findall(
        r"""
        ___LUA_LITERAL_\d+___
        |
        \.\.\.
        |
        [A-Za-z_][A-Za-z0-9_]*
        |
        \d+(?:\.\d+)?
        |
        ==|~=|<=|>=|\.\.
        |
        [{}()\[\],;=+\-*/%^#<>.:]
        """,
        code,
        flags=re.VERBOSE
    )

    lines = []
    current = []

    indent = 0
    paren = 0
    bracket = 0
    block = 0

    def text():
        return "".join(current)

    def flush():
        nonlocal current
        s = "".join(current).strip()
        if s:
            lines.append("\t" * indent + s)
        current = []

    def add(x):
        current.append(x)

    def space():
        if current and not current[-1].endswith(" "):
            current.append(" ")

    def trim():
        if current and current[-1] == " ":
            current.pop()

    def ident(x):
        return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", x or ""))

    operators = {
        "=",
        "==",
        "~=",
        "<",
        ">",
        "<=",
        ">=",
        "+",
        "-",
        "*",
        "/",
        "%",
        "^"
    }

    i = 0
    prev = None

    while i < len(tokens):

        t = tokens[i]
        n = tokens[i + 1] if i + 1 < len(tokens) else None

        if t == "end":

            if paren == 0 and bracket == 0 and block:
                flush()
                indent -= 1
                block -= 1
                lines.append("\t" * indent + "end")

            else:
                space()
                add("end")

            prev = t
            i += 1
            continue


        if t == "until":
            flush()
            indent -= 1
            block = max(block - 1, 0)
            lines.append("\t" * indent + "until")

            prev = t
            i += 1
            continue


        if t in ("else", "elseif"):

            flush()
            indent -= 1
            lines.append("\t" * indent + t)
            indent += 1

            prev = t
            i += 1
            continue


        if t in ("then", "do"):

            space()
            add(t)
            flush()

            indent += 1
            block += 1

            prev = t
            i += 1
            continue


        if t == "function":

            if current:
                space()

            add("function")

            prev = t
            i += 1
            continue


        if t == "(":

            if current:

                last = text().rstrip()

                if last.endswith("="):
                    space()

                else:
                    trim()

            add("(")
            paren += 1


        elif t == ")":

            trim()
            add(")")
            paren = max(paren - 1, 0)


        elif t == "[":

            trim()
            add("[")
            bracket += 1


        elif t == "]":

            trim()
            add("]")
            bracket = max(bracket - 1, 0)


        elif t == ".":

            trim()
            add(".")


        elif t == ":":

            trim()
            add(":")


        elif t == ",":

            trim()
            add(", ")


        elif t in operators:

            trim()
            space()
            add(t)
            space()


        elif t == ";":

            add(";")
            flush()


        else:

            if current:

                last = current[-1]

                if not last.endswith(
                    (
                        " ",
                        "(",
                        "[",
                        ".",
                        ":"
                    )
                ):
                    space()

            add(t)


        prev = t
        i += 1


    flush()

    result = "\n".join(lines)

    for k, v in saved.items():
        result = result.replace(k, v)

    return result

def Pretty(code,internet):
    if internet:
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
                    
        except:
            pass

    try:
        return NIntPretty(code)
    except:
        pass
    return code 
