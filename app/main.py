import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from ldap3 import Server, Connection, ALL
from dotenv import load_dotenv

from .schemas import LDAPAuthRequest, LDAPAuthResponse, LDAPUserInfo


logger = logging.getLogger("uvicorn.error")


load_dotenv()

LDAP_SERVER = os.getenv("LDAP_SERVER", "")
LDAP_PORT = int(os.getenv("LDAP_PORT", "389"))
LDAP_BIND_DN_SUFFIX = os.getenv("LDAP_BIND_DN", "")
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "")


def authenticate_ldap(login: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with LDAP and return full attributes if successful.

    Returns dict with keys: dn, attributes
    """
    try:
        server = Server(LDAP_SERVER, port=LDAP_PORT, get_info=ALL)
        bind_dn = f"{login}@{LDAP_BIND_DN_SUFFIX}" if LDAP_BIND_DN_SUFFIX else login

        conn = Connection(server, bind_dn, password, auto_bind=True)
        search_filter = f"(sAMAccountName={login})"

        conn.search(LDAP_BASE_DN, search_filter, attributes=["*"])

        if not conn.entries:
            conn.unbind()
            return None

        entry = conn.entries[0]
        try:
            decoded_entry = json.loads(entry.entry_to_json())
            dn = decoded_entry.get("dn", "")
            attrs = decoded_entry.get("attributes", {})
            conn.unbind()
            return {"dn": dn, "attributes": attrs}
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.exception("Failed to decode LDAP entry: %s", e)
            conn.unbind()
            return None
    except Exception as e:
        # Avoid logging sensitive values such as login or password
        logger.warning("LDAP authentication failed: %s", e)
        return None


app = FastAPI(title="LDAP via HTTP", version="1.0.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/auth/ldap", response_model=LDAPAuthResponse)
def auth_ldap(payload: LDAPAuthRequest):
    if not LDAP_SERVER or not LDAP_BASE_DN:
        raise HTTPException(status_code=500, detail="LDAP configuration is missing")

    result = authenticate_ldap(payload.login, payload.password)
    if not result:
        return JSONResponse(
            status_code=401,
            content=LDAPAuthResponse(ok=False, detail="Invalid credentials").model_dump(),
        )

    user = LDAPUserInfo(dn=result["dn"], attributes=result["attributes"])
    return LDAPAuthResponse(ok=True, user=user)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "0") == "1",
    )
