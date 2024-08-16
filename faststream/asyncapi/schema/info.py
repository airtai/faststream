from typing import Any, Callable, Dict, Iterable, Optional, Type, Union

from pydantic import AnyHttpUrl, BaseModel
from typing_extensions import Required, TypedDict

from faststream._compat import (
    PYDANTIC_V2,
    CoreSchema,
    GetJsonSchemaHandler,
    JsonSchemaValue,
    with_info_plain_validator_function,
)
from faststream.log import logger

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
            return with_info_plain_validator_function(cls._validate)


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


class LicenseDict(TypedDict, total=False):
    """A dictionary-like class to represent a license.

    Attributes:
        name : required name of the license (type: str)
        url : URL of the license (type: AnyHttpUrl)

    """

    name: Required[str]
    url: AnyHttpUrl


class License(BaseModel):
    """A class to represent a license.

    Attributes:
        name : name of the license
        url : URL of the license (optional)

    Config:
        extra : allow additional attributes in the model (PYDANTIC_V2)

    """

    name: str
    url: Optional[AnyHttpUrl] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"


class Info(BaseModel):
    """A class to represent information.

    Attributes:
        title : title of the information
        version : version of the information (default: "1.0.0")
        description : description of the information (default: "")
        termsOfService : terms of service for the information (default: None)
        contact : contact information for the information (default: None)
        license : license information for the information (default: None)

    """

    title: str
    version: str = "1.0.0"
    description: str = ""
    termsOfService: Optional[AnyHttpUrl] = None
    contact: Optional[Union[Contact, ContactDict, Dict[str, Any]]] = None
    license: Optional[Union[License, LicenseDict, Dict[str, Any]]] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
