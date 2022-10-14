from typing import Union, Tuple

import logging

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed448
from cryptography.hazmat.primitives.asymmetric.ed448 import (
    Ed448PrivateKey,
    Ed448PublicKey,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)

KEY_SIZE = 114
SIGN_SIZE = 228


def hex_to_bytes(hex_enc):
    return bytes(bytearray.fromhex(hex_enc))


class PublicKeyContainer:
    def __init__(self, key: str):
        """
        This class allow to manage public keys with tokens that contains the key and a token encrypted with the
        gth private key to ensure that the token belongs to public key owner
        :param key:
        :param token:
        :param gth_private_key:
        """
        logger.debug(f"Creating public key container with key {key}")

        self.key, self.signature, self.data = self.decode(key)

        logger.debug(f"key details {self.key}, {self.signature}, {self.data}")

        assert (
                len(self.signature.encode()) == SIGN_SIZE
                and len(self.key.encode()) == KEY_SIZE
        )

    def encode(self):
        return self.key.encode() + self.signature.encode() + self.data

    def __str__(self) -> str:
        return self.encode()

    @classmethod
    def from_gth_private_key_token(
            cls, private_key: "PrivateKey", data: str, gth_private_key: "PrivateKey"
    ):
        """
        This method creates a PublicKeyToken from a public key and a token signed with the gth private key
        :param private_key:
        :param data:
        :param gth_private_key:
        :return:
        """
        public_key = PublicKey.from_private_key(private_key)
        signature = gth_private_key.sign(public_key.encode() + data)
        return cls(public_key.encode() + signature.encode() + data)

    @staticmethod
    def decode(key: str) -> Tuple["PublicKey", "Signature", str]:
        return (
            PublicKey(key[:KEY_SIZE]),
            Signature(key[KEY_SIZE: KEY_SIZE + SIGN_SIZE]),
            key[KEY_SIZE + SIGN_SIZE:],
        )

    def verify(self, signature: "Signature", data: str) -> bool:
        return self.key.verify(signature, data)

    def key_is_valid(self) -> bool:
        if self.is_casual():
            return self.key.verify(self.signature, self.key.encode() + self.data)
        return GTH_PUBLIC_KEY.verify(
            self.signature, self.key.encode() + self.data
        )

    @classmethod
    def casual_from_private_key(cls, private_key):
        public_key = PublicKey.from_private_key(private_key)
        data = "casual"
        signature = private_key.sign(public_key.encode() + data)
        return cls(public_key.encode() + signature.encode() + data)

    def is_casual(self) -> bool:
        return self.data == "casual"


class PrivateKey:
    def __init__(self, key: str):
        """
        Class to represent a private key and make it serializable.
        :param key: The private key hex encoded
        """
        self.key: Ed448PrivateKey

        try:
            if isinstance(key, str):
                self.key = PrivateKey.decode(key)
            else:
                logger.error(f"Invalid private key type. Type received {type(key)}")
        except ValueError as e:
            logger.error(f"Invalid public key type. {e}")

    @staticmethod
    def decode(key: str) -> Ed448PrivateKey:
        return Ed448PrivateKey.from_private_bytes(hex_to_bytes(key))

    def encode(self) -> str:
        return self.key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        ).hex()

    def __str__(self) -> str:
        return self.encode()

    @classmethod
    def generate(cls) -> "PrivateKey":
        private_key = ed448.Ed448PrivateKey.generate()
        private_key_encoded = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        ).hex()
        return cls(private_key_encoded)

    def sign(self, data: str) -> "Signature":
        logger.debug(f"Signing data {data}")
        logger.debug(f"Signing data {bytes(data, 'utf-8')}")
        return Signature(self.key.sign(bytes(data, "utf-8")).hex())


class PublicKey:
    def __init__(self, key: str):
        """
        Class to represent a public key and make it serializable.
        :param key: The public key hex encoded.
        """
        self.key: Ed448PublicKey

        try:
            if isinstance(key, str):
                self.key = PublicKey.decode(key)
            else:
                logger.error(f"Invalid public key type. Type received {type(key)}")
        except ValueError as e:
            logger.error(f"Invalid public key type. {e}")

    @staticmethod
    def decode(key: str) -> Ed448PublicKey:
        return Ed448PublicKey.from_public_bytes(hex_to_bytes(key))

    def encode(self) -> str:
        return self.key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ).hex()

    def __str__(self) -> str:
        return self.encode()

    @classmethod
    def from_private_key(cls, private_key: PrivateKey):
        public_key_encoded = (
            private_key.key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            .hex()
        )
        return cls(public_key_encoded)

    def verify(self, signature: "Signature", data: str) -> bool:
        try:
            self.key.verify(signature.signature, bytes(data, "utf-8"))
            return True
        except InvalidSignature:
            return False


class Signature:
    def __init__(self, signature: str):
        """
        Class to represent a signature and make it serializable.
        :param signature: hexadecimal encoded signature.
        """
        self.signature: bytes

        try:
            self.signature = Signature.decode(signature)
        except ValueError as e:
            logger.error(f"Invalid public key type. {e.__traceback__}")

    def __str__(self) -> str:
        return self.encode()

    def encode(self) -> str:
        return self.signature.hex()

    @staticmethod
    def decode(signature: str) -> bytes:
        """
        Decode a signature string to a tuple.
        :param signature: string signature to decode.
        :return: decoded signature.
        """
        return hex_to_bytes(signature)

    def is_valid(self, data: str, public_key: PublicKey) -> bool:
        """
        Check if a signature is valid.
        :param signature: signature to check.
        :param data: data to check.
        :param public_key: public key to check.
        :return: True if the signature is valid, False otherwise.
        """
        try:
            public_key.verify(self, data)
        except InvalidSignature:
            return False
        return True


GTH_PUBLIC_KEY = PublicKeyContainer(
    "798f62356605804e81754ba5ba552c813df77ec193a5c71426655ab34919b9a827604971e16d26f2e8d7d9926f8e8d7d44acd9db9eb2b11f80ed45ec335c9ab09e6c9b7d2b5d294cab7ea6d052d470bda0c03713c0e28311531df330092b94a4aa9ebd0df6cf0425383e6d3c9249c4501c8071e7a3da0a162c684894dec43681e637d26ba11a419fed162af02555ef7f8f750a986bac5a302491dc87b2f515db336573822de39ff2191e00GTH"
)

if __name__ == "__main__":
    # token = "GTH"
    #
    # pvk = PrivateKey.generate()
    # pbk = PublicKey.generate_from_private_key(pvk)
    # print(pvk.encode(), len(pvk.encode()))
    # print(pbk.encode())
    # print(
    #     pvk.sign(bytes(token, "utf-8")),
    #     "\n",
    #     len(pvk.sign(bytes(token, "utf-8")).encode()),
    # )
    # pbk2 = PublicKeyContainer.from_gth_private_key_token(pbk, "GTH", pvk)
    # print(pbk2.encode())

    from credentials import PRIVATE_KEY, PUBLIC_KEY  # Because credentials here are these of GTH

    GTH_private_key = PRIVATE_KEY

    admin_token = "snowy"

    admin_private_key = PrivateKey.generate()
    admin_public_key = PublicKeyContainer.from_gth_private_key_token(
        admin_private_key, admin_token, GTH_private_key
    )

    print("key_is_valid", admin_public_key.key_is_valid())

    # Print snowy information
    print("1", admin_public_key.encode())
    print("1", admin_private_key.encode())
