from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database import get_user, check_user_exists, add_user, get_tasks, add_task, toggle_task, get_task_status, get_diary_entries
from app.keyboards import *
from app.texts import texts

router = Router()

class Form(StatesGroup):
    language = State()
    authorization = State()
    registration = State()
    task_description = State()
    task_deadline = State()
    task_list = State()

@router.message(CommandStart())
async def c_start(message: Message, state: FSMContext):
    await state.set_state(Form.language)
    await message.reply(texts['en']['choose_language'], reply_markup=language_selection, parse_mode='HTML')

@router.callback_query(F.data.startswith('lang_'))
async def set_language(callback_query: CallbackQuery, state: FSMContext):
    lang_code = callback_query.data.split('_')[1]
    await state.update_data(language=lang_code)

    await state.set_state(Form.authorization)
    await callback_query.message.answer(texts[lang_code]['authorize'], parse_mode='HTML')

@router.message(Form.authorization)
async def authorize_user(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    login_details = message.text.split()
    if len(login_details) != 2:
        await message.answer(texts[lang_code]['authorize_error'], parse_mode='HTML')
        return

    username, password = login_details
    user = get_user(username, password)

    if user:
        await state.update_data(user_id=user[0])
        reply_keyboard = sections_reply_en if lang_code == 'en' else sections_reply_ru
        await message.answer(texts[lang_code]['authorization_success'], reply_markup=reply_keyboard, parse_mode='HTML')
        await state.clear()
    else:
        await message.answer(texts[lang_code]['authorization_failed'], parse_mode='HTML')

@router.message(Command('signup'))
async def start_signup(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await state.set_state(Form.registration)
    await message.answer(texts[lang_code]['signup'], parse_mode='HTML')

@router.message(Form.registration)
async def register_user(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    registration_details = message.text.split()
    if len(registration_details) != 3:
        await message.answer(texts[lang_code]['signup_error'], parse_mode='HTML')
        return

    username, password, email = registration_details
    user = check_user_exists(username)

    if user:
        await message.answer(texts[lang_code]['user_exists'], parse_mode='HTML')
    else:
        add_user(username, password, email)
        reply_keyboard = sections_reply_en if lang_code == 'en' else sections_reply_ru
        await message.answer(texts[lang_code]['registration_success'], reply_markup=reply_keyboard, parse_mode='HTML')
        await state.clear()

@router.message(F.text.in_(['Task List', 'Список задач']))
@router.callback_query(F.data == 'task_list')
async def task_list_handler(message_or_callback: Message | CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')

    tasks = get_tasks(user_id)

    keyboard = InlineKeyboardMarkup(row_width=1, inline_keyboard=[])
    for task in tasks:
        status = '✅' if task[3] else '❌'
        button = InlineKeyboardButton(text=f"{task[1]} - {task[2]} {status}", callback_data=f"task_{task[0]}")
        keyboard.inline_keyboard.append([button])

    button_add_text = 'Add Task' if lang_code == 'en' else 'Добавить задачу'
    button_add = InlineKeyboardButton(text=button_add_text, callback_data='add_task')
    keyboard.inline_keyboard.append([button_add])

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(texts[lang_code]['task_list'], reply_markup=keyboard, parse_mode='HTML')
    else:
        await message_or_callback.message.answer(texts[lang_code]['task_list'], reply_markup=keyboard, parse_mode='HTML')

@router.callback_query(F.data == 'add_task')
async def add_task(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await state.set_state(Form.task_description)
    await callback_query.message.answer(texts[lang_code]['task_description'], parse_mode='HTML')

@router.message(Form.task_description)
async def get_task_description(message: Message, state: FSMContext):
    task_description = message.text
    await state.update_data(task_description=task_description)

    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await state.set_state(Form.task_deadline)
    await message.answer(texts[lang_code]['task_deadline'], parse_mode='HTML')

@router.message(Form.task_deadline)
async def get_task_deadline(message: Message, state: FSMContext):
    task_deadline = message.text
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')
    task_description = user_data.get('task_description')

    add_task(task_description, task_deadline, user_id)

    await message.answer(texts[lang_code]['task_added'], parse_mode='HTML')
    await state.clear()

@router.callback_query(F.data.startswith('task_'))
async def toggle_task_completion(callback_query: CallbackQuery, state: FSMContext):
    task_id = int(callback_query.data.split('_')[1])
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    is_complete = get_task_status(task_id)
    new_status = not is_complete

    toggle_task(task_id, new_status)

    await callback_query.answer(texts[lang_code]['task_status_updated'], show_alert=True)
    await task_list_handler(callback_query, state)

@router.message(F.text.in_(['Diary', 'Дневник']))
@router.callback_query(F.data == 'diary')
async def diary_handler(message_or_callback: Message | CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(texts[lang_code]['diary'], parse_mode='HTML')
    else:
        await message_or_callback.message.answer(texts[lang_code]['diary'], parse_mode='HTML')

@router.message(F.text.in_(['Diary Entries', 'Записи дневника']))
@router.callback_query(F.data == 'diary_entries')
async def diary_entries_handler(message_or_callback: Message | CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    entries = get_diary_entries()

    keyboard = InlineKeyboardMarkup(row_width=1, inline_keyboard=[])
    for entry in entries:
        button = InlineKeyboardButton(text=f"{entry[1]}: {entry[2][:20]}...", callback_data=f"entry_{entry[0]}")
        keyboard.inline_keyboard.append([button])

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(texts[lang_code]['diary_entries'], reply_markup=keyboard, parse_mode='HTML')
    else:
        await message_or_callback.message.answer(texts[lang_code]['diary_entries'], reply_markup=keyboard, parse_mode='HTML')

@router.message(F.text.in_(['Reading List', 'Список чтения']))
@router.callback_query(F.data == 'reading_list')
async def reading_list_handler(message_or_callback: Message | CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(texts[lang_code]['reading_list'], parse_mode='HTML')
    else:
        await message_or_callback.message.answer(texts[lang_code]['reading_list'], parse_mode='HTML')

@router.message(F.text.in_(['Calendar', 'Календарь']))
@router.callback_query(F.data == 'calendar')
async def calendar_handler(message_or_callback: Message | CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(texts[lang_code]['calendar'], parse_mode='HTML')
    else:
        await message_or_callback.message.answer(texts[lang_code]['calendar'], parse_mode='HTML')

@router.message(F.text.in_(['Mood Journal', 'Журнал настроения']))
@router.callback_query(F.data == 'mood_journal')
async def mood_journal_handler(message_or_callback: Message | CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(texts[lang_code]['mood_journal'], parse_mode='HTML')
    else:
        await message_or_callback.message.answer(texts[lang_code]['mood_journal'], parse_mode='HTML')
