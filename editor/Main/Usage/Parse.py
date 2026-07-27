import re
import ast
import operator


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


        if isinstance(node, ast.Call):

            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "len"
            ):
                return len(calc(node.args[0]))


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



def decode_strings(lua):

    def convert(m):

        x = m.group(0)


        if x.startswith("\\x"):
            return chr(int(x[2:], 16))


        if x.startswith("\\u{"):
            return chr(int(x[3:-1], 16))


        if x.startswith("\\u"):
            return chr(int(x[2:], 16))


        if re.fullmatch(r"\\[0-9]{1,3}", x):
            return chr(int(x[1:], 10))


        return {
            "\\n": "\n",
            "\\r": "\r",
            "\\t": "\t",
            "\\\\": "\\",
            '\\"': '"',
            "\\'": "'"
        }.get(x, x)



    def repl(m):

        body = m.group(2)


        body = re.sub(
            r"\\u\{[0-9a-fA-F]+\}|\\u[0-9a-fA-F]{4}|\\x[0-9a-fA-F]{2}|\\[0-9]{1,3}|\\.",
            convert,
            body
        )


        return m.group(1) + body + m.group(1)



    return re.sub(
        r'(["\'])(.*?)(?<!\\)\1',
        repl,
        lua,
        flags=re.S
    )



def decode_char(lua):

    while True:

        changed = False


        for m in re.finditer(
            r"string\.char\(",
            lua
        ):

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

                value = "".join(
                    chr(int(x.strip()))
                    for x in split_args(inside)
                )


                lua = (
                    lua[:start]
                    +
                    '"' + value + '"'
                    +
                    lua[pos + 1:]
                )


                changed = True
                break


            except:
                pass


        if not changed:
            break


    return lua



def decode_length(lua):

    lua = re.sub(
        r'#((?:"(?:\\.|[^"])*")|(?:\'(?:\\.|[^\'])*\'))',
        lambda m: str(len(ast.literal_eval(m.group(1)))),
        lua
    )


    return lua



def decode_compare(lua):

    pattern = (
        r'("(?:\\.|[^"])*"|\'(?:\\.|[^\'])*\'|\d+(?:\.\d+)?)'
        r'\s*(==|~=|<=|>=|<|>)\s*'
        r'("(?:\\.|[^"])*"|\'(?:\\.|[^\'])*\'|\d+(?:\.\d+)?)'
    )


    def repl(m):

        try:

            a = ast.literal_eval(m.group(1)) \
                if m.group(1)[0] in "\"'" \
                else float(m.group(1))

            b = ast.literal_eval(m.group(3)) \
                if m.group(3)[0] in "\"'" \
                else float(m.group(3))


            return (
                "true"
                if compare_ops[m.group(2)](a, b)
                else "false"
            )


        except:

            return m.group(0)



    return re.sub(
        pattern,
        repl,
        lua
    )



def decode_math(lua):

    pattern = r"(?<![\w\"'])(\d+(?:\.\d+)?(?:\s*[\+\-\*/\^]\s*\d+(?:\.\d+)?)+)(?![\w\"'])"


    def repl(m):

        try:

            value = safe_eval(m.group(1))


            if isinstance(value, float) and value.is_integer():
                value = int(value)


            return str(value)


        except:

            return m.group(0)



    return re.sub(
        pattern,
        repl,
        lua
    )



def Parse(lua):

    old = None


    while old != lua:

        old = lua

        lua = decode_char(lua)
        lua = decode_strings(lua)
        lua = decode_length(lua)
        lua = decode_compare(lua)
        lua = decode_math(lua)


    return lua
