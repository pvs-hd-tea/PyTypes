def function(parameter: int | None) -> str | int:
    if parameter is None:
        return "string"
    return parameter
