from tools import get, post


class ManageKeys:
    def __init__(self):
        self.token = "b1d69ce4-dd33-4dac-9781-afcb909d74cd"  # FIXME: Changer cette var en var d'env
        self.public_key_path = "keys.pub"  # FIXME: Changer le path pour avoir la public key de GTH en variable d'env
        self.base_url = "https://keymanager.gamestradehub.com/"

    def get_all_keys(self):
        resp = get(
            f"{self.base_url}listkeys/",
            headers={"Authorization": f"Token {self.token}"}
        )
        return resp.json()

    def add_key(self, key_to_add_path, entity):
        with open(self.public_key_path, "r") as f:
            pub_key = f.read()
            # pub_key = rsa.PublicKey.load_pkcs1(f.read().replace("\\n", "\n").encode("utf-8"))
        with open(key_to_add_path, "r") as f:
            key_to_add = f.read()
            # encrypted_key = rsa.encrypt(f.read().replace("\\n", "\n").encode("utf-8"), pub_key)
        resp = post(
            f"{self.base_url}addkey/",
            headers={"Authorization": f"Token {self.token}"},
            data={
                "pub_key": pub_key,
                "key": key_to_add,
                "entity": entity
            }
        )
        return resp.content

    def check_key_exist(self, key):
        resp = post(
            f"{self.base_url}checkkey/",
            headers={"Authorization": f"Token {self.token}"},
            data={"key": key}
        )
        return True if resp.json()["status"] == "Ok" else False
