from models.user import User

class Admin(User):
    def login(self):
        print(f"Admin {self.username} logged in")
