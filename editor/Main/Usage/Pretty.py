import subprocess
import sys

package = "luastyle"

subprocess.check_call([
    sys.executable,
    "-m",
    "pip",
    "install",
    package
])

import luastyle

def Pretty(code):
    return luastyle.format(code)
