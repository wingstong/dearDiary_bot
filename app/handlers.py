from aiogram import F, Router, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, delete

import app.keyboards as kb
import app.database.requests as rq
from app.database.models import *
from app.texts import texts
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.calendarr import create_calendar

router = Router()


class Form(StatesGroup):
    language = State()
    authorization = State()

    task_description = State()
    task_deadline = State()

    book_namebook = State()
    book_author = State()
    book_description = State()

    diary_note = State()

    mood_journal = State()
    mood_note = State()
    mood_description = State()

    event_description = State()
    event_date = State()


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


async def tasks(callback_query: CallbackQuery, state: FSMContext, session: async_session):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')
    all_tasks = await rq.get_user_tasks(session, user_id)
    keyboard = InlineKeyboardBuilder()
    for task in all_tasks:
        status = '✅' if task.isComplete else '❌'
        button_text = f"{task.taskText} - {task.deadLine} - {status}"
        keyboard.row(InlineKeyboardButton(text=button_text, callback_data=f"task_toggle_{task.Id_task}"))

    keyboard.row(
        InlineKeyboardButton(text=texts[lang_code]['add_task'], callback_data='add_task'),
        InlineKeyboardButton(text=texts[lang_code]['clear_all_notes'], callback_data='clear_all_tasks'),
        InlineKeyboardButton(text=texts[lang_code]['back'], callback_data='back')
    )
    await callback_query.message.edit_text(texts[lang_code]['task_list'], reply_markup=keyboard.as_markup(),
                                           parse_mode='HTML')


@router.callback_query(F.data == 'task_list')
async def task_list_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    tg_id = callback_query.from_user.id
    user = await rq.set_user(tg_id)
    if user:
        await state.update_data(user_id=user.Id_user)

    await tasks(callback_query, state, async_session)


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
    await callback_query.message.edit_text(texts[lang_code]['welcome'], reply_markup=sect_keyboard, parse_mode='HTML')


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

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text=texts[lang_code]['back'], callback_data='back_Task'))
    await message.answer(texts[lang_code]['task_added'], reply_markup=keyboard.as_markup())
    await state.clear()


@router.callback_query(F.data == "back_Task")
async def back_task(callback_query: CallbackQuery, state: FSMContext):
    await task_list_handler(callback_query, state)


@router.callback_query(F.data == 'clear_all_tasks')
async def clear_all_tasks(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')

    async with async_session() as session:
        async with session.begin():
            await session.execute(delete(TODO).where(TODO.user_id == user_id))
            await session.commit()

    await callback_query.message.edit_text(texts[lang_code]['all_notes_cleared'], parse_mode='HTML')
    await task_list_handler(callback_query, state)


@router.callback_query(F.data == 'reading_list')
async def reading_list_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')

    async with async_session() as session:
        result = await session.execute(select(ReadingList).where(ReadingList.user_id == user_id))
        books = result.scalars().all()

    keyboard = InlineKeyboardBuilder()
    for book in books:
        status = '✅' if book.isWatched else '❌'
        button_text = f"{book.namebook}: {book.author} - {book.descriptBook} - {status}"
        keyboard.row(InlineKeyboardButton(text=button_text, callback_data=f"book_toggle_{book.Id_book}"))

    keyboard.row(
        InlineKeyboardButton(text=texts[lang_code]['add_book'], callback_data='add_book'),
        InlineKeyboardButton(text=texts[lang_code]['clear_all_notes'], callback_data='clear_all_books'),
        InlineKeyboardButton(text=texts[lang_code]['back'], callback_data='back')
    )

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

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text=texts[lang_code]['back'], callback_data='back_Book'))
    await message.answer(texts[lang_code]['book_added'], reply_markup=keyboard.as_markup(), parse_mode='HTML')


@router.callback_query(F.data == "back_Book")
async def back_task(callback_query: CallbackQuery, state: FSMContext):
    await reading_list_handler(callback_query, state)


@router.callback_query(F.data == 'clear_all_books')
async def clear_all_books(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')

    async with async_session() as session:
        async with session.begin():
            await session.execute(delete(ReadingList).where(ReadingList.user_id == user_id))
            await session.commit()

    await callback_query.message.edit_text(texts[lang_code]['all_notes_cleared'], parse_mode='HTML')
    await reading_list_handler(callback_query, state)


@router.callback_query(F.data == 'diary')
async def diary_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await state.set_state(Form.diary_note)
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text=texts[lang_code]['back'], callback_data='back'))

    await callback_query.message.edit_text(texts[lang_code]['diary'], reply_markup=keyboard.as_markup(),
                                           parse_mode='HTML')


