import re


def Pretty(code):
    saved = {}
    counter = 0

    def protect(m):
        nonlocal counter
        k = f"___LUA_LITERAL_{counter}___"
        saved[k] = m.group(0)
        counter += 1
        return k

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

    def emit():
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

    def remove_space():
        if current and current[-1] == " ":
            current.pop()

    def ident(x):
        return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", x or ""))

    keywords_block = {
        "if",
        "for",
        "while",
        "repeat",
        "function"
    }

    i = 0
    prev = None

    while i < len(tokens):
        t = tokens[i]
        n = tokens[i + 1] if i + 1 < len(tokens) else None

        if t == "end":
            if paren == 0 and bracket == 0 and block > 0:
                emit()
                indent = max(indent - 1, 0)
                block -= 1
                lines.append("\t" * indent + "end")
            else:
                space()
                add("end")

            prev = t
            i += 1
            continue

        if t == "until":
            emit()
            indent = max(indent - 1, 0)
            lines.append("\t" * indent + "until")
            prev = t
            i += 1
            continue

        if t in ("else", "elseif"):
            emit()
            indent = max(indent - 1, 0)
            lines.append("\t" * indent + t)
            indent += 1
            prev = t
            i += 1
            continue

        if t in ("then", "do"):
            space()
            add(t)
            emit()
            indent += 1
            block += 1
            prev = t
            i += 1
            continue

        if t == "function":
            if current and current[-1] != " ":
                space()
            add("function")
            prev = t
            i += 1
            continue

        if t == "(":
            remove_space()
            add("(")
            paren += 1

        elif t == ")":
            remove_space()
            add(")")
            paren = max(0, paren - 1)

        elif t == "[":
            remove_space()
            add("[")
            bracket += 1

        elif t == "]":
            remove_space()
            add("]")
            bracket = max(0, bracket - 1)

        elif t == ".":
            remove_space()
            add(".")

        elif t == ",":
            remove_space()
            add(", ")

        elif t == ";":
            add(";")
            emit()

        elif t in {
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
        }:
            space()
            add(t)
            space()

        else:
            if current:
                last = current[-1]
                if (
                    not last.endswith((" ", "(", "[", ".", ":"))
                    and t not in (")", "]")
                ):
                    space()

            add(t)

        if (
            t == "local"
            and n == "function"
        ):
            pass

        prev = t
        i += 1

    emit()

    result = "\n".join(lines)

    for k, v in saved.items():
        result = result.replace(k, v)

    return result
