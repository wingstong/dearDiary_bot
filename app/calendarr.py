from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import calendar


def create_calendar(year: int = datetime.now().year, month: int = datetime.now().month) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=7)
    # Первая строка - Месяц и Год
    markup.add(InlineKeyboardButton(text=f'{calendar.month_name[month]} {year}', callback_data='ignore'))

    # Вторая строка - Дни недели
    week_days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
    for day in week_days:
        markup.insert(InlineKeyboardButton(text=day, callback_data='ignore'))

    # Дни месяца
    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        for day in week:
            if day == 0:
                markup.insert(InlineKeyboardButton(text=' ', callback_data='ignore'))
            else:
                markup.insert(InlineKeyboardButton(text=str(day), callback_data=f'calendar;{year};{month};{day}'))

    # Последняя строка - кнопки навигации
    markup.add(
        InlineKeyboardButton(text='<<', callback_data=f'calendar_prev;{year};{month}'),
        InlineKeyboardButton(text='>>', callback_data=f'calendar_next;{year};{month}')
    )

    return markup
