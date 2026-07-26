import tempfile
import os
import luastyle

def Pretty(code):
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".lua",
        delete=False
    ) as f:
        f.write(code)
        filename = f.name

    try:
        with open(filename, "r", encoding="utf-8") as f:
            lua_code = f.read()

        # Use the imported luastyle package here
        return luastyle.format(lua_code)

    finally:
        os.remove(filename)
