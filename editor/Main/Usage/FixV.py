import re

def FixV(code):
    var_counter = 1
    func_counter = 1

    variables = {}
    functions = {}

    # Protect strings/comments
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


    # Functions
    def replace_function(match):
        nonlocal func_counter

        prefix = match.group(1) or ""
        old = match.group(2)

        if old not in functions:
            functions[old] = f"f{func_counter}"
            func_counter += 1

        return f"{prefix}function {functions[old]}"


    code = re.sub(
        r"\b(local\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)",
        replace_function,
        code
    )


    # Variables only when assigned
    def replace_variable(match):
        nonlocal var_counter

        old = match.group(1)

        if old not in variables:
            variables[old] = f"v{var_counter}"
            var_counter += 1

        return variables[old] + match.group(2)


    code = re.sub(
        r"(?<![A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*)",
        replace_variable,
        code
    )


    # Replace references
    for old, new in functions.items():
        code = re.sub(
            rf"(?<![A-Za-z0-9_]){re.escape(old)}(?![A-Za-z0-9_])",
            new,
            code
        )


    for old, new in variables.items():
        code = re.sub(
            rf"(?<![A-Za-z0-9_]){re.escape(old)}(?![A-Za-z0-9_])",
            new,
            code
        )


    # Restore strings/comments
    def restore(match):
        return protected[int(match.group(1))]


    code = re.sub(
        r"___PROTECTED_(\d+)___",
        restore,
        code
    )

    return code