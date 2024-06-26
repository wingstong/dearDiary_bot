import logging
from aiogram import F, Router, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

import app.keyboards as kb
import app.database.requests as rq
from app.database.models import *
from app.texts import texts
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


class Form(StatesGroup):
    language = State()
    authorization = State()
    registration = State()
    task_description = State()
    task_deadline = State()
    book_namebook = State()
    book_author = State()
    book_description = State()
    task_list = State()


@router.message(CommandStart())
async def c_start(message: Message, state: FSMContext):
    await state.set_state(Form.language)
    await rq.set_user(message.from_user.id)
    tg_id = message.from_user.id
    user = await rq.set_user(tg_id)
    await state.update_data(user_id=user.Id_user)
    await message.answer(texts['en']['choose_language'], reply_markup=kb.language_selection, parse_mode='HTML')


@router.callback_query(lambda c: c.data.startswith('lang_'))
async def set_language(callback_query: CallbackQuery, state: FSMContext):
    lang_code = callback_query.data.split('_')[1]
    await callback_query.answer("")
    await state.update_data(language=lang_code)
    await state.set_state(Form.authorization)
    sect_keyboard = kb.sections_inline_en if lang_code == 'en' else kb.sections_inline_ru
    await callback_query.message.answer(texts[lang_code]['welcome'], reply_markup=sect_keyboard, parse_mode='HTML')


async def get_user_tasks(session: async_session, user_id: int):
    async with session() as db_session:
        result = await db_session.execute(select(TODO).where(TODO.user_id == user_id))
        return result.scalars().all()


async def tasks(state: FSMContext, session: async_session):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')
    all_tasks = await get_user_tasks(session, user_id)
    keyboard = InlineKeyboardBuilder()
    for task in all_tasks:
        status = '✅' if task.isComplete else '❌'
        button_text = f"{task.taskText} - {task.deadLine} - {status}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f"task_toggle_{task.Id_task}"))

    button_add_text = 'Add Task' if lang_code == 'en' else 'Добавить задачу'
    button_back_text = 'Back' if lang_code == 'en' else 'Назад'
    keyboard.add(InlineKeyboardButton(text=button_add_text, callback_data='add_task'))
    keyboard.add(InlineKeyboardButton(text=button_back_text, callback_data='back'))
    return keyboard.adjust(1)


@router.message(F.text.in_(['Task List', 'Список задач']))
@router.message(Command('task_list'))
@router.callback_query(F.data == 'task_list')
async def task_list_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    tg_id = callback_query.from_user.id
    user = await rq.set_user(tg_id)
    if user:
        await state.update_data(user_id=user.Id_user)

    keyboard = await tasks(state, async_session)
    if isinstance(callback_query, Message):
        await callback_query.edit_text(texts[lang_code]['task_list'], reply_markup=keyboard.as_markup(),
                                       parse_mode='HTML')
    else:
        await callback_query.message.edit_text(texts[lang_code]['task_list'], reply_markup=keyboard.as_markup(),
                                               parse_mode='HTML')


