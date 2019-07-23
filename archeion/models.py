from globus_sdk import (
    AuthClient,
    TransferClient,
    AccessTokenAuthorizer,
    NativeAppAuthClient,
    TransferData,
)
from conf import CLIENT_ID

class OAuth2(object):
    def __init__(self):
        """Initiate an OAuth2 flow
        """
        self.client = NativeAppAuthClient(CLIENT_ID)
        self.client.oauth2_start_flow(refresh_tokens=True)

        print(
            "Please go to this URL and login: {0}".format(
                self.client.oauth2_get_authorize_url()
            )
        )

        get_input = getattr(
            __builtins__, "raw_input", input
        )
        auth_code = get_input(
            "Please enter the code you get after login here: "
        ).strip()
        token_response = self.client.oauth2_exchange_code_for_tokens(
            auth_code
        )

        self.access_token = token_response.by_resource_server[
            "auth.globus.org"
        ][
            "access_token"
        ]
        transfer_response = token_response.by_resource_server[
            "transfer.api.globus.org"
        ]
        self.transfer_token = transfer_response[
            "access_token"
        ]
        self.transfer_refresh_token = transfer_response[
            "refresh_token"
        ]
        self.transfer_expiry_seconds = transfer_response[
            "expires_at_seconds"
        ]

        authorizer = RefreshTokenAuthorizer(
            self.transfer_refresh_token,
            self.client,
            access_token=self.transfer_token,
            expires_at=self.transfer_expiry_seconds,
        )
        self.transfer_client = TransferClient(
            AccessTokenAuthorizer(TRANSFER_TOKEN)
        )
        self.authorisation_client = AuthClient(
            authorizer=authorizer
        )
