from google.oauth2 import service_account
from google.oauth2.service_account import Credentials


def get_service_account_creds(json_key: str, scopes: list[str]) -> Credentials:
    return service_account.Credentials.from_service_account_file(
        json_key, scopes=scopes
    )
