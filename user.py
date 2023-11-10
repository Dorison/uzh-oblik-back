from dataclasses import dataclass

def hash(password):
    # TODO security
    return password


@dataclass
class User:
    is_authenticated: bool
    is_active: bool
    id: str
    hash: str
    is_admin: bool

    def get_id(self):
        return self.id


class DictUserManager:
    def __init__(self):
        self.users_by_id = {"test": User(False, False, "test", hash("test"), True)}

    def get_by_id(self, id: str):
        return self.users_by_id.get(id)

    def create_user(self, user: User):
        self.users_by_id[user.get_id()] = user

def authenticate(user: User, password)->bool:
    return not user is None and user.hash == hash(password)


user_manager = DictUserManager()
