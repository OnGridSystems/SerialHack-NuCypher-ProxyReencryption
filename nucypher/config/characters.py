import os

from constant_sorrow import constants
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurve
from cryptography.x509 import Certificate

from nucypher.blockchain.eth.agents import EthereumContractAgent
from nucypher.config.constants import DEFAULT_CONFIG_FILE_LOCATION
from nucypher.config.node import NodeConfiguration
from nucypher.crypto.powers import CryptoPower


class UrsulaConfiguration(NodeConfiguration):

    DEFAULT_REST_HOST = 'localhost'
    DEFAULT_REST_PORT = 9151
    __DB_TEMPLATE = "ursula.{port}.db"
    DEFAULT_DB_NAME = __DB_TEMPLATE.format(port=DEFAULT_REST_PORT)

    __DEFAULT_TLS_CURVE = ec.SECP384R1

    def __init__(self,
                 rest_host: str = None,
                 rest_port: int = None,

                 # TLS
                 tls_curve: EllipticCurve = None,
                 tls_private_key: bytes = None,
                 certificate: Certificate = None,

                 # Ursula
                 db_name: str = None,
                 db_filepath: str = None,
                 interface_signature=None,
                 crypto_power: CryptoPower = None,

                 # Blockchain
                 miner_agent: EthereumContractAgent = None,
                 checksum_address: str = None,

                 *args, **kwargs
                 ) -> None:

        # REST
        self.rest_host = rest_host or self.DEFAULT_REST_HOST
        self.rest_port = rest_port or self. DEFAULT_REST_PORT
        self.db_name = db_name or self.__DB_TEMPLATE.format(port=self.rest_port)
        self.db_filepath = db_filepath or constants.UNINITIALIZED_CONFIGURATION

        #
        # TLS
        #
        self.tls_curve = tls_curve or self.__DEFAULT_TLS_CURVE
        self.tls_private_key = tls_private_key
        self.certificate = certificate

        # Ursula
        self.interface_signature = interface_signature
        self.crypto_power = crypto_power

        #
        # Blockchain
        #
        self.miner_agent = miner_agent
        self.checksum_address = checksum_address

        super().__init__(*args, **kwargs)

    @classmethod
    def from_configuration_file(cls, filepath=None, **overrides) -> 'UrsulaConfiguration':
        from nucypher.config.parsers import parse_ursula_config
        filepath = filepath if filepath is None else DEFAULT_CONFIG_FILE_LOCATION
        payload = parse_ursula_config(filepath=filepath)
        instance = cls(**{**payload, **overrides})
        return instance

    def generate_runtime_filepaths(self, config_root: str) -> dict:
        base_filepaths = NodeConfiguration.generate_runtime_filepaths(config_root=config_root)
        filepaths = dict(db_filepath=os.path.join(config_root, self.db_name),
                         )
        base_filepaths.update(filepaths)
        return base_filepaths

    @property
    def payload(self) -> dict:

        ursula_payload = dict(

                 # REST
                 rest_host=self.rest_host,
                 rest_port=self.rest_port,
                 db_name=self.db_name,
                 db_filepath=self.db_filepath,

                 # TLS
                 tls_curve=self.tls_curve,
                 tls_private_key=self.tls_private_key,
                 certificate=self.certificate,
                 # certificate_filepath=self.certificate_filepath,  # TODO: Handle existing certificates, injecting the path

                 # Ursula
                 interface_signature=self.interface_signature,
                 crypto_power=self.crypto_power,

                 # Blockchain
                 miner_agent=self.miner_agent,
                 checksum_address=self.checksum_address,
                 registry_filepath=self.registry_filepath
        )

        base_payload = super().payload
        ursula_payload.update(base_payload)
        return ursula_payload

    def produce(self, **overrides):
        merged_parameters = {**self.payload, **overrides}
        from nucypher.characters.lawful import Ursula
        ursula = Ursula(**merged_parameters)

        # if self.save_metadata:                     # TODO: Does this belong here..?
        ursula.write_node_metadata(node=ursula)
        ursula.save_certificate_to_disk(directory=ursula.known_certificates_dir)  # TODO: Move this..?

        if self.temp:
            class MockDatastoreThreadPool(object):  # TODO: Does this belong here..?
                def callInThread(self, f, *args, **kwargs):
                    return f(*args, **kwargs)
            ursula.datastore_threadpool = MockDatastoreThreadPool()

        return ursula


class AliceConfiguration(NodeConfiguration):
    from nucypher.characters.lawful import Alice
    from nucypher.config.parsers import parse_alice_config

    _Character = Alice
    _parser = parse_alice_config

    def __init__(self, policy_agent: EthereumContractAgent = None, *args, **kwargs) -> None:
        self.policy_agent = policy_agent
        super().__init__(*args, **kwargs)

    @property
    def payload(self) -> dict:
        alice_payload = dict(policy_agent=self.policy_agent)
        base_payload = super().payload
        alice_payload.update(base_payload)
        return base_payload


class BobConfiguration(NodeConfiguration):
    from nucypher.characters.lawful import Bob

    _Character = Bob
