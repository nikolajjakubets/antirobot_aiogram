import datetime

from aiogram import types
from aiogram.utils.exceptions import CantRestrictSelf

from data.permissions import new_user_added, user_allowed
from filters import IsGroup
from keyboards.inline import generate_confirm_markup, confirming_callback
from loader import bot
from loader import dp


@dp.message_handler(IsGroup(), content_types=types.ContentTypes.NEW_CHAT_MEMBERS)
async def new_chat_member(message: types.Message):
    """
    Обрабатываем вход нового пользователя
    """
    # Пропускаем старые запросы
    if message.date < datetime.datetime.now() - datetime.timedelta(minutes=1):
        return

    try:
        # сразу выдаём ему права, неподтверждённого пользователя
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.new_chat_members[0].id,
            permissions=new_user_added,
        )
    except CantRestrictSelf:
        return
    # Каждому пользователю отсылаем кнопку
    for i, new_member in enumerate(message.new_chat_members):
        generated_tuple = generate_confirm_markup(message.new_chat_members[i].id)
        markup = generated_tuple[0]
        subject = generated_tuple[1]
        await message.reply(
            (
                f"{new_member.get_mention(as_html=True)}, добро пожаловать в чат!\n"
                f"Подтверди, что ты не бот и нажми на {subject}"
            ),
            reply_markup=markup
        )


@dp.callback_query_handler(confirming_callback.filter())
async def user_confirm(query: types.CallbackQuery, callback_data: dict):
    """
    Хэндлер обрабатывающий нажатие на кнопку
    """

    # сразу получаем все необходимые нам переменные, а именно
    # предмет, на который нажал пользователь
    subject = callback_data.get("subject")
    # предмет на который пользователь должен был нажать
    necessary_subject = callback_data.get('necessary_subject')
    # айди пользователя (приходит строкой, поэтому используем int)
    user_id = int(callback_data.get("user_id"))
    # и айди чата, для последнующей выдачи прав
    chat_id = int(query.message.chat.id)

    # если на кнопку нажал не только что вошедший пользователь, говорим, чтобы не лез и игнорируем (выходим из функции).
    if query.from_user.id != user_id:
        return await query.answer("Эта кнопочка не для тебя", show_alert=True)

    # не забываем выдать юзеру необходимые права если он нажал на правильную кнопку
    if subject == necessary_subject:
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=user_allowed,
        )
    else:
        until_date = datetime.datetime.now() + datetime.timedelta(seconds=30)
        await bot.kick_chat_member(chat_id=chat_id, user_id=user_id, until_date=until_date)

    # и убираем часики
    await query.answer()

    # а также удаляем сообщение, чтобы пользователь в RO не мог получить права
    await query.message.delete()