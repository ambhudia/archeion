from globus_sdk import (
    AuthClient,
    TransferClient,
    AccessTokenAuthorizer,
    NativeAppAuthClient,
    TransferData,
    RefreshTokenAuthorizer,
)
from conf import CLIENT_ID
import webbrowser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler("archeion.log")
formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(name)s : %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


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

        logger.info("Opening browser window for Globus Authentication")
        webbrowser.open_new(self.client.oauth2_get_authorize_url())

        get_input = getattr(__builtins__, "raw_input", input)
        auth_code = get_input(
            "Please enter the code you get after login here: "
        ).strip()
        logger.debug("User has input authentication code")
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
        self.transfer_client = TransferClient(
            AccessTokenAuthorizer(self.transfer_token)
        )
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
        oauth : :py:class:models.OAuth2 or None
            Authotizer. If passed None insted of OAuth2 instance,
            authorizer will be intitated from OAuth2 class.        

        Examples
        --------
        From existing OAuth2 instance
            >>> from archeion.models import OAuth2, Endpoint
            >>> authorizer = OAuth2()
            >>> endpoint = Endpoint('499930f1-5c43-11e7-bf29-22000b9a448b', authorizer)

        From scratch
            >>> from archeion.models import Endpoint
            >>> endpoint = Endpoint('499930f1-5c43-11e7-bf29-22000b9a448b')

        """
        if "OAuth2" in str(oauth.__class__):
            self.__dict__ = oauth.__dict__.copy()
        elif oauth is None:
            super().__init__()
        else:
            raise TypeError(
                "Argument `oauth` expected to be :py:class:models.OAuth2 or None."
                "Received {0} instead".format(type(oauth))
            )
        self.endpoint_id = endpoint_id
        self.autoactivate()

    def autoactivate(self, if_expires_in=3600):
        """Autoactivate an Endpoint instance

        Activate an instance if it is not activated or if its activation 
        will expire in `if_expires_in` seconds.

        Some endpoints have limits for activation expiry. `if_expires_in` 
        therefore has to be used carefully. For manual activation, user 
        input 'break' will break the loop. 

        Parameters
        ----------
        if_expires_in : int [default: 3600]
            Number of seconds exndpoint should have left before expiry to 
            warrant autoactivation. 
        
        Examples
        --------
        Autoactivate an endpoint instanceif it expires in 12 minutes
            >>> from archeion.models import Endpoint
            >>> endpoint = Endpoint('499930f1-5c43-11e7-bf29-22000b9a448b')
            >>> endpoint.activate(if_expires_in=7200)

        """
        r = self.transfer_client.endpoint_autoactivate(
            self.endpoint_id, if_expires_in=if_expires_in
        )
        while r["code"] == "AutoActivationFailed":
            logger.info(
                "Endpoint requires manual activation, please open "
                "the following URL in a browser to activate the "
                "endpoint:"
            )
            webbrowser.open_new(
                "https://app.globus.org/file-manager?origin_id=%s" % self.endpoint_id
            )
            resp = input("Press ENTER after activating the endpoint:").strip()
            if resp == "break":
                break
            r = self.transfer_client.endpoint_autoactivate(
                self.endpoint_id, if_expires_in=if_expires_in
            )

    def __repr__(self):
        endpoint = self.transfer_client.get_endpoint(host_id)
        return "Shared Endpoint name: {0}".format(
            endpoint["display_name"] or endpoint["canonical_name"]
        )

    def dir(self, path):
        logging.debug("Checking contents of directory `path`")
        files, folders = [], []
        for fyle in self.transfer_client.operation_ls(self.endpoint_id, path=path):
            if fyle["type"] == "file":
                files.append(fyle["name"])
            else:
                folders.append(fyle["name"])
        return dict(files=files, folders=folders)

    def mkdir(self, path):
        try:
            self.transfer_client.operation_mkdir(self.endpoint_id, path=path)
        except TransferAPIError:  # folder already exists
            pass
        
    def mv(self, oldpath, newpath):
        logging.debug(
            "Moving {0} to {1} on endpoint {2}".format(
                oldpath, newpath, self.endpoint_id
            )
        )
        self.transfer_client.operation_rename(
            self.endpoint_id, oldpath=oldpath, newpath=newpath
        )

    def ls(self, path):
        return self.dir(path)

    def search_endpoints(self, num_results=25):
        endpoints = self.transfer_client.endpoint_search(
            filter_scope="my-endpoints", num_results=num_results
        )
        search_results = dict()
        for endpoint in endpoints:
            search_results[endpoint["display_name"]] = endpoint["id"]
        return search_results


class Transfer:
    def __init__(
        self,
        endpoint1,
        endpoint2,
        label,
        sync_level="checksum",
        verify_checksum=False,
        encrypt_data=False,
    ):
        """
        Parameters
        ----------
        endpoint1 : :py:class:models.Endpoint
            The endpoint to transfer from
        
        endp
        
        sync_level : int or string [default: "checksum"]
            "exists", "size", "mtime", or "checksum"
            For compatibility, this can also be 0, 1, 2, or 3

            The meanings are as follows:

            0, exists
            Determine whether or not to transfer based on file existence. If the
            destination file is absent, do the transfer.

            1, size
            Determine whether or not to transfer based on the size of the file. If
            destination file size does not match the source, do the transfer.

            2, mtime
            Determine whether or not to transfer based on modification times. If source
            has a newer modififed time than the destination, do the transfer.

            3, checksum
            Determine whether or not to transfer based on checksums of file contents. If
            source and destination contents differ, as determined by a checksum of their
            contents, do the transfer.

        verify_checksum :  bool [default: False]
            When true, after transfer verify that the source and destination file
            checksums match. If they don't, re-transfer the entire file and keep
            trying until it succeeds.

            This will create CPU load on both the origin and destination of the transfer,
            and may even be a bottleneck if the network speed is high enough.

        encrypt_data : bool [default: False]
            When true, all files will be TLS-protected during transfer.

        """
        if not "Endpoint" in str(endpoint1.__class__):
            raise AttributeError(
                "Positional argument `endpoint1` expected to be `:py:class:Endpoint`",
                ", recieved `:py:class:{0} instead".format(type(endpoint1)),
            )
        if not "Endpoint" in str(endpoint2.__class__):
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
            encrypt_data=encrypt_data,
        )
        self.add_transfers = []

    def add(self, endpoint1_path, endpoint2_path, recursive=True):
        self.transfer_data.add_item(endpoint1_path, endpoint2_path, recursive=recursive)
        logger.info(
            "Added transfer of {0} on endpoint {1} to {2} on endpoint {3}".format(
                endpoint1_path,
                self.endpoint1.endpoint_id,
                endpoint2_path,
                self.endpoint2.endpoint_id,
            )
        )

    def submit(self):
        self.transfer_submission = self.endpoint1.transfer_client.submit_transfer(
            self.transfer_data
        )
        if "has been accepted" in self.transfer_submission["message"]:
            pass  # TODO
        elif "Duplicate" in self.transfer_submission["message"]:
            pass
        else:
            pass

    def status(self):
        status = self.endpoint1.transfer_client.task_event_list(
            self.transfer_submission["task_id"]
        )[0]
        update = '{0}: {1}'.format(status['code'], status['details'])
        return update
