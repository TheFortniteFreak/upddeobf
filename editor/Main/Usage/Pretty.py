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
        [{}()\[\],;=+\-*/%^<>.]
        """,
        code,
        flags=re.VERBOSE
    )

    lines = []
    current = []

    indent = 0
    paren = 0
    function_mode = None
    function_header = False

    statement_words = {
        "if",
        "for",
        "while",
        "function",
        "local",
        "return",
        "repeat"
    }

    def flush():
        nonlocal current
        if current:
            text = "".join(current).strip()
            if text:
                lines.append("\t" * indent + text)
            current = []

    def add(x):
        current.append(x)

    def space():
        if current and not current[-1].endswith(" "):
            current.append(" ")

    previous = None

    for token in tokens:

        if token in ("end", "until"):
            flush()
            indent = max(indent - 1, 0)
            lines.append("\t" * indent + token)
            previous = token
            continue

        if token in ("else", "elseif"):
            flush()
            indent = max(indent - 1, 0)
            lines.append("\t" * indent + token)
            indent += 1
            previous = token
            continue

        if token == "function":

            function_mode = "expression" if previous == "=" else "declaration"

            add("function")
            space()

            function_header = True

            previous = token
            continue


        if function_header:

            add(token)

            if token == "(":
                paren += 1

            elif token == ")":
                paren -= 1

                if paren == 0:
                    flush()
                    indent += 1
                    function_header = False

            previous = token
            continue


        if token in ("then", "do"):

            space()
            add(token)
            flush()
            indent += 1

            previous = token
            continue


        if (
            token in statement_words
            and current
            and previous not in ("then", "do", "=")
        ):
            flush()


        if token == "(":
            add("(")

        elif token == ")":

            if current and current[-1] == " ":
                current.pop()

            add(")")


        elif token == ",":

            if current and current[-1] == " ":
                current.pop()

            add(", ")


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
            add(token)
            space()


        elif token == ";":

            add(";")
            flush()


        else:

            if current:
                last = current[-1]

                if (
                    not last.endswith((" ", "(", ".", "["))
                    and token not in (")", "]")
                ):
                    space()

            add(token)


        previous = token


    flush()

    result = "\n".join(lines)

    for k, v in saved.items():
        result = result.replace(k, v)

    return result
