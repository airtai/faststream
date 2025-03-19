from typing import Any, Dict

from pydantic import BaseModel

from faststream._compat import PYDANTIC_V2

class Route(BaseModel):
    """A class to represent a route.
    
    Attributes:
        method : HTTP method of the route
        path : path of the route
    
    """

    path: str
    method: str