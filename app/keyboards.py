from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

sections_en = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Task List', callback_data='task_list')],
    [InlineKeyboardButton(text='Diary', callback_data='diary')],
    [InlineKeyboardButton(text='Diary Entries', callback_data='diary_entries')],
    [InlineKeyboardButton(text='Reading List', callback_data='reading_list')],
    [InlineKeyboardButton(text='Calendar', callback_data='calendar')],
    [InlineKeyboardButton(text='Mood Journal', callback_data='mood_journal')]
])

sections_ru = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Список задач', callback_data='task_list')],
    [InlineKeyboardButton(text='Дневник', callback_data='diary')],
    [InlineKeyboardButton(text='Записи', callback_data='diary_entries')],
    [InlineKeyboardButton(text='Список чтения', callback_data='reading_list')],
    [InlineKeyboardButton(text='Календарь', callback_data='calendar')],
    [InlineKeyboardButton(text='Журнал настроения', callback_data='mood_journal')]
])

language_selection = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Eng', callback_data='lang_en')],
    [InlineKeyboardButton(text='Ru', callback_data='lang_ru')]
])

sections_reply_en = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Task List'),
    KeyboardButton(text='Reading List')],
    [KeyboardButton(text='Diary'),
    KeyboardButton(text='Diary Entries')],
    [KeyboardButton(text='Mood Journal'),
    KeyboardButton(text='Calendar')],

], resize_keyboard=True)

sections_reply_ru = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Список задач'),
    KeyboardButton(text='Список чтения')],
    [KeyboardButton(text='Дневник'),
    KeyboardButton(text='Записи дневника')],
    [KeyboardButton(text='Журнал настроения'),
    KeyboardButton(text='Календарь')],

], resize_keyboard=True)