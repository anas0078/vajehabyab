import random
from datetime import date

WORDS_5 = ["کتاب","درخت","آسمان","زمین","آتش","شهر","کوه","دریا","جنگل","برف","باران","ستاره","خورشید","خانه","اتاق","پنجره","میز","صندلی","مدرسه","بازار","فوتبال","موسیقی","بهار","تابستان","پاییز","زمستان"]

def get_random_word(length=5):
    return random.choice(WORDS_5)

def get_daily_word():
    today = date.today()
    random.seed(today.year*10000+today.month*100+today.day)
    word = random.choice(WORDS_5)
    random.seed()
    return word
