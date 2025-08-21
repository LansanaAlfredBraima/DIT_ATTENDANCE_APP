from models.user import User

class Lecturer(User):
    def login(self):
        print(f"Lecturer {self.username} logged in")
