from typing import Optional, Union, cast, overload

from pydantic import AnyHttpUrl, BaseModel
from typing_extensions import Self

from faststream._internal._compat import PYDANTIC_V2, EmailStr
from faststream._internal.basic_types import AnyDict
from faststream._internal.utils.data import filter_by_dict
from faststream.specification.schema.extra import (
    Contact as SpecContact,
    ContactDict,
)


class Contact(BaseModel):
    """A class to represent a contact.

    Attributes:
        name : name of the contact (str)
        url : URL of the contact (Optional[AnyHttpUrl])
        email : email of the contact (Optional[EmailStr])
    """

    name: str
    # Use default values to be able build from dict
    url: Optional[AnyHttpUrl] = None
    email: Optional[EmailStr] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"

    @overload
    @classmethod
    def from_spec(cls, contact: None) -> None: ...

    @overload
    @classmethod
    def from_spec(cls, contact: SpecContact) -> Self: ...

    @overload
    @classmethod
    def from_spec(cls, contact: ContactDict) -> Self: ...

    @overload
    @classmethod
    def from_spec(cls, contact: AnyDict) -> AnyDict: ...

    @classmethod
    def from_spec(
        cls, contact: Union[SpecContact, ContactDict, AnyDict, None]
    ) -> Union[Self, AnyDict, None]:
        if contact is None:
            return None

        if isinstance(contact, SpecContact):
            return cls(
                name=contact.name,
                url=contact.url,
                email=contact.email,
            )

        contact = cast("AnyDict", contact)
        contact_data, custom_data = filter_by_dict(ContactDict, contact)

        if custom_data:
            return contact

        return cls(**contact_data)
