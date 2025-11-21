from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class GmailTokenPair(BaseModel):
    """
    Represents the OAuth2 access token and refresh token for Gmail API access.
    """
    access_token: str = Field(..., description="The Gmail API access token.")
    refresh_token: str = Field(..., description="The Gmail API refresh token.")
    token_expiration_timestamp: datetime = Field(..., description="The timestamp when the access token expires.")
    encryption_status: bool = Field(False, description="True if the token is encrypted at rest, False otherwise.")
    scope: Optional[str] = Field(None, description="The scope of the granted access token.")
    token_type: Optional[str] = Field(None, description="The type of the token, typically 'Bearer'.")
