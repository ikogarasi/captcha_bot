import asyncio
from asyncio.windows_events import NULL

from aiogram import (
    Bot, Dispatcher, executor, types
)
from multicolorcaptcha import CaptchaGenerator
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from io import BytesIO
from random import randint
from config import TOKEN, CaptchaForm
from aiogram.dispatcher import FSMContext
import json

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
generator = CaptchaGenerator(4)
bot_id = TOKEN.split(":")[0]
phrases = []
message_ids = []

#file = open('uk-language.json', encoding='utf8')
#data = json.load(file)
#for i in data:    phrases.append(i)

print('bot is running')

@dp.message_handler(state=CaptchaForm.captcha_answer)
@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def captcha_new_user(message: types.Message, state: FSMContext): 
    global message_ids
    temp = NULL
    message_ids.append(message['message_id'])
    if (message.content_type == types.ContentType.NEW_CHAT_MEMBERS and not message['new_chat_member']['id'] == int(bot_id)):
        new_user_id = message['new_chat_member']['id']
        new_user_name = message['new_chat_member']['username']
        byte_io = BytesIO()
        captcha = generator.gen_captcha_image(difficult_level=1)
        byte_io.name = 'image.png'
        captcha['image'].save(byte_io, 'PNG')
        byte_io.seek(0)
        temp = (await message.reply_photo(photo=byte_io, caption=f"@{new_user_name}"))['message_id']
        message_ids.append(temp)
        CaptchaForm.correct_answer = captcha['characters']
        CaptchaForm.user_id = new_user_id
        await CaptchaForm.captcha_answer.set(user=new_user_id)
        await asyncio.sleep(30)
        try:
            data = await state.get_data()
            if (data['captcha_answered'] != 'true'):
               raise KeyError
            await state.finish()
        except KeyError:
            temp = (await message.answer('Time is up'))['message_id']
            message_ids.append(temp)
            await state.finish()
            await kick_user(message['chat']['id'], new_user_id)
            await clear_chat(chat_id=message['chat']['id'])
    elif (message['from']['id'] == CaptchaForm.user_id):
        if (message.text == CaptchaForm.correct_answer):
            temp = (await message.reply('correct'))['message_id']
            message_ids.append(temp)
        else:
            temp = (await message.reply('incorrect'))['message_id']
            message_ids.append(temp)
            user_id = CaptchaForm.user_id
            await kick_user(message['chat']['id'], user_id=user_id)
        #await state.finish()
        await state.update_data(captcha_answered = 'true')
        await clear_chat(chat_id=message['chat']['id'])

async def kick_user(chat_id, user_id=None):
    bot_status = (await bot.get_chat_member(chat_id=chat_id, user_id=int(bot_id)))['status']
    user_param = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    username = user_param['user']['username']
    if (bot_status == 'administrator'):
        if (user_param['status'] == 'administrator' or user_param['status'] == 'creator'):
           temp = (await bot.send_message(chat_id=chat_id, text=f'@{username} is admin'))['message_id']
           message_ids.append(temp)
        else:
            temp = (await bot.send_message(chat_id=chat_id, text=f"@{username} kicked"))['message_id']
            message_ids.append(temp)
            await bot.kick_chat_member(chat_id=chat_id, user_id=user_id)
            #temp = (await bot.kick_chat_member(chat_id=chat_id, user_id=user_id))['message_id']
            #message_ids.append(temp)
    else:
        await bot.send_message(chat_id=chat_id, text='bot hasn\'t admin rights')

async def delete_msg(chat_id):
    for id in message_ids:
        await bot.delete_message(chat_id=chat_id, message_id=id)
    message_ids.clear()

async def clear_chat(chat_id):
    await asyncio.sleep(10)
    await delete_msg(chat_id)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
