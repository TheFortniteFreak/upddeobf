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


def is_block_start(line):
    return re.match(r"(if|while|for|function)\b", line.strip()) is not None


def find_matching_end(lines, start):
    depth = 0

    for i in range(start, len(lines)):
        s = lines[i].strip()

        if is_block_start(s):
            depth += 1

        elif s == "end":
            depth -= 1

            if depth == 0:
                return i

    return len(lines) - 1


def process_if(lines, start):
    """
    Handles:
        if cond then
        elseif cond then
        else
        end
    """

    branches = []
    current = []

    depth = 0
    i = start

    first = True
    condition = None

    while i < len(lines):
        s = lines[i].strip()

        if first:
            m = re.match(r"if\s+(.+?)\s+then$", s)
            condition = m.group(1)
            branches.append((condition, []))
            first = False
            i += 1
            continue

        # nested blocks
        if is_block_start(s):
            depth += 1
            current.append(lines[i])
            i += 1
            continue

        if s == "end":
            if depth == 0:
                branches[-1][1].extend(current)
                return i, branches
            else:
                depth -= 1
                current.append(lines[i])
                i += 1
                continue

        if depth == 0:
            m = re.match(r"elseif\s+(.+?)\s+then$", s)

            if m:
                branches[-1][1].extend(current)
                current = []
                branches.append((m.group(1), []))
                i += 1
                continue

            if s == "else":
                branches[-1][1].extend(current)
                current = []
                branches.append((None, []))
                i += 1
                continue

        current.append(lines[i])
        i += 1

    return i, branches


def RDead(code):
    lines = code.splitlines()
    out = []

    i = 0

    while i < len(lines):
        s = lines[i].strip()

        # while false
        m = re.match(r"while\s+(.+?)\s+do$", s)

        if m:
            result = eval_cond(m.group(1))

            if result is False:
                i = find_matching_end(lines, i) + 1
                continue

        # if handling
        if re.match(r"if\s+.+\s+then$", s):

            end, branches = process_if(lines, i)

            chosen = None
            unknown = False

            for cond, body in branches:

                if cond is None:
                    if chosen is None:
                        chosen = body
                    break

                result = eval_cond(cond)

                if result is None:
                    unknown = True
                    break

                if result:
                    chosen = body
                    break

            # cannot decide
            if unknown:
                out.extend(lines[i:end + 1])

            else:
                if chosen:
                    out.extend(chosen)

            i = end + 1
            continue

        out.append(lines[i])
        i += 1

    return "\n".join(out)
