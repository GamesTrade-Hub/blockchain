from fastecdsa import curve, ecdsa, keys, point
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)


class Signature:
    def __init__(self, signature):
        try:
            if isinstance(signature, str):
                self.signature = Signature.decode(signature)
            elif isinstance(signature, tuple):
                self.signature = signature
            else:
                logger.error(f'Invalid private key type. Type received {type(signature)}')
        except ValueError:
            logger.error(f'Invalid private key type. Type received {type(signature)}')

    def __str__(self):
        return f'{self.signature[0]}A{self.signature[1]}'

    def encode(self):
        return self.__str__()

    @staticmethod
    def decode(signature):
        return tuple([int(s) for s in signature.split('A')])


class PrivateKey:
    def __init__(self, key):
        self.key = None

        try:
            if isinstance(key, str):
                self.key = PrivateKey.decode(key)
            elif isinstance(key, int):
                self.key = key
            else:
                logger.error(f'Invalid private key type. Type received {type(key)}')
        except ValueError:
            logger.error(f'Invalid private key type. Type received {type(key)}')

    @staticmethod
    def decode(key):
        return int(key)

    def encode(self):
        return str(self.key)

    def __str__(self):
        return self.encode()

    @classmethod
    def generate(cls, encoded=False):
        private_key = keys.gen_private_key(curve.secp256k1)
        if encoded:
            cls(private_key).encode()
        return cls(private_key)


class PublicKey:
    def __init__(self, key):
        self.key = None

        try:
            if isinstance(key, str):
                self.key = PublicKey.decode(key)
            elif isinstance(key, point.Point):
                self.key = key
            else:
                logger.error(f'Invalid public key type. Type received {type(key)}')
        except ValueError:
            logger.error(f'Invalid public key type. Type received {type(key)}')

    @staticmethod
    def decode(key):
        pk = str(key).split('A')
        return point.Point(int(pk[0]), int(pk[1]), curve.secp256k1)

    def encode(self):
        return str(self.key.x) + 'A' + str(self.key.y)

    def __str__(self):
        return self.encode()

    @classmethod
    def generate_from_private_key(cls, private_key: PrivateKey, encoded=False):
        public_key = keys.get_public_key(private_key.key, curve.secp256k1)
        if encoded:
            return cls(public_key).encode()
        return cls(public_key)


def sign(content: str, private_key: PrivateKey) -> tuple:
    try:
        signature = ecdsa.sign(content, private_key.key, curve.secp256k1, ecdsa.sha256)
    except BaseException as e:
        logger.warning(f'Unable to sign string {content}: {e}')
        signature = None
    logger.info(f'[sign] signature created {signature} {type(signature)}')
    return signature


def has_valid_signature(signature: tuple, content: str, sender_public_key: PublicKey) -> bool:
    if not bool(signature):
        logger.warning(f'[hasValidSignature] transaction not signed')
        return False
    if not ecdsa.verify(signature, content, sender_public_key.key, curve.secp256k1, ecdsa.sha256):
        logger.warning(f'[hasValidSignature] Invalid signature')
        return False
    return True
