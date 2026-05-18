from features.users.model.user import User


class UserRepository:

    def __init__(self, client):
        super().__init__()


    async def get_users(self) -> list[User]:
        pass