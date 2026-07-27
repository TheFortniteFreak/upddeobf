import re
import ast
import operator
import sys
import os


ops = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
}


compare_ops = {
    "==": operator.eq,
    "~=": operator.ne,
    "<": operator.lt,
    ">": operator.gt,
    "<=": operator.le,
    ">=": operator.ge,
}


def safe_eval(expr):
    expr = expr.replace("^", "**")

    tree = ast.parse(expr, mode="eval")

    def calc(node):
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.BinOp):
            return ops[type(node.op)](
                calc(node.left),
                calc(node.right)
            )

        if isinstance(node, ast.UnaryOp):
            return -calc(node.operand)

        raise ValueError()

    return calc(tree.body)


def split_args(s):
    out = []
    cur = ""
    depth = 0

    for c in s:
        if c == "(":
            depth += 1

        elif c == ")":
            depth -= 1

        if c == "," and depth == 0:
            out.append(cur)
            cur = ""

        else:
            cur += c

    if cur:
        out.append(cur)

    return out


def decode_char(lua):
    while True:
        found = False

        for m in re.finditer(r"string\.char\(", lua):

            start = m.start()
            pos = m.end()
            depth = 1

            while pos < len(lua):

                if lua[pos] == "(":
                    depth += 1

                elif lua[pos] == ")":
                    depth -= 1

                    if depth == 0:
                        break

                pos += 1

            inside = lua[m.end():pos]

            try:
                chars = []

                for x in split_args(inside):
                    chars.append(chr(int(x.strip())))

                lua = (
                    lua[:start]
                    +
                    repr("".join(chars))
                    +
                    lua[pos + 1:]
                )

                found = True
                break

            except:
                pass

        if not found:
            break

    return lua


def decode_strings(lua):

    def decode_content(s):

        def convert(match):
            x = match.group(0)

            if x.startswith("\\x"):
                try:
                    return chr(int(x[2:], 16))
                except:
                    return x

            if x.startswith("\\u{"):
                try:
                    return chr(int(x[3:-1], 16))
                except:
                    return x

            if x.startswith("\\u"):
                try:
                    return chr(int(x[2:], 16))
                except:
                    return x

            if re.fullmatch(r"\\[0-9]{1,3}", x):
                try:
                    return chr(int(x[1:], 10))
                except:
                    return x

            escapes = {
                "\\n": "\n",
                "\\r": "\r",
                "\\t": "\t",
                "\\\\": "\\",
                '\\"': '"',
                "\\'": "'",
            }

            return escapes.get(x, x)

        return re.sub(
            r"\\u\{[0-9a-fA-F]+\}|\\u[0-9a-fA-F]{4}|\\x[0-9a-fA-F]{2}|\\[0-9]{1,3}|\\.",
            convert,
            s
        )

    def repl(m):
        return (
            m.group(1)
            +
            decode_content(m.group(2))
            +
            m.group(1)
        )

    return re.sub(
        r'(["\'])(.*?)(?<!\\)\1',
        repl,
        lua,
        flags=re.S
    )


def decode_length(lua):

    def repl(m):
        try:
            return str(len(m.group(2)))
        except:
            return m.group(0)

    return re.sub(
        r'#(["\'])(.*?)(?<!\\)\1',
        repl,
        lua,
        flags=re.S
    )


def decode_compare(lua):

    def repl(m):

        left = m.group(1)
        op = m.group(2)
        right = m.group(3)

        try:

            if left[0] in "\"'" and right[0] in "\"'":
                left = ast.literal_eval(left)
                right = ast.literal_eval(right)

            else:
                left = safe_eval(left)
                right = safe_eval(right)

            result = compare_ops[op](left, right)

            return "true" if result else "false"

        except:
            return m.group(0)


    pattern = (
        r'(".*?"|\'.*?\'|[0-9\.\+\-\*/\^]+)'
        r'\s*(==|~=|<=|>=|<|>)\s*'
        r'(".*?"|\'.*?\'|[0-9\.\+\-\*/\^]+)'
    )

    old = None

    while old != lua:
        old = lua
        lua = re.sub(pattern, repl, lua)

    return lua


def decode_math(lua):

    pattern = r"(?<![\w\"'])((?:\d+(?:\.\d+)?|\s|[\+\-\*/%\^])+)(?![\w\"'])"


    def repl(m):

        expr = m.group(1).strip()

        if not re.search(r"[\+\-\*/%\^]", expr):
            return m.group(0)

        try:

            result = safe_eval(expr)

            if isinstance(result, float) and result.is_integer():
                result = int(result)

            return str(result)

        except:
            return m.group(0)


    old = None

    while old != lua:
        old = lua
        lua = re.sub(pattern, repl, lua)

    return lua


def Parse(lua):

    last = None

    while last != lua:

        last = lua

        lua = decode_char(lua)
        lua = decode_strings(lua)
        lua = decode_length(lua)
        lua = decode_compare(lua)
        lua = decode_math(lua)

    return lua