@router.message(StateFilter(Form.diary_note))
async def save_diary_note(message: Message, state: FSMContext):
    note = message.text
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')

    # Добавление текущей даты к заметке
    current_date = datetime.now().strftime("%d.%m.%y")
    note_with_date = f"{current_date}: {note}"

    new_entry = DiaryEntry(
        user_id=user_id,
        Content=note_with_date
    )

    async with async_session() as session:
        async with session.begin():
            session.add(new_entry)
            await session.commit()

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text=texts[lang_code]['back'], callback_data='back'))
    await message.answer(texts[lang_code]['diary_entry_added'], reply_markup=keyboard.as_markup(), parse_mode='HTML')


@router.callback_query(F.data == 'diary_entries')
async def diary_entries_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')

    async with async_session() as db_session:
        result = await db_session.execute(select(DiaryEntry).where(DiaryEntry.user_id == user_id))
        entries = result.scalars().all()

    await state.set_state(Form.diary_note)
    keyboard = InlineKeyboardBuilder()

    for entry in entries:
        keyboard.row(InlineKeyboardButton(text=entry.Content[:32], callback_data=f'diary_entry_{entry.id_entry}'))

    keyboard.row(
        InlineKeyboardButton(text=texts[lang_code]['clear_all_notes'], callback_data='clear_all_entries'),
        InlineKeyboardButton(text=texts[lang_code]['back'], callback_data='back')
    )

    await callback_query.message.edit_text(texts[lang_code]['diary_entries'], reply_markup=keyboard.as_markup(),
                                           parse_mode='HTML')


@router.callback_query(lambda c: c.data.startswith('diary_entry_'))
async def view_diary_entry(callback_query: CallbackQuery, state: FSMContext):
    entry_id = int(callback_query.data.split('_')[2])
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    async with async_session() as session:
        entry = await session.get(DiaryEntry, entry_id)

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text=texts[lang_code]['back'], callback_data='back_Entries'))

    await callback_query.message.edit_text(entry.Content, reply_markup=keyboard.as_markup(), parse_mode='HTML')


@router.callback_query(F.data == 'clear_all_entries')
async def clear_all_books(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')

    async with async_session() as session:
        async with session.begin():
            await session.execute(delete(DiaryEntry).where(DiaryEntry.user_id == user_id))
            await session.commit()

    await callback_query.message.edit_text(texts[lang_code]['all_entries_cleared'], parse_mode='HTML')
    await diary_entries_handler(callback_query, state)


@router.callback_query(F.data == "back_Entries")
async def back_entry(callback_query: CallbackQuery, state: FSMContext):
    await diary_entries_handler(callback_query, state)


emojis = ['🤩', '😊', '🥰', '🙂', '😴', '🫡',
          '🤯', '😭', '🥲', '🤔', '🙄', '😞', ]


@router.callback_query(F.data == 'mood_journal')
async def mood_journal_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')

    async with async_session() as session:
        result = await session.execute(select(MoodJournal).where(MoodJournal.user_id == user_id))
        mood_notes = result.scalars().all()

    keyboard = InlineKeyboardBuilder()
    for mood in mood_notes:
        date_str = datetime.now().strftime("%d.%m.%y")
        mood_index = int(mood.mood) - 1
        emoji = emojis[mood_index]
        keyboard.row(InlineKeyboardButton(text=f"{date_str}: {emoji} - {mood.description}",
                                          callback_data=f"mood_note_{mood.id_mood}"))

    keyboard.row(
        InlineKeyboardButton(text=texts[lang_code]['add_mood'], callback_data='add_mood_note'),
        InlineKeyboardButton(text=texts[lang_code]['clear_all_notes'], callback_data='clear_all_mood_notes'),
        InlineKeyboardButton(text=texts[lang_code]['back'], callback_data='back')
    )
    await callback_query.message.edit_text(texts[lang_code]['mood_journal'], reply_markup=keyboard.as_markup(),
                                           parse_mode='HTML')


@router.callback_query(F.data == 'add_mood_note')
async def add_mood_note_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await state.set_state(Form.mood_note)
    keyboard = InlineKeyboardBuilder()
    for idx, emoji in enumerate(emojis, 1):
        keyboard.add(InlineKeyboardButton(text=emoji, callback_data=f"mood_{idx}"))
    keyboard.adjust(6)

    await callback_query.message.answer(texts[lang_code]['mood_emo'], reply_markup=keyboard.as_markup(),
                                        parse_mode='HTML')


@router.callback_query(lambda c: c.data.startswith('mood_'))
async def mood_selected(callback_query: CallbackQuery, state: FSMContext):
    mood_id = int(callback_query.data.split('_')[1])
    await state.update_data(selected_mood=mood_id)
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await state.set_state(Form.mood_description)
    await callback_query.message.edit_text(texts[lang_code]['mood_description'], parse_mode='HTML')


@router.message(StateFilter(Form.mood_description))
async def save_mood_description(message: Message, state: FSMContext):
    description = message.text
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')
    selected_mood = user_data.get('selected_mood')

    new_mood_note = MoodJournal(
        user_id=user_id,
        mood=selected_mood,
        description=description
    )

    async with async_session() as session:
        async with session.begin():
            session.add(new_mood_note)
            await session.commit()
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text=texts[lang_code]['back'], callback_data='back_Mood'))
    await message.answer(texts[lang_code]['mood_added'], reply_markup=keyboard.as_markup(), parse_mode='HTML')


