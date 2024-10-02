from typing import (
    Optional,
)

from pydantic import AnyHttpUrl, BaseModel
from typing_extensions import Required, TypedDict

from faststream._internal._compat import PYDANTIC_V2, EmailStr


class ContactDict(TypedDict, total=False):
    """A class to represent a dictionary of contact information.

    Attributes:
        name : required name of the contact (type: str)
        url : URL of the contact (type: AnyHttpUrl)
        email : email address of the contact (type: EmailStr)
    """

    name: Required[str]
    url: AnyHttpUrl
    email: EmailStr


class Contact(BaseModel):
    """A class to represent a contact.

    Attributes:
        name : name of the contact (str)
        url : URL of the contact (Optional[AnyHttpUrl])
        email : email of the contact (Optional[EmailStr])
    """

    name: str
    url: Optional[AnyHttpUrl] = None
    email: Optional[EmailStr] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
