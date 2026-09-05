from typing import Annotated, get_type_hints


def QueryParameterConstraint(min_length: int = 0, max_length: int = 50):
    return {"min_length": min_length, "max_length": max_length}


def my_function(value: Annotated[str, QueryParameterConstraint(10, 30)]):
    print(value)


my_function("hello")

hints = get_type_hints(my_function, include_extras=True)
print(hints["value"].__metadata__)
