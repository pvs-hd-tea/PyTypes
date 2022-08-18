import pathlib


def stringify(a):
    return f"{a}"


if __name__ == "__main__":
    print(stringify(1))
    print(stringify("name"))
    print(stringify(pathlib.Path.cwd()))
