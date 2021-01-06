from web3 import Web3

from dydx3.eth_signing import SignWithWeb3
from dydx3.eth_signing import SignWithKey
from dydx3.modules.api_keys import ApiKeys
from dydx3.modules.eth import Eth
from dydx3.modules.private import Private
from dydx3.modules.public import Public
from dydx3.modules.onboarding import Onboarding
from dydx3.starkex.helpers import private_key_to_public_hex


class Client(object):

    def __init__(
        self,
        host,
        api_timeout=3000,  # TODO: Actually use this.
        api_private_key=None,
        stark_private_key=None,
        eth_private_key=None,
        web3=None,
        web3_account=None,
        web3_provider=None,
    ):
        # Remove trailing '/' if present, from host.
        if host.endswith('/'):
            host = host[:-1]

        self.host = host
        self.api_timeout = api_timeout
        self.api_private_key = api_private_key
        self.stark_private_key = stark_private_key

        self.web3 = None
        self.eth_signer = None
        self.default_address = None

        if web3 is not None or web3_provider is not None:
            self.web3 = web3 or Web3(web3_provider)
            self.eth_signer = SignWithWeb3(self.web3)
            self.default_address = self.web3.eth.defaultAccount or None

        if eth_private_key is not None or web3_account is not None:
            # May override web3 or web3_provider configuration.
            key = eth_private_key or web3_account.key
            self.eth_signer = SignWithKey(key)
            self.default_address = self.eth_signer.address

        # Initialize the public module. Other modules are initialized on
        # demand, if the necessary configuration options were provided.
        self._public = Public(host)
        self._private = None
        self._api_keys = None
        self._eth = None
        self._onboarding = None

        # Derive the public keys.
        if stark_private_key is not None:
            self.stark_public_key = private_key_to_public_hex(
                stark_private_key,
            )
        else:
            self.stark_public_key = None
        if api_private_key is not None:
            self.api_public_key = private_key_to_public_hex(
                api_private_key,
            )
        else:
            self.api_public_key = None

    @property
    def public(self):
        '''
        Get the public module, used for interacting with public endpoints.
        '''
        return self._public

    @property
    def private(self):
        '''
        Get the private module, used for interacting with endpoints that
        require API-key auth.
        '''
        if not self._private:
            if self.api_private_key:
                self._private = Private(
                    host=self.host,
                    stark_private_key=self.stark_private_key,
                    api_private_key=self.api_private_key,
                    api_public_key=self.api_public_key,
                    default_address=self.default_address,
                )
            else:
                raise Exception(
                    'Private endpoints not supported' +
                    'since api_private_key was not specified',
                )
        return self._private

    @property
    def api_keys(self):
        '''
        Get the api_keys module, used for managing API keys. Requires
        Ethereum key auth.
        '''
        if not self._api_keys:
            if self.eth_signer:
                self._api_keys = ApiKeys(
                    host=self.host,
                    eth_signer=self.eth_signer,
                    default_address=self.default_address,
                )
            else:
                raise Exception(
                    'API keys module is not supported since no Ethereum ' +
                    'signing method (web3, web3_account, web3_provider) was ' +
                    'provided',
                )
        return self._api_keys

    @property
    def onboarding(self):
        '''
        Get the onboarding module, used to create a new user. Requires
        Ethereum key auth.
        '''
        if not self._onboarding:
            if self.eth_signer:
                self._onboarding = Onboarding(
                    host=self.host,
                    eth_signer=self.eth_signer,
                    default_address=self.default_address,
                    stark_public_key=self.stark_public_key,
                    api_public_key=self.api_public_key,
                )
            else:
                raise Exception(
                    'Onboarding is not supported since no Ethereum ' +
                    'signing method (web3, web3_account, web3_provider) was ' +
                    'provided',
                )
        return self._onboarding

    @property
    def eth(self):
        '''
        Get the eth module, used for interacting with Ethereum smart contracts.
        '''
        if not self._eth:
            if self.web3:
                self._eth = Eth(self.web3)
            else:
                raise Exception(
                    'Eth module is not supported since neither web3 ' +
                    'nor web3_provider was specified',
                )
        return self._eth
