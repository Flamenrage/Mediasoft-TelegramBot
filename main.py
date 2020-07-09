import telebot
import requests
import datetime
import xmltodict
import random, os
from telebot import types
from bs4 import BeautifulSoup as BS
import configuration
import logging

bot = telebot.TeleBot(configuration.token)
logger = telebot.logger
logging.basicConfig(filename='logger.log', filemode='w', format=' %(asctime)s - %(levelname)s - %(message)s')
telebot.logger.setLevel(logging.DEBUG)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    button_weather = types.KeyboardButton('Узнать погоду')
    button_money = types.KeyboardButton('Курс доллара/евро:')
    button_cookie = types.KeyboardButton('Печенье с предсказанием')
    button_return = types.KeyboardButton('Закрыть меню')
    markup.add(button_weather, button_money, button_return, button_cookie)
    bot.send_message(message.chat.id,
                     "Привет! Меня зовут Афина,я Ваш личный помощник,"
                     "умею выводить курсы валют, дарить печеньки и предсказывать погоду!")
    sms = bot.send_message(message.chat.id,
                           "Выберите:", reply_markup=markup)
    bot.register_next_step_handler(sms, process_select_step)


def process_select_step(req):
    try:
        if req.text == 'Курс доллара/евро:':
            money(req)
        elif req.text == 'Узнать погоду':
            weather(req)
        elif req.text == 'Закрыть меню':
            # убрать клавиатуру
            markup = types.ReplyKeyboardRemove(selective=False)
            bot.send_message(req.chat.id, "Чтож, увидимся позже, напиши /start или /help, чтобы возобновить работу.\n",
                             reply_markup=markup)
        elif req.text == "/start" or req.text == "/help":
            send_welcome(req)
        elif req.text == 'Печенье с предсказанием':
            cookie(req)
        else:
            bot.send_message(req.chat.id, "Извините, я еще только учусь понимать человеческую речь :)\n")
            send_welcome(req)
    except Exception as e:
        bot.reply_to(req, "Извините, что-то пошло не так...")


# Погода
def weather(message):
    r = requests.get('https://sinoptik.ua/погода-ульяновск')
    html = BS(r.content, 'html.parser')

    for el in html.select('#content'):
        temp_low = el.select('.temperature .min')[0].text
        temp_high = el.select('.temperature .max')[0].text
        text = el.select('.wDescription .description')[0].text
    bot.send_message(message.chat.id, "Прогноз погоды на сегодня:\n" +
                     temp_low + ', ' + temp_high + '\n' + text)
    bot.register_next_step_handler(message, process_select_step)


# Печенье с предсказанием
def cookie(message):
    path = r'pic'
    ph = random.choice([
        x for x in os.listdir(path)
        if os.path.isfile(os.path.join(path, x))
    ])
    with open(os.path.join(path, ph), 'rb') as photo:
        bot.send_photo(message.chat.id, photo)
    photo.close()
    bot.register_next_step_handler(message, process_select_step)


# Курс валют
def money(message):
    # URL запроса
    get_curl = "http://www.cbr.ru/scripts/XML_daily.asp"
    # Формат даты: день/месяц/год
    date_format = "%d/%m/%Y"

    # Дата запроса
    today = datetime.datetime.today()
    params = {
        "date_req": today.strftime(date_format),
    }
    r = requests.get(get_curl, params=params)
    data = xmltodict.parse(r.text)
    # Ищем по @ID
    section_id_usd = 'R01235'  # неизменный id доллара
    section_id_eur = 'R01239'  # неизменный id евро

    for item in data['ValCurs']['Valute']:
        if item['@ID'] == section_id_usd:
            rate_usd = item['Value']
        elif item['@ID'] == section_id_eur:
            rate_eur = item['Value']
            break
    bot.send_message(message.chat.id, 'Курс валют на сегодня:\n USD: %s\n EUR: %s' % (rate_usd, rate_eur))
    bot.register_next_step_handler(message, process_select_step)


if __name__ == '__main__':
    bot.polling(none_stop=True)