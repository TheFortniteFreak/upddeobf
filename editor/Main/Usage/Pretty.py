import re

def Pretty(code):
    protected = []

    def protect(match):
        protected.append(match.group(0))
        return f"___PROTECTED_{len(protected)-1}___"

    code = re.sub(
        r'(--\[\[.*?\]\]|--[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\[\[.*?\]\])',
        protect,
        code,
        flags=re.S
    )

    code = code.replace("\r\n", "\n").replace("\r", "\n")

    code = re.sub(
        r"\s*(==|~=|<=|>=|//|\.{3}|[=+\-*\/<>])\s*",
        r" \1 ",
        code
    )

    code = re.sub(r"\s*,\s*", ", ", code)

    code = re.sub(r"\(\s*", "(", code)
    code = re.sub(r"\s*\)", ")", code)

    code = re.sub(
        r"(___PROTECTED_\d+___|\b[A-Za-z_][A-Za-z0-9_\.\[\]]*)\s+"
        r"(?=(local\b|function\b|if\b|for\b|while\b|return\b|print\s*\())",
        r"\1\n",
        code
    )

    code = re.sub(
        r"(\S.*?=.*?)\s+(?=[A-Za-z_][A-Za-z0-9_\.\[\]]*\s*=)",
        r"\1\n",
        code
    )

    code = re.sub(r"\s*(then)\s*", r" \1\n", code)
    code = re.sub(r"\s*(do)\s*", r" \1\n", code)

    code = re.sub(
        r"\s*elseif\s+",
        "\nelseif ",
        code
    )

    code = re.sub(
        r"\s*else\s*(?!if\b)",
        "\nelse\n",
        code
    )

    code = re.sub(
        r"\s*(end)\s*",
        "\nend\n",
        code
    )

    code = re.sub(
        r"\n\s*\n+",
        "\n\n",
        code
    )


    lines = code.split("\n")

    output = []
    indent = 0

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if (
            line == "end"
            or line.startswith("end ")
            or line.startswith("else")
            or line.startswith("elseif")
            or line.startswith("until")
        ):
            indent = max(indent - 1, 0)


        output.append("    " * indent + line)


        opens = False

        if re.search(r"\bfunction\s*\(", line):
            opens = True

        elif re.match(r"^(local\s+)?function\b", line):
            opens = True

        elif re.match(r"^if\b.*\bthen$", line):
            opens = True

        elif re.match(r"^for\b.*\bdo$", line):
            opens = True

        elif re.match(r"^while\b.*\bdo$", line):
            opens = True

        elif line == "repeat":
            opens = True


        if opens:
            indent += 1


        if line.startswith("until"):
            indent = max(indent - 1, 0)


    code = "\n".join(output)

    def restore(match):
        return protected[int(match.group(1))]

    code = re.sub(
        r"___PROTECTED_(\d+)___",
        restore,
        code
    )

    return code
