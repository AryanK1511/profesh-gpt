import base64
from typing import Any, Dict

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from src.common.config import settings


class JWKSClient:
    def __init__(self, jwks_url: str):
        self.jwks_url = jwks_url
        self._keys_cache: Dict[str, Any] = None

    def get_jwks(self) -> Dict[str, Any]:
        if self._keys_cache is None:
            try:
                response = requests.get(self.jwks_url, timeout=10)
                response.raise_for_status()
                self._keys_cache = response.json()
            except requests.RequestException as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to fetch JWKS: {str(e)}"
                )
        return self._keys_cache

    def get_signing_key(self, kid: str) -> str:
        jwks = self.get_jwks()

        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return self._construct_public_key(key)

        raise HTTPException(
            status_code=401, detail=f"Unable to find key with kid: {kid}"
        )

    def _construct_public_key(self, key_data: Dict[str, Any]) -> str:
        if key_data.get("kty") != "RSA":
            raise HTTPException(status_code=401, detail="Only RSA keys are supported")

        try:
            n = self._base64url_decode(key_data["n"])
            e = self._base64url_decode(key_data["e"])

            n_int = int.from_bytes(n, byteorder="big")
            e_int = int.from_bytes(e, byteorder="big")

            public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key(
                default_backend()
            )

            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            return pem.decode("utf-8")
        except (KeyError, ValueError) as e:
            raise HTTPException(status_code=401, detail=f"Invalid key data: {str(e)}")

    def _base64url_decode(self, data: str) -> bytes:
        missing_padding = len(data) % 4
        if missing_padding:
            data += "=" * (4 - missing_padding)

        return base64.urlsafe_b64decode(data)


class TokenVerifier:
    def __init__(self):
        self.jwks_url = settings.WORKOS_JWKS_URL
        if not self.jwks_url:
            raise ValueError("WORKOS_JWKS_URL not set in environment variables")

        self.jwks_client = JWKSClient(self.jwks_url)
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

    def get_public_key(self, token: str) -> str:
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not kid:
                raise HTTPException(status_code=401, detail="No 'kid' in token header")
            return self.jwks_client.get_signing_key(kid)
        except JWTError as e:
            raise HTTPException(
                status_code=401, detail=f"Invalid token header: {str(e)}"
            )

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            public_key = self.get_public_key(token)
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=None,
                options={"verify_aud": False},
            )

            if not payload:
                raise HTTPException(status_code=401, detail="Invalid token payload")

            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "permissions": payload.get("permissions", []),
                "exp": payload.get("exp"),
                "iat": payload.get("iat"),
            }
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation error: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )


token_verifier = TokenVerifier()


def get_current_user(
    token: str = Depends(token_verifier.oauth2_scheme),
) -> Dict[str, Any]:
    return token_verifier.verify_token(token)
