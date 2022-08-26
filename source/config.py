from array import array
from asyncio.windows_events import NULL
from asyncore import dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Dispatcher

TOKEN = ""

class IdState(State):
    async def set(self, user=None):
        state = Dispatcher.get_current().current_state(user=user)
        await state.set_state(self.state)

class CaptchaForm(StatesGroup):
    correct_answer = None
    user_id = None
    captcha_answer = IdState()