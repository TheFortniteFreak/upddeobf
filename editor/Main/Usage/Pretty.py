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

    code = re.sub(r"\s*([=+\-*\/<>])\s*", r" \1 ", code)

    code = re.sub(r"\s*,\s*", ", ", code)

    code = re.sub(r"\(\s*", "(", code)
    code = re.sub(r"\s*\)", ")", code)

    code = re.sub(
        r'\s+(?=(local\s+|function\s+|if\s+|elseif\s+|else\b|for\s+|while\s+|repeat\b|return\s+|print\s*\(|[A-Za-z_][A-Za-z0-9_]*\s*=))',
        "\n",
        code
    )

    code = re.sub(r"\s*(then)\s*", r" \1\n", code)
    code = re.sub(r"\s*(do)\s*", r" \1\n", code)
    code = re.sub(r"\s*(else)\s*", r"\nelse\n", code)
    code = re.sub(r"\s*(elseif)\s*", r"\nelseif ", code)
    code = re.sub(r"\s*(end)\s*", r"\nend\n", code)

    code = re.sub(r"\n\s*\n+", "\n\n", code)

    lines = code.split("\n")

    output = []
    indent = 0

    closing = (
        "end",
        "else",
        "elseif"
    )

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith(closing):
            indent = max(indent - 1, 0)

        output.append("    " * indent + line)

        if (
            line.startswith("function ")
            or line.startswith("if ")
            or line.startswith("for ")
            or line.startswith("while ")
            or line.startswith("repeat")
            or line.endswith("then")
            or line.endswith("do")
        ):
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
