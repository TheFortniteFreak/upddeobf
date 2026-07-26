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

    code = re.sub(
        r"\s+(?=(local|function|if|for|while|repeat|return|break)\b)",
        "\n",
        code
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
        [{}()\[\],;=+\-*/%^#<>.]
        """,
        code,
        flags=re.VERBOSE
    )

    lines = []
    current = []
    indent = 0
    paren = 0
    bracket = 0

    def flush():
        nonlocal current
        if current:
            s = "".join(current).strip()
            if s:
                lines.append("\t" * indent + s)
            current = []

    def space():
        if current and not current[-1].endswith(" "):
            current.append(" ")

    def is_ident(x):
        return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", x or ""))

    i = 0
    previous = None

    while i < len(tokens):
        token = tokens[i]
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None

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
            token == "local"
            and current
            and paren == 0
            and bracket == 0
        ):
            flush()

        if (
            is_ident(token)
            and nxt == "="
            and current
            and paren == 0
            and bracket == 0
            and previous not in (
                "local",
                "function"
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
            paren = max(paren - 1, 0)

        elif token == "[":
            current.append("[")
            bracket += 1

        elif token == "]":
            if current and current[-1] == " ":
                current.pop()
            current.append("]")
            bracket = max(bracket - 1, 0)

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
            "%",
            "^"
        ):
            space()
            current.append(token)
            space()

        elif token == ";":
            current.append(";")
            flush()

        else:
            if current and not current[-1].endswith((" ", "(", "[", ".")):
                current.append(" ")
            current.append(token)

        previous = token
        i += 1

    flush()

    result = "\n".join(lines)

    for k, v in saved.items():
        result = result.replace(k, v)

    return result