@router.callback_query(lambda c: c.data.startswith('task_toggle_'))
async def toggle_task_status(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    task_id = int(callback_query.data.split('_')[2])
    async with async_session() as session:
        async with session.begin():
            task = await session.get(TODO, task_id)
            task.isComplete = not task.isComplete
            await session.commit()
    await callback_query.answer(texts[lang_code]['task_status_updated'])
    await task_list_handler(callback_query, state)



@router.callback_query(F.data == 'back')
async def back_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await state.set_state(Form.task_description)
    sect_keyboard = kb.sections_inline_en if lang_code == 'en' else kb.sections_inline_ru
    await callback_query.message.answer(texts[lang_code]['welcome'], reply_markup=sect_keyboard, parse_mode='HTML')


@router.callback_query(F.data == 'add_task')
async def add_task_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await state.set_state(Form.task_description)
    await callback_query.message.answer(texts[lang_code]['task_description'], parse_mode='HTML')


@router.message(StateFilter(Form.task_description))
async def get_task_description(message: Message, state: FSMContext):
    task_description = message.text
    await state.update_data(task_description=task_description)

    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await state.set_state(Form.task_deadline)
    await message.answer(texts[lang_code]['task_deadline'], parse_mode='HTML')


@router.message(StateFilter(Form.task_deadline))
async def get_task_deadline(message: Message, state: FSMContext):
    task_deadline = message.text
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')
    task_description = user_data.get('task_description')

    new_task = TODO(
        taskText=task_description,
        deadLine=task_deadline,
        isComplete=False,
        user_id=user_id
    )

    async with async_session() as session:
        async with session.begin():
            session.add(new_task)
            await session.commit()

    await message.answer(texts[lang_code]['task_added'], parse_mode='HTML')
    await state.clear()


async def get_user_books(session: async_session, user_id: int):
    async with session() as db_session:
        result = await db_session.execute(select(ReadingList).where(ReadingList.user_id == user_id))
        return result.scalars().all()


async def books(state: FSMContext, session: async_session):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')
    all_books = await get_user_books(session, user_id)
    keyboard = InlineKeyboardBuilder()
    for book in all_books:
        status = '✅' if book.isWatched else '❌'
        button_text = f"{book.namebook} - {book.author} - {book.descriptBook} {status}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f"book_toggle_{book.Id_book}"))

    button_add_text = 'Add Book' if lang_code == 'en' else 'Добавить книгу'
    button_back_text = 'Back' if lang_code == 'en' else 'Назад'
    keyboard.add(InlineKeyboardButton(text=button_add_text, callback_data='add_book'))
    keyboard.add(InlineKeyboardButton(text=button_back_text, callback_data='back'))
    return keyboard.adjust(1)


@router.message(F.text.in_(['Reading List', 'Список чтения']))
@router.callback_query(F.data == "reading_list")
async def reading_list_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    tg_id = callback_query.from_user.id
    user = await rq.set_user(tg_id)
    if user:
        await state.update_data(user_id=user.Id_user)

    keyboard = await books(state, async_session)
    if isinstance(callback_query, Message):
        await callback_query.edit_text(texts[lang_code]['reading_list'], reply_markup=keyboard.as_markup(),
                                       parse_mode='HTML')
    else:
        await callback_query.message.edit_text(texts[lang_code]['reading_list'], reply_markup=keyboard.as_markup(),
                                               parse_mode='HTML')

@router.callback_query(lambda c: c.data.startswith('book_toggle_'))
async def toggle_book_status(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    book_id = int(callback_query.data.split('_')[2])
    async with async_session() as session:
        async with session.begin():
            book = await session.get(ReadingList, book_id)
            book.isWatched = not book.isWatched
            await session.commit()
    await callback_query.answer(texts[lang_code]['book_status_updated'])
    await reading_list_handler(callback_query, state)


@router.callback_query(F.data == 'add_book')
async def add_book_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await state.set_state(Form.book_namebook)
    await callback_query.message.answer(texts[lang_code]['book_name'], parse_mode='HTML')


@router.message(StateFilter(Form.book_namebook))
async def get_book_name(message: Message, state: FSMContext):
    book_namebook = message.text
    await state.update_data(book_namebook=book_namebook)

    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await state.set_state(Form.book_author)
    await message.answer(texts[lang_code]['book_author'], parse_mode='HTML')


@router.message(StateFilter(Form.book_author))
async def get_book_author(message: Message, state: FSMContext):
    book_author = message.text
    await state.update_data(book_author=book_author)

    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await state.set_state(Form.book_description)
    await message.answer(texts[lang_code]['book_desc'], parse_mode='HTML')


@router.message(StateFilter(Form.book_description))
async def get_book_desc(message: Message, state: FSMContext):
    book_desc = message.text
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')
    book_namebook = user_data.get('book_namebook')
    book_author = user_data.get('book_author')

    new_book = ReadingList(
        namebook=book_namebook,
        author=book_author,
        descriptBook=book_desc,
        isWatched=False,
        user_id=user_id
    )

    async with async_session() as session:
        async with session.begin():
            session.add(new_book)
            await session.commit()

    await message.answer(texts[lang_code]['book_added'], parse_mode='HTML')
    await state.clear()


@router.message(F.text.in_(['Diary', 'Дневник']))
@router.message(Command('diary'))
@router.callback_query(F.data == 'diary')
async def diary_handler(message_or_callback: Message | CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(texts[lang_code]['diary'], parse_mode='HTML')
    else:
        await message_or_callback.message.answer(texts[lang_code]['diary'], parse_mode='HTML')


@router.message(F.text.in_(['Diary Entries', 'Записи дневника']))
@router.message(Command('diary_entries'))
@router.callback_query(F.data == 'diary_entries')
async def diary_entries_handler(message_or_callback: Message | CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    entries = 0

    keyboard = InlineKeyboardMarkup(row_width=1, inline_keyboard=[])
    for entry in entries:
        button = InlineKeyboardButton(text=f"{entry[1]}: {entry[2][:20]}...", callback_data=f"entry_{entry[0]}")
        keyboard.inline_keyboard.append([button])

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(texts[lang_code]['diary_entries'], reply_markup=keyboard, parse_mode='HTML')
    else:
        await message_or_callback.message.answer(texts[lang_code]['diary_entries'], reply_markup=keyboard,
                                                 parse_mode='HTML')


@router.message()
async def unknown_command(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await message.answer(texts[lang_code]['unknown_command'], parse_mode='HTML')
