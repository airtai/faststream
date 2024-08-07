from typing import Dict, List, Optional

from pydantic import BaseModel

from faststream._compat import PYDANTIC_V2

SecurityRequirement = List[Dict[str, List[str]]]


class ServerVariable(BaseModel):
    """A class to represent a server variable.

    Attributes:
        enum : list of possible values for the server variable (optional)
        default : default value for the server variable (optional)
        description : description of the server variable (optional)
        examples : list of example values for the server variable (optional)

    """

    enum: Optional[List[str]] = None
    default: Optional[str] = None
    description: Optional[str] = None
    examples: Optional[List[str]] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
