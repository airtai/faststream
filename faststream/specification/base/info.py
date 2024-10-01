from pydantic import BaseModel

from faststream._internal._compat import PYDANTIC_V2


class BaseInfo(BaseModel):
    """A class to represent basic application information.

    Attributes:
        title : application title
        version : application version (default: "1.0.0")
        description : application description (default: "")
    """

    title: str
    version: str = "1.0.0"
    description: str = ""

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
