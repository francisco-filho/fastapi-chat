import tomli
with open("pyproject.toml", "rb") as f:
    p = tomli.load(f)
    print(p["project"]["version"])

