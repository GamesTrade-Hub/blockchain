from fastecdsa import curve, ecdsa, keys, point


class PrivateKey:
    def __init__(self, key):
        if isinstance(key, str):
            self.key = PrivateKey.decode(key)
        elif isinstance(key, int):
            self.key = key
        else:
            print('Error: Invalid public key type. Type received', type(key))

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
        return cls(private_key).key


class PublicKey:
    def __init__(self, key):
        if isinstance(key, str):
            self.key = PublicKey.decode(key)
        elif isinstance(key, point.Point):
            self.key = key
        else:
            print('Error: Invalid public key type. Type received', type(key))

    @staticmethod
    def decode(key):
        pk = str(key).split('A')
        return point.Point(int(pk[0]), int(pk[1]), curve.secp256k1)

    def encode(self):
        return str(self.key.x) + 'A' + str(self.key.y)

    def __str__(self):
        return self.encode()

    @classmethod
    def generate_from_private_key(cls, private_key, encoded=False):
        private_key = PrivateKey(private_key).key
        public_key = keys.get_public_key(private_key, curve.secp256k1)
        if encoded:
            return cls(public_key).encode()
        return cls(public_key).key
