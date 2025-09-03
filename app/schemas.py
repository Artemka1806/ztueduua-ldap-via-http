from pydantic import BaseModel, Field
from typing import Any, Dict, Optional


class LDAPAuthRequest(BaseModel):
    login: str = Field(..., description="User login (e.g., sAMAccountName)")
    password: str = Field(..., description="User password")


class LDAPUserInfo(BaseModel):
    dn: str = Field(..., description="Distinguished Name of the user entry")
    attributes: Dict[str, Any] = Field(
        ..., description="All attributes returned by LDAP for the user"
    )


class LDAPAuthResponse(BaseModel):
    ok: bool
    user: Optional[LDAPUserInfo] = None
    detail: Optional[str] = None
