import requests
from fastapi import HTTPException, Header

AUTH_SERVICE = "http://auth-service"

def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        res = requests.get(
            f"{AUTH_SERVICE}/validate",
            headers={"Authorization": authorization},
            timeout=2
        )

        if res.status_code != 200:
            raise Exception()

        return res.json()

    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")