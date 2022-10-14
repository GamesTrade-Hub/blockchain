# from typing import Union
#
# import logging
#
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)
# logger.setLevel(logging.DEBUG)
#
#
# class Signature:
#     def __init__(self, signature: Union[str, tuple]):
#         """
#         Class to represent a signature and make it serializable.
#         :param signature: signature to store.
#         """
#         try:
#             if isinstance(signature, str):
#                 self.signature = Signature.decode(signature)
#             elif isinstance(signature, tuple):
#                 self.signature = signature
#             else:
#                 logger.error(
#                     f"Invalid private key type. Type received {type(signature)}"
#                 )
#         except ValueError:
#             logger.error(f"Invalid private key type. Type received {type(signature)}")
#
#     def __str__(self) -> str:
#         return f"{self.signature[0]}A{self.signature[1]}"
#
#     def encode(self) -> str:
#         return self.__str__()
#
#     @staticmethod
#     def decode(signature: str) -> tuple:
#         """
#         Decode a signature string to a tuple.
#         :param signature: string signature to decode.
#         :return: decoded signature.
#         """
#         return tuple([int(s) for s in signature.split("A")])
#
#
# class PrivateKey:
#     def __init__(self, key: Union[str, int]):
#         """
#         Class to represent a private key and make it serializable.
#         :param key: key to store.
#         """
#         self.key = None
#
#         try:
#             if isinstance(key, str):
#                 self.key = PrivateKey.decode(key)
#             elif isinstance(key, int):
#                 self.key = key
#             else:
#                 logger.error(f"Invalid private key type. Type received {type(key)}")
#         except ValueError:
#             logger.error(f"Invalid private key type. Type received {type(key)}")
#
#     @staticmethod
#     def decode(key: str) -> int:
#         return int(key)
#
#     def encode(self) -> str:
#         return str(self.key)
#
#     def __str__(self) -> str:
#         return self.encode()
#
#     @classmethod
#     def generate(cls, encoded=False) -> "PrivateKey":
#         private_key = keys.gen_private_key(curve.secp256k1)
#         if encoded:
#             cls(private_key).encode()
#         return cls(private_key)
#
#
# class PublicKey:
#     def __init__(self, key: Union[str, point.Point]):
#         """
#         Class to represent a public key and make it serializable.
#         :param key: key to store.
#         """
#         self.key = None
#
#         try:
#             if isinstance(key, str):
#                 self.key = PublicKey.decode(key)
#             elif isinstance(key, point.Point):
#                 self.key = key
#             else:
#                 logger.error(f"Invalid public key type. Type received {type(key)}")
#         except ValueError:
#             logger.error(f"Invalid public key type. Type received {type(key)}")
#
#     @staticmethod
#     def decode(key: str) -> point.Point:
#         pk = str(key).split("A")
#         return point.Point(int(pk[0]), int(pk[1]), curve.secp256k1)
#
#     def encode(self) -> str:
#         return str(self.key.x) + "A" + str(self.key.y)
#
#     def __str__(self) -> str:
#         return self.encode()
#
#     @classmethod
#     def generate_from_private_key(cls, private_key: PrivateKey, encoded: bool = False) -> Union["PublicKey", str]:
#         public_key = keys.get_public_key(private_key.key, curve.secp256k1)
#         if encoded:
#             return cls(public_key).encode()
#         return cls(public_key)
#
#
# def sign(content: str, private_key: PrivateKey) -> tuple:
#     try:
#         signature = ecdsa.sign(content, private_key.key, curve.secp256k1, ecdsa.sha256)
#     except BaseException as e:
#         logger.warning(f"Unable to sign string {content}: {e}")
#         signature = None
#     logger.info(f"[sign] signature created {signature} {type(signature)}")
#     return signature
#
#
# def has_valid_signature(
#     signature: tuple, content: str, sender_public_key: PublicKey
# ) -> bool:
#     if not bool(signature):
#         logger.warning(f"[hasValidSignature] transaction not signed")
#         return False
#     if not ecdsa.verify(
#         signature, content, sender_public_key.key, curve.secp256k1, ecdsa.sha256
#     ):
#         logger.warning(f"[hasValidSignature] Invalid signature")
#         return False
#     return True
