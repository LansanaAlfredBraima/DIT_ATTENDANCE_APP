from abc import ABC, abstractmethod

class User(ABC):
    def __init__(self, user_id: int, username: str, role: str, full_name: str):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.full_name = full_name

    @abstractmethod
    def login(self):
        pass
