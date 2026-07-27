import re

def eval_cond(cond):
    cond = cond.strip()

    if cond == "false":
        return False
    if cond == "true":
        return True

    try:
        return bool(eval(cond, {"__builtins__": None}, {}))
    except:
        return None

def RDead(code):
    lines = code.splitlines()
    out = []
    skip = False
    depth = 0

    for line in lines:
        s = line.strip()

        m = re.match(r"while\s+(.+?)\s+do$", s)
        if not skip and m:
            result = eval_cond(m.group(1))
            if result is False:
                skip = True
                depth = 1
                continue

        m = re.match(r"if\s+(.+?)\s+then$", s)
        if not skip and m:
            result = eval_cond(m.group(1))
            if result is False:
                skip = True
                depth = 1
                continue

        if skip:
            if re.match(r"(if|while|for|function)\b", s):
                depth += 1
            elif s == "end":
                depth -= 1
                if depth == 0:
                    skip = False
            continue

        out.append(line)

    return "\n".join(out)
