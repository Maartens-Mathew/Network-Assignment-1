import keyring

class KeyStore:
    def __init__(self, app_name: str, password: bytes = None):
        self.app_name = app_name

    def save(self, username: str, public_key: str, private_key: str):
        keyring.set_password(self.app_name, "username",    username)
        keyring.set_password(self.app_name, "public_key",  public_key)
        keyring.set_password(self.app_name, "private_key", private_key)

    def load(self) -> dict:
        username    = keyring.get_password(self.app_name, "username")
        public_key  = keyring.get_password(self.app_name, "public_key")
        private_key = keyring.get_password(self.app_name, "private_key")

        if not all([username, public_key, private_key]):
            raise ValueError("No keystore entry found.")

        return {
            "username":    username,
            "public_key":  public_key,
            "private_key": private_key,
        }

    def set_username(self, new_username: str):
        if not self.exists():
            raise ValueError("No keystore entry found.")
        keyring.set_password(self.app_name, "username", new_username)

    def get_username(self) -> str:
        if not self.exists():
            raise ValueError("No keystore entry found.")
        return keyring.get_password(self.app_name, "username")

    def exists(self) -> bool:
        return keyring.get_password(self.app_name, "username") is not None