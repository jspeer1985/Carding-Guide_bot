from aiogram.filters import BaseFilter
from aiogram.types import Message
from utils.admin_utils import is_admin

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        # Early return if the message doesn't contain a valid user or user ID is missing
        if not message.from_user or not message.from_user.id:
            return False

        user_id = message.from_user.id
        username = message.from_user.username
        
        # Call the is_admin function to check if the user is an admin
        return await is_admin(user_id, username)
