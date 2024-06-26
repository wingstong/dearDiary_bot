from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


sections_inline_en = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Diary', callback_data='diary'), InlineKeyboardButton(text='Diary Entries', callback_data='diary_entries')],
    [InlineKeyboardButton(text='Task List', callback_data='task_list'), InlineKeyboardButton(text='Reading List', callback_data='reading_list')],
    [InlineKeyboardButton(text='Mood Journal', callback_data='mood_journal'), InlineKeyboardButton(text='Calendar', callback_data='calendar')],
])

sections_inline_ru = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Дневник', callback_data='diary'), InlineKeyboardButton(text='Записи', callback_data='diary_entries')],
    [InlineKeyboardButton(text='Список задач', callback_data='task_list'), InlineKeyboardButton(text='Список чтения', callback_data='reading_list')],
    [InlineKeyboardButton(text='Журнал настроения', callback_data='mood_journal'), InlineKeyboardButton(text='Календарь', callback_data='calendar')],
])

language_selection = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Eng', callback_data='lang_en')],
    [InlineKeyboardButton(text='Ru', callback_data='lang_ru')]
])

sections_reply_en = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Diary'), KeyboardButton(text='Diary Entries')],
    [KeyboardButton(text='Task List'), KeyboardButton(text='Reading List')],
    [KeyboardButton(text='Mood Journal'), KeyboardButton(text='Calendar')],
], resize_keyboard=True)

sections_reply_ru = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Дневник'), KeyboardButton(text='Записи дневника')],
    [KeyboardButton(text='Список задач'), KeyboardButton(text='Список чтения')],
    [KeyboardButton(text='Журнал настроения'), KeyboardButton(text='Календарь')],

], resize_keyboard=True)

