from typing import (
    Optional,
    Union,
    overload,
)

from pydantic import AnyHttpUrl, BaseModel
from typing_extensions import Self

from faststream._internal._compat import PYDANTIC_V2, EmailStr
from faststream._internal.basic_types import AnyDict
from faststream.specification import schema as spec


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

    @classmethod
    def from_spec(cls, contact: spec.contact.Contact) -> Self:
        return cls(
            name=contact.name,
            url=contact.url,
            email=contact.email,
        )


@overload
def from_spec(contact: spec.contact.Contact) -> Contact: ...


@overload
def from_spec(contact: spec.contact.ContactDict) -> AnyDict: ...


@overload
def from_spec(contact: AnyDict) -> AnyDict: ...


def from_spec(
    contact: Union[spec.contact.Contact, spec.contact.ContactDict, AnyDict],
) -> Union[Contact, AnyDict]:
    if isinstance(contact, spec.contact.Contact):
        return Contact.from_spec(contact)

    return dict(contact)
