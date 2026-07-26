import re


def Pretty(code):
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
        [A-Za-z_][A-Za-z0-9_]*
        |
        \d+(?:\.\d+)?
        |
        ==|~=|<=|>=|\.\.
        |
        [{}()\[\],;=+\-*/%^#<>.]
        """,
        code,
        flags=re.VERBOSE
    )

    lines = []
    current = []
    indent = 0
    paren = 0

    def flush():
        nonlocal current
        if current:
            text = "".join(current).strip()
            if text:
                lines.append("\t" * indent + text)
            current = []

    def space():
        if current and not current[-1].endswith(" "):
            current.append(" ")

    def ident(x):
        return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", x or ""))

    i = 0
    previous = None

    while i < len(tokens):
        token = tokens[i]
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        nxt2 = tokens[i + 2] if i + 2 < len(tokens) else None

        if token in ("end", "until"):
            flush()
            indent = max(indent - 1, 0)
            lines.append("\t" * indent + token)
            previous = token
            i += 1
            continue

        if token in ("else", "elseif"):
            flush()
            indent = max(indent - 1, 0)
            lines.append("\t" * indent + token)
            indent += 1
            previous = token
            i += 1
            continue

        if token in ("then", "do"):
            space()
            current.append(token)
            flush()
            indent += 1
            previous = token
            i += 1
            continue

        if (
            current
            and ident(token)
            and (
                nxt == "="
                or nxt == "("
            )
            and previous not in (
                "local",
                "function",
                "if",
                "for",
                "while"
            )
        ):
            flush()

        if token == "function":
            if current:
                space()
            current.append("function")
            space()

        elif token == "(":
            current.append("(")
            paren += 1

        elif token == ")":
            if current and current[-1] == " ":
                current.pop()
            current.append(")")
            paren -= 1

        elif token == ",":
            if current and current[-1] == " ":
                current.pop()
            current.append(", ")

        elif token in (
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
            "%"
        ):
            space()
            current.append(token)
            space()

        elif token == ";":
            current.append(";")
            flush()

        else:
            if current and not current[-1].endswith((" ", "(", ".", "[")):
                current.append(" ")
            current.append(token)

        previous = token
        i += 1

    flush()

    result = "\n".join(lines)

    for k, v in saved.items():
        result = result.replace(k, v)

    return result
