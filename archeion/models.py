from globus_sdk import (
    AuthClient,
    TransferClient,
    AccessTokenAuthorizer,
    NativeAppAuthClient,
    TransferData,
    RefreshTokenAuthorizer
)
from conf import CLIENT_ID


class OAuth2(object):
    """Base class for OAuth2 model
    """
    def __init__(self):
        """Initiate an OAuth2() object.

        Initiate OAuth2 flow with Globus credentaials to obtain access tokens. 
        Refresh the tokens automatically so another login is not required.

        Examples
        --------
        Create an OAuth2 object:
            >>> from archeion.models import OAuth2
            >>> authorizer = OAuth2()

        """
        self.client = NativeAppAuthClient(CLIENT_ID)
        self.client.oauth2_start_flow(refresh_tokens=True)

        print(
            "Please go to this URL and login: {0}".format(
                self.client.oauth2_get_authorize_url()
            )
        )

        get_input = getattr(__builtins__, "raw_input", input)
        auth_code = get_input(
            "Please enter the code you get after login here: "
        ).strip()
        token_response = self.client.oauth2_exchange_code_for_tokens(auth_code)

        self.access_token = token_response.by_resource_server["auth.globus.org"][
            "access_token"
        ]
        transfer_response = token_response.by_resource_server["transfer.api.globus.org"]
        self.transfer_token = transfer_response["access_token"]
        self.transfer_refresh_token = transfer_response["refresh_token"]
        self.transfer_expiry_seconds = transfer_response["expires_at_seconds"]

        authorizer = RefreshTokenAuthorizer(
            self.transfer_refresh_token,
            self.client,
            access_token=self.transfer_token,
            expires_at=self.transfer_expiry_seconds,
        )
        self.transfer_client = TransferClient(AccessTokenAuthorizer(TRANSFER_TOKEN))
        self.authorisation_client = AuthClient(authorizer=authorizer)


def search_shared_endpoints(authorizer, query):
    """Search for Globus Shared Endpoints

    Parameters
    ----------
    authorizer : :py:class:`archeion.models.OAuth2`
        OAuth2 instance 
    
    Returns
    -------
    dict
        dict with `display_name` or `canonical_name` 
        of endpoints as keys and `id` as values
    """
    endpoints = authorizer.transfer_client.endpoint_search(query)
    search_results = dict()
    for endpoint in endpoints:
        search_results[
            endpoint["display_name"] or endpoint["canonical_name"]
        ] = endpoint["id"]
    return search_results


class Endpoint(OAuth2):
    """Class for Endpoint Model
    """
    def __init__(self, endpoint_id, oauth=None):
        """Initiate an Endpoint() instance

        Intitiate an Endpoint instance, either from an existing 
        authorizer or through super() proxy

        Parameters
        ----------
        endpoint_id : string
            Globus Endpoint ID
        oauth : :py:class:archeion.models.OAuth2 or None
            Authotizer. If passsed None insted of OAuth2 instance,
            authorizer will be intitated from OAuth2 class.        

        Examples
        --------
        # from existing OAuth2 instance
            >>> from archeion.models import OAuth2, Endpoint
            >>> authorizer = OAuth2()
            >>> endpoint = Endpoint('499930f1-5c43-11e7-bf29-22000b9a448b', authorizer)

        # from scratch
            >>> from archeion.models import Endpoint
            >>> endpoint = Endpoint('499930f1-5c43-11e7-bf29-22000b9a448b')

        """
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
                "https://app.globus.org/file-manager?origin_id=%s" % shared_endpoint_id
            )
            input("Press ENTER after activating the endpoint:")
            r = self.transfer_client.endpoint_autoactivate(
                endpoint_id, if_expires_in=3600
            )

    def __repr__(self):
        endpoint = tc.get_endpoint(host_id)
        return "Shared Endpoint name: {0}".format(
            endpoint["display_name"] or endpoint["canonical_name"]
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

    def mkdir(self, path):
        self.transfer_client.operation_mkdir(self.endpoint_id, path=path)

    def mv(self, oldpath, newpath):
        self.transfer_client.operation_rename(
            self.endpoint_id, oldpath=oldpath, newpath=newpath
        )

    def ls(self, path):
        SharedEndpoint.dir(path)

    def search_endpoints(self, num_results=25):
        endpoints = self.transfer_client.endpoint_search(
            filter_scope="my-endpoints", num_results=num_results
        )
        search_results = dict()
        for endpoint in endpoints:
            search_results[endpoint["display_name"]] = endpoint["id"]
        return search_results


class Transfer:
    def __init__(endpoint1, endpoint2, label, sync_level="checksum"):
        if not isinstance(endpoint1, Endpoint):
            raise AttributeError(
                "Positional argument `endpoint1` expected to be `:py:class:Endpoint`",
                ", recieved `:py:class:{0} instead".format(type(endpoint1)),
            )
        if not isinstance(endpoint2, Endpoint):
            raise AttributeError(
                "Positional argument `endpoint1` expected to be `:py:class:Endpoint`",
                ", recieved `:py:class:{0} instead".format(type(endpoint1)),
            )
        self.endpoint1 = endpoint1
        self.endpoint2 = endpoint2
        self.endpoint1.transfer_client.get_submission_id()
        self.transfer_data = TransferData(
            self.endpoint1.transfer_client,
            self.endpoint1.endpoint_id,
            self.endpoint2.endpoint_id,
            label=label,
            sync_level=sync_level,
        )

    def add(self, endpoint_path, shared_endpoint_path, recursive=True):
        self.transfer_data.add_item(
            endpoint_path, shared_endpoint_path, recursive=recursive
        )
        # TODO logging

    def submit(self):
        status = self.transfer_client.submit_transfer(transfer_data)
        if "has been accepted" in status["message"]:
            pass  # TODO
        else:
            pass  # TODO

    def status(self):
        status = self.transfer_client.task_event_list(transfer_result["task_id"])[
            "code"
        ]
        if status is "STARTED":
            pass  # TODO
        else:
            pass  # TODO
