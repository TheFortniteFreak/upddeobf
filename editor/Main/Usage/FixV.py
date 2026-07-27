import re

def FixV(code):
    var_counter = 1
    func_counter = 1

    variables = {}
    functions = {}

    protected = []

    def protect(match):
        protected.append(match.group(0))
        return f"\x00PROTECTED{len(protected)-1}\x00"


    code = re.sub(
        r'(--\[\[.*?\]\]|--[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\[\[.*?\]\])',
        protect,
        code,
        flags=re.S
    )


    def new_var(old):
        nonlocal var_counter

        if old not in variables:
            variables[old] = f"v{var_counter}"
            var_counter += 1

        return variables[old]


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


    def replace_params(match):

        func = match.group(1)
        params = match.group(2)

        if not params.strip():
            return f"{func}()"

        result = []

        for p in params.split(","):

            p = p.strip()

            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", p):
                result.append(new_var(p))

            else:
                result.append(p)


        return f"{func}({','.join(result)})"


    code = re.sub(
        r"\b(function\s+f\d+)\s*\(([^)]*)\)",
        replace_params,
        code
    )


    def replace_for(match):

        vars_part = match.group(1)
        names = []

        for v in vars_part.split(","):

            v = v.strip()

            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", v):
                names.append(new_var(v))

            else:
                names.append(v)


        return "for " + ",".join(names) + " in"


    code = re.sub(
        r"\bfor\s+([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)\s+in\b",
        replace_for,
        code
    )


    def replace_local(match):
        return "local " + new_var(match.group(1))


    code = re.sub(
        r"\blocal\s+([A-Za-z_][A-Za-z0-9_]*)",
        replace_local,
        code
    )


    def replace_assignment(match):

        return new_var(match.group(1)) + match.group(2)


    code = re.sub(
        r"(?<![#A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*)",
        replace_assignment,
        code
    )

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

    code = re.sub(
        r"\x00PROTECTED(\d+)\x00",
        lambda m: protected[int(m.group(1))],
        code
    )


    return code
