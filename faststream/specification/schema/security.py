from typing import Dict, Literal, Optional

from pydantic import AnyHttpUrl, BaseModel, Field

from faststream._compat import PYDANTIC_V2


class OauthFlowObj(BaseModel):
    """A class to represent an OAuth flow object.

    Attributes:
        authorizationUrl : Optional[AnyHttpUrl] : The URL for authorization
        tokenUrl : Optional[AnyHttpUrl] : The URL for token
        refreshUrl : Optional[AnyHttpUrl] : The URL for refresh
        scopes : Dict[str, str] : The scopes for the OAuth flow

    """

    authorizationUrl: Optional[AnyHttpUrl] = None
    tokenUrl: Optional[AnyHttpUrl] = None
    refreshUrl: Optional[AnyHttpUrl] = None
    scopes: Dict[str, str]

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"


class OauthFlows(BaseModel):
    """A class to represent OAuth flows.

    Attributes:
        implicit : Optional[OauthFlowObj] : Implicit OAuth flow object
        password : Optional[OauthFlowObj] : Password OAuth flow object
        clientCredentials : Optional[OauthFlowObj] : Client credentials OAuth flow object
        authorizationCode : Optional[OauthFlowObj] : Authorization code OAuth flow object

    """

    implicit: Optional[OauthFlowObj] = None
    password: Optional[OauthFlowObj] = None
    clientCredentials: Optional[OauthFlowObj] = None
    authorizationCode: Optional[OauthFlowObj] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"


class SecuritySchemaComponent(BaseModel):
    """A class to represent a security schema component.

    Attributes:
        type : Literal, the type of the security schema component
        name : optional name of the security schema component
        description : optional description of the security schema component
        in_ : optional location of the security schema component
        schema_ : optional schema of the security schema component
        bearerFormat : optional bearer format of the security schema component
        openIdConnectUrl : optional OpenID Connect URL of the security schema component
        flows : optional OAuth flows of the security schema component

    """

    type: Literal[
        "userPassword",
        "apikey",
        "X509",
        "symmetricEncryption",
        "asymmetricEncryption",
        "httpApiKey",
        "http",
        "oauth2",
        "openIdConnect",
        "plain",
        "scramSha256",
        "scramSha512",
        "gssapi",
    ]
    name: Optional[str] = None
    description: Optional[str] = None
    in_: Optional[str] = Field(
        default=None,
        alias="in",
    )
    schema_: Optional[str] = Field(
        default=None,
        alias="schema",
    )
    bearerFormat: Optional[str] = None
    openIdConnectUrl: Optional[str] = None
    flows: Optional[OauthFlows] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
