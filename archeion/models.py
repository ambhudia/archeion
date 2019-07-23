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


class Utilities(OAuth2):
    def search_shared_endpoints(self, query):
        endpoints = self.transfer_client.endpoint_search(
            query
        )
        search_results = dict()
        for endpoint in endpoints:
            search_results[
                endpoint["display_name"]
                or endpoint["canonical_name"]
            ] = endpoint["id"]
        return search_results
        

class Endpoint(OAuth2):
    def __init__(self, endpoint_id, oauth=None):
        if type(oauth) is OAuth2:
            self.__dict__ = oauth.__dict__.copy()
        elif oauth is None:
            super().__init__()
        else:
            pass  # TODO exit condition
        self.endpoint_id = endpoint_id
        r = self.transfer_client.endpoint_autoactivate(
            self.endpoint_id, if_expires_in=3600
        )
        while r["code"] == "AutoActivationFailed":
            print(
                "Endpoint requires manual activation, please open "
                "the following URL in a browser to activate the "
                "endpoint:"
            )
            print(
                "https://app.globus.org/file-manager?origin_id=%s"
                % shared_endpoint_id
            )
            input(
                "Press ENTER after activating the endpoint:"
            )
            r = self.transfer_client.endpoint_autoactivate(
                endpoint_id, if_expires_in=3600
            )

    def __repr__(self):
        endpoint = tc.get_endpoint(host_id)
        return "Shared Endpoint name: {0}".format(
            endpoint["display_name"]
            or endpoint["canonical_name"]
        )

    def dir(self, path):
        files, folders = [], []
        for fyle in self.transfer_client.operation_ls(
            self.shared_endpoint_id, path=path
        ):
            if fyle["type"] == "file":
                files.append(fyle["name"])
            else:
                folders.append(fyle["name"])
        return dict(files=files, folders=folders)

    def ls(self, path):
        SharedEndpoint.dir(path)

    def search_endpoints(self, num_results=25):
        endpoints = self.transfer_client.endpoint_search(
            filter_scope="my-endpoints",
            num_results=num_results,
        )
        search_results = dict()
        for endpoint in endpoints:
            search_results[
                endpoint["display_name"]
            ] = endpoint["id"]
        return search_results
