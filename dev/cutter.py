import re

def cut_parts(ori_code: str):
    declaration: str = re.search("(.+)(?=/\* --- FUNCTIONS --- \*/)", ori_code, re.S).group()
    functions_definition: str = re.search("/\* --- FUNCTIONS --- \*/(.+)(?=int main)", ori_code, re.S).group()
    functions: list[str] = re.findall("\n([^\n]+func_\d+?\([^;]*?\)\s?\{.+?\n})", functions_definition, re.S)
    main: str = re.search("int main \(int argc, char\* argv\[]\)\n{.+?\n}", ori_code, re.S).group()

    with open("declaration.h", "w") as f:
        f.write(declaration)

    for func in functions:
        func_name: str = re.search("func_\d+", func).group()
        with open(f"{func_name}.c", "w") as f:
            f.write("#include \"declaration.h\"\n\n")
            f.write(func)

    with open("main.c", "w") as f:
        f.write("#include \"declaration.h\"\n\n")
        f.write(main)



if __name__ == "__main__":
    with open("orig.c", "r") as f:
        code = f.read()
    cut_parts(code)