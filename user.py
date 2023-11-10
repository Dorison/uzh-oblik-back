from dataclasses import dataclass
from db import DbUser
def hash(password):
    # TODO security
    return password
@dataclass
class User:
    is_authenticated: bool
    is_active: bool
    is_anonymous: bool
    id: str
    hash: str

    def get_id(self):
        return self.id

    def __init__(self, db_user: DbUser):
        self.is_authenticated = False
        self.is_active = False
        self.is_anonymous = False
        self.id = db_user.id
        self.hash = db_user.hash


class DBUserManager:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, id):
        db_user = self.db.get(DbUser, id)
        return User(db_user)

    def create_user(self, username: str, password: str, is_admin: bool):
        db_user = DbUser(username, hash(password), is_admin)
        self.db.session.add(db_user)
        self.db.session.commit()

"""
class DictUserManager:
    def __init__(self):
        self.users_by_id = {"test": User(False, False, "test", hash("test"), True)}

    def get_by_id(self, id: str):
        return self.users_by_id.get(id)

    def create_user(self, username, password, is_admin):
        self.users_by_id[username] = User(False, False, username, hash(password), is_admin)
"""

def authenticate(user: User, password)->bool:
    return not user is None and user.hash == hash(password)


user_manager = DBUserManager()
