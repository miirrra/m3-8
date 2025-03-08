
import os
from mistralai import Mistral
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import logging
from basa import init_db, save_argument, get_argument
from config import BOT_TOKEN,api_key

logging.basicConfig(level=logging.INFO)

mistral_client = Mistral(api_key=api_key)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

init_db()

class DebateState(StatesGroup):
    topic = State()
    side = State()
    round = State()

def generate_argument(topic, side):
    prompt = f"Напишите аргумент {'за' if side == 'за' else 'против'} по теме: {topic}. напиши не больше 2 абзацев."
    try:
        response = mistral_client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка: {str(e)}"

# Обработчик команды /start
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.reply("Привет! Напишите /debate, чтобы начать дебаты.")

# Обработчик команды /debate
@dp.message(Command("debate"))
async def start_debate(message: Message, state: FSMContext):
    await message.reply("Введите тему дебатов.")
    await state.set_state(DebateState.topic)

@dp.message(DebateState.topic)
async def choose_side(message: Message, state: FSMContext):
    topic = message.text.strip()
    await state.update_data(topic=topic)

    # Кнопки для выбора стороны
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="За", callback_data="side_za"),InlineKeyboardButton(text="Против", callback_data="side_protiv")],

        ]
    )
    await message.reply(f"Выбрана тема: {topic}. Выберите вашу позицию.", reply_markup=inline_kb)

# Обработка выбора стороны и начало раундов
@dp.callback_query(lambda c: c.data in ["side_za", "side_protiv"])
async def start_rounds(callback_query: types.CallbackQuery, state: FSMContext):
    side = "за" if callback_query.data == "side_za" else "против"
    await state.update_data(side=side, round=1)

    bot_side = "против" if side == "за" else "за"

    await callback_query.message.reply(f"Вы выбрали: {side}. Бот будет играть за {bot_side}. Введите ваш первый аргумент!")
    await state.set_state(DebateState.round)


@dp.message(DebateState.round)
async def play_round(message: Message, state: FSMContext):
    data = await state.get_data()
    topic = data['topic']
    side = data['side']
    round_number = data['round']
    bot_side = "против" if side == "за" else "за"

    user_argument = message.text.strip()
    # save_argument(topic, side, user_argument)     #если что откомммент!

    bot_argument = get_argument(topic, bot_side) or generate_argument(topic, bot_side)
    save_argument(topic, bot_side, bot_argument)

    await message.reply(f"Раунд {round_number}:\n\nВаш аргумент ({side}): {user_argument}\n\nАргумент бота ({bot_side}): {bot_argument}")

    if round_number < 3:
        await state.update_data(round=round_number + 1)
        await message.reply("Переход к следующему раунду. Введите ваш следующий аргумент!")
    else:
        await message.reply("Дебаты завершены! Спасибо за участие!")
        await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Работа завершена.")



"""Техническое задание:
Бот- дебатер
Бот принимает сторону «за» или «против» в зависимости от выбора пользователя и играет против пользователя, игра длится в три раунда. 

У бота есть команды:
/start для начало- приветствие 
/debate для запрашивание темы
Инлайн кнопка для выбора на чей стороне играть

Работа с sqlite3 для базы данных “debate.db”, где будут храниться topics, side,arguments.
 Подключение Mistral AI , генерирует аргументы, в случае если в бд уже есть аргументы на определеную тему то аргументы берутся с бд."""