@router.callback_query(F.data == "back_Mood")
async def back_mood(callback_query: CallbackQuery, state: FSMContext):
    await mood_journal_handler(callback_query, state)


@router.callback_query(F.data == 'clear_all_mood_notes')
async def clear_all_mood_notes(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')
    user_id = user_data.get('user_id')

    async with async_session() as session:
        async with session.begin():
            await session.execute(delete(MoodJournal).where(MoodJournal.user_id == user_id))
            await session.commit()

    await callback_query.message.edit_text(texts[lang_code]['all_notes_cleared'], parse_mode='HTML')
    await mood_journal_handler(callback_query, state)


@router.callback_query(F.data == 'calendar')
async def process_calendar(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data.split(';')
    action = data[0]

    if action == 'calendar':
        if len(data) == 4:  # Ensure there are enough elements
            year, month, day = int(data[1]), int(data[2]), int(data[3])
            selected_date = datetime(year, month, day).date()
            await state.update_data(event_date=selected_date)
            await callback_query.message.answer(
                f"Вы выбрали дату: {selected_date}. {texts[callback_query.from_user.language_code]['event_description']}")
            await state.set_state(Form.event_description)
        else:
            await callback_query.answer("Некорректные данные календаря.")
    elif action in ['calendar_prev', 'calendar_next']:
        if len(data) == 3:  # Ensure there are enough elements
            year, month = int(data[1]), int(data[2])
            if action == 'calendar_prev':
                month -= 1
                if month == 0:
                    month = 12
                    year -= 1
            elif action == 'calendar_next':
                month += 1
                if month == 13:
                    month = 1
                    year += 1
            await callback_query.message.edit_reply_markup(create_calendar(year, month))
        else:
            await callback_query.answer("Некорректные данные навигации по календарю.")


@router.message(StateFilter(Form.event_description))
async def get_event_description(message: Message, state: FSMContext):
    event_description = message.text
    user_data = await state.get_data()
    event_date = user_data.get('event_date')
    user_id = user_data.get('user_id')

    new_event = CalendarEvent(
        event_date=event_date,
        description=event_description,
        user_id=user_id
    )

    async with async_session() as session:
        async with session.begin():
            session.add(new_event)
            await session.commit()

    await message.answer(texts[user_data['language']]['event_added'])
    await state.clear()


@router.message(Command('show_events'))
async def show_events(message: Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = user_data.get('user_id')

    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(CalendarEvent).where(CalendarEvent.user_id == user_id))
            events = result.scalars().all()

    if events:
        events_text = f"{texts[user_data['language']]['calendar_event']}\n"
        for event in events:
            events_text += f"{event.event_date}: {event.description}\n"
        await message.answer(events_text)
    else:
        await message.answer(texts[user_data['language']]['no_events'])


@router.message(Command('add_event'))
async def add_event(message: Message, state: FSMContext):
    await state.set_state(Form.event_date)
    await message.answer(texts[message.from_user.language_code]['calendar_event'], reply_markup=create_calendar())


@router.message(StateFilter(Form.event_date))
async def select_event_date(message: Message, state: FSMContext):
    await message.answer(texts[message.from_user.language_code]['calendar_event'], reply_markup=create_calendar())


@router.message()
async def unknown_command(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang_code = user_data.get('language', 'en')

    await message.answer(texts[lang_code]['unknown_command'], parse_mode='HTML')
