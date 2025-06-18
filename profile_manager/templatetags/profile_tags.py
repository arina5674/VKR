import datetime

from django import template

register = template.Library()

@register.filter
def age_format(birthday):
    if not birthday:
        return "Возраст не указан"
    years = datetime.datetime.now().year - birthday.year
    if years == 1 or (years % 10 == 1 and years % 100 != 11):
        return f"{years} год"
    elif 2 <= years % 10 <= 4 and (years % 100 < 10 or years % 100 >= 20):
        return f"{years} года"
    else:
        return f"{years} лет"
