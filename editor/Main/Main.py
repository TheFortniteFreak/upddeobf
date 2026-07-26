import Usage
import sys
import os

def Main(script, *args):

    if "--fixv" in args:
        script = Usage.FixV(script)
    if "--parse" in args:
        script = Usage.Parse(script)
    if "--pretty" in args:
        script = Usage.Pretty(script)

    return script

def main():
    if len(sys.argv) < 2:
        print("Usage: python Parse.py <lua_file.lua>")
        sys.exit(1)

    file_path = sys.argv[1]

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = f"{base_name}_Deobfuscated.lua"

    with open(file_path, "r", encoding="utf-8") as f:
        data = f.read()

    result = Main(data, *sys.argv[2:])

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"Done! Saved as {output_file}")


if __name__ == "__main__":
    main()
