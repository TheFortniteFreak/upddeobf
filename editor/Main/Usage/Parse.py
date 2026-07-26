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


def safe_eval(expr):

    # Lua exponent operator -> Python exponent operator
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



def decode_math(lua):

    # Match math expressions that are not part of identifiers
    pattern = r"(?<![\w\"'])((?:\d+(?:\.\d+)?|\s|[\+\-\*/%\^])+)(?![\w\"'])"

    def repl(m):

        expr = m.group(1).strip()

        # Ignore single numbers
        if not re.search(r"[\+\-\*/%\^]", expr):
            return m.group(0)

        try:
            result = safe_eval(expr)

            # Lua usually wants integers
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

                    chars.append(
                        chr(int(x.strip()))
                    )


                lua = (
                    lua[:start]
                    +
                    repr("".join(chars))
                    +
                    lua[pos+1:]
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


            # Hex: \x41
            if x.startswith("\\x"):

                try:
                    return chr(int(x[2:], 16))

                except:
                    return x



            # Decimal: \116
            if x[1:].isdigit():

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
            r"\\x[0-9a-fA-F]{2}|\\[0-9]{1,3}|\\.",
            convert,
            s
        )



    def repl(m):

        quote = m.group(1)
        content = m.group(2)

        return quote + decode_content(content) + quote



    return re.sub(
        r'(["\'])(.*?)(?<!\\)\1',
        repl,
        lua,
        flags=re.S
    )







def Parse(lua):

    last = None

    while last != lua:

        last = lua

        lua = decode_math(lua)

        lua = decode_char(lua)

        lua = decode_strings(lua)


    return lua