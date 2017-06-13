from flask_login import UserMixin
class User(UserMixin):
    def __init__(self,id,name, passwd, username,email,active=True):
        self.name = name
        self.id = id
        self.active = active
        self.passwd=passwd
        self.username=username
        self.email=email

    def is_active(self):
        return self.active

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.username


