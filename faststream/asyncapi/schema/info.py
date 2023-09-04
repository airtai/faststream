from typing import Any, Callable, Dict, Iterable, Optional, Type, Union

from pydantic import AnyHttpUrl, BaseModel

from faststream._compat import (
    PYDANTIC_V2,
    CoreSchema,
    GetJsonSchemaHandler,
    JsonSchemaValue,
    Required,
    TypedDict,
    general_plain_validator_function,
    is_installed,
)
from faststream.log import logger

if is_installed("email_validator"):
    from pydantic import EmailStr
else:  # pragma: no cover
    # NOTE: EmailStr mock was copied from the FastAPI
    # https://github.com/tiangolo/fastapi/blob/master/fastapi/openapi/models.py#24
    class EmailStr(str):  # type: ignore
        @classmethod
        def __get_validators__(cls) -> Iterable[Callable[..., Any]]:
            yield cls.validate

        @classmethod
        def validate(cls, v: Any) -> str:
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
            return {"type": "string", "format": "email"}

        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            source: Type[Any],
            handler: Callable[[Any], CoreSchema],
        ) -> JsonSchemaValue:
            return general_plain_validator_function(cls._validate)


class ContactDict(TypedDict, total=False):
    name: Required[str]
    url: AnyHttpUrl
    email: EmailStr


class Contact(BaseModel):
    name: str
    url: Optional[AnyHttpUrl] = None
    email: Optional[EmailStr] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"


class LicenseDict(TypedDict, total=False):
    name: Required[str]
    url: AnyHttpUrl


class License(BaseModel):
    name: str
    url: Optional[AnyHttpUrl] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"


class Info(BaseModel):
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
