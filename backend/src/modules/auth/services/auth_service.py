from src.common.config import settings
from src.common.utils.exceptions import AuthenticationError, InvalidCredentialsError
from workos import WorkOSClient

from ..schemas.auth_schemas import AuthenticateResponse


class AuthService:
    def __init__(self):
        self.workos_client = WorkOSClient(
            api_key=settings.WORKOS_API_KEY,
            client_id=settings.WORKOS_CLIENT_ID,
        )

    def get_jwt_token(self) -> AuthenticateResponse:
        try:
            user_details = (
                self.workos_client.user_management.authenticate_with_password(
                    email=settings.WORKOS_TESTUSER_EMAIL,
                    password=settings.WORKOS_TESTUSER_PASSWORD,
                )
            )

            return AuthenticateResponse(
                token=user_details.access_token,
            )
        except Exception as e:
            # Check if it's a credentials-related error
            if "invalid" in str(e).lower() or "credentials" in str(e).lower():
                raise InvalidCredentialsError(
                    f"Invalid credentials provided: {str(e)}",
                    details={"provider": "workos"},
                )
            else:
                raise AuthenticationError(
                    f"Failed to get JWT token: {str(e)}",
                    details={
                        "provider": "workos",
                        "operation": "authenticate_with_password",
                    },
                )
