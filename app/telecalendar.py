import calendar
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_calendar(language, year, month):
    markup = InlineKeyboardBuilder()

    # Названия месяцев и дней недели
    if language == 'en':
        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
    else:
        months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

    markup.row(InlineKeyboardButton(text=f'{months[month-1]} {year}', callback_data='ignore'))

    markup.row(*(InlineKeyboardButton(text=day, callback_data='ignore') for day in days))

    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        row = [InlineKeyboardButton(text=str(day) if day != 0 else ' ', callback_data=f'DAY_{day}_{month}_{year}' if day != 0 else 'ignore') for day in week]
        markup.row(*row)

    prev_month = InlineKeyboardButton(text='<', callback_data=f'PREV-MONTH_{month}_{year}')
    back = InlineKeyboardButton(text='back', callback_data='back')
    events = InlineKeyboardButton(text='events', callback_data='show_events')
    next_month = InlineKeyboardButton(text='>', callback_data=f'NEXT-MONTH_{month}_{year}')
    markup.row(prev_month, events, back, next_month)

    return markup.as_markup()
