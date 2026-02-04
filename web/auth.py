from flask_login import UserMixin

class Admin(UserMixin):

    def __init__(self, id):
        self.id = id


# simple admin (later can use DB)
ADMINS = {
    "admin": "123456",   # username : password
}
