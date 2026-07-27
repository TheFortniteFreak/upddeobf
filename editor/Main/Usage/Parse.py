import re
import ast
import operator


variables = {}


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


        if isinstance(node, ast.Name):

            if node.id in variables:
                return variables[node.id]

            raise ValueError()


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



def decode_vars(lua):

    def repl(m):

        name = m.group(1)
        value = m.group(2).strip()


        try:

            if value == "true":
                variables[name] = True

            elif value == "false":
                variables[name] = False

            elif value == "nil":
                variables[name] = None

            elif value[0] in "\"'":
                variables[name] = ast.literal_eval(value)

            else:
                variables[name] = safe_eval(value)


            return ""


        except:

            return m.group(0)



    return re.sub(
        r"(?:local\s+)?([A-Za-z_]\w*)\s*=\s*(?![=])([^\n]+)",
        repl,
        lua
    )



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

    def convert(match):

        x = match.group(0)


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
            "\\'": "'",
        }.get(x, x)



    return re.sub(
        r'(["\'])(.*?)(?<!\\)\1',
        lambda m:
            m.group(1)
            +
            re.sub(
                r"\\u\{[0-9a-fA-F]+\}|\\u[0-9a-fA-F]{4}|\\x[0-9a-fA-F]{2}|\\[0-9]{1,3}|\\.",
                convert,
                m.group(2)
            )
            +
            m.group(1),
        lua,
        flags=re.S
    )



def decode_length(lua):
    lua = re.sub(
        r'#((?:"(?:\\.|[^"])*")|(?:\'(?:\\.|[^\'])*\'))',
        r'len(\1)',
        lua
    )


    lua = re.sub(
        r'#([A-Za-z_]\w*)',
        r'len(\1)',
        lua
    )


    return lua



def decode_compare(lua):

    def repl(m):

        left = m.group(1)
        op = m.group(2)
        right = m.group(3)


        try:

            left = safe_eval(left)
            right = safe_eval(right)


            return (
                "true"
                if compare_ops[op](left, right)
                else "false"
            )


        except:

            return m.group(0)



    pattern = (
        r'([A-Za-z_][\w]*\([^)]*\)|".*?"|\'.*?\'|[\d\.\+\-\*/\^]+|true|false)'
        r'\s*(==|~=|<=|>=|<|>)\s*'
        r'([A-Za-z_][\w]*\([^)]*\)|".*?"|\'.*?\'|[\d\.\+\-\*/\^]+|true|false)'
    )


    old = None

    while old != lua:

        old = lua
        lua = re.sub(pattern, repl, lua)


    return lua



def decode_math(lua):

    pattern = r"(?<![\w\"'])((?:\d+(?:\.\d+)?|\s|[\+\-\*/%\^])+)(?![\w\"'])"


    def repl(m):

        try:

            result = safe_eval(
                m.group(1).strip()
            )


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

    global variables

    variables = {}


    last = None


    while last != lua:

        last = lua

        lua = decode_vars(lua)
        lua = decode_char(lua)
        lua = decode_strings(lua)
        lua = decode_length(lua)
        lua = decode_compare(lua)
        lua = decode_math(lua)


    return lua
