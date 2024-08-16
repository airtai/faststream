from typing import (
    Any,
    Callable,
    Iterable,
    Optional,
    Type,
    Union,
    overload,
)

from pydantic import AnyHttpUrl, BaseModel
from typing_extensions import Self

from faststream._compat import (
    PYDANTIC_V2,
    CoreSchema,
    GetJsonSchemaHandler,
    JsonSchemaValue,
    with_info_plain_validator_function,
)
from faststream.log import logger
from faststream.specification import schema as spec
from faststream.types import AnyDict

try:
    import email_validator

    if email_validator is None:
        raise ImportError
    from pydantic import EmailStr

except ImportError:  # pragma: no cover
    # NOTE: EmailStr mock was copied from the FastAPI
    # https://github.com/tiangolo/fastapi/blob/master/fastapi/openapi/models.py#24
    class EmailStr(str):  # type: ignore
        """EmailStr is a string that should be an email.

        Note: EmailStr mock was copied from the FastAPI:
        https://github.com/tiangolo/fastapi/blob/master/fastapi/openapi/models.py#24

        """

        @classmethod
        def __get_validators__(cls) -> Iterable[Callable[..., Any]]:
            """Returns the validators for the EmailStr class."""
            yield cls.validate

        @classmethod
        def validate(cls, v: Any) -> str:
            """Validates the EmailStr class."""
            logger.warning(
                "email-validator bot installed, email fields will be treated as str.\n"
                "To install, run: pip install email-validator"
            )
            return str(v)

        @classmethod
        def _validate(cls, __input_value: Any, _: Any) -> str:
            logger.warning(
                "email-validator bot installed, email fields will be treated as str.\n"
                "To install, run: pip install email-validator"
            )
            return str(__input_value)

        @classmethod
        def __get_pydantic_json_schema__(
            cls,
            core_schema: CoreSchema,
            handler: GetJsonSchemaHandler,
        ) -> JsonSchemaValue:
            """Returns the JSON schema for the EmailStr class.

            Args:
                core_schema : the core schema
                handler : the handler
            """
            return {"type": "string", "format": "email"}

        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            source: Type[Any],
            handler: Callable[[Any], CoreSchema],
        ) -> JsonSchemaValue:
            """Returns the core schema for the EmailStr class.

            Args:
                source : the source
                handler : the handler
            """
            return with_info_plain_validator_function(cls._validate)  # type: ignore[no-any-return]


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
        contact: Union[spec.contact.Contact, spec.contact.ContactDict, AnyDict]
) -> Union[Contact, AnyDict]:
    if isinstance(contact, spec.contact.Contact):
        return Contact.from_spec(contact)

    return dict(contact)
