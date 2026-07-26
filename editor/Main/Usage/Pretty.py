import subprocess
import sys
import tempfile
import os

package = "luastyle"

subprocess.check_call([
    sys.executable,
    "-m",
    "pip",
    "install",
    package
])

def Pretty(code):
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".lua",
        delete=False
    ) as f:
        f.write(code)
        filename = f.name

    try:
        result = subprocess.run(
            ["luastyle", filename],
            capture_output=True,
            text=True
        )

        return result.stdout
    finally:
        os.remove(filename)
