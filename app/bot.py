import config
import telebot
from telebot import types
import logging
telebot.logger.setLevel(logging.INFO)
from db_actions import SQL
from db_config import CONN_STR

db_client = SQL(CONN_STR)

bot = telebot.TeleBot(config.token)

@bot.message_handler(commands=['start'])
def start(msg):
    client = db_client.get_customer(msg.from_user.id)
    kb=types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(
            text='Make order'
            , callback_data=f'make_order'
        ),
        types.InlineKeyboardButton(
            text='View orders history'
            , callback_data=f'orders_history'
        ),
    )
    if client:
        bot.send_message(
            chat_id=msg.chat.id
            ,text='What do you wish?'
            ,reply_markup=kb
        )
    else:
        db_client.add_new_customer(msg.from_user.id)
        bot.send_message(
            chat_id=msg.chat.id
            , text=f'Welcome to our online store,  {msg.from_user.first_name}!'
            , reply_markup=kb
        )

@bot.callback_query_handler(func=lambda q: q.data.startswith('make_order'))
def make_order(query):
    kb = types.InlineKeyboardMarkup()
    catalog = db_client.get_catalog()
    for item in catalog:
        kb.add(
            types.InlineKeyboardButton(
                text=f'{item[1]}({item[2]})'
                ,callback_data=f'add_item_{item[0]}'
            )
        )

    bot.send_message(
        chat_id=query.message.chat.id
        , text='Choose item for your order:'
        , reply_markup=kb
    )


@bot.callback_query_handler(func=lambda q: q.data.startswith('add_item'))
def add_item(query):
    bot.answer_callback_query(
        callback_query_id=query.id,
        text=query.data)



@bot.callback_query_handler(func=lambda q: q.data.startswith('orders_history'))
def get_orders_history(query):
    orders = db_client.get_orders_history(query.from_user.id)

    bot.delete_message(
        chat_id=query.message.chat.id
        ,message_id=query.message.id
    )
    if orders:
        bot.send_message(
            chat_id=query.message.chat.id
            , text=orders
        )
    else:
        bot.send_message(
            chat_id=query.message.chat.id
            , text='You dont have any orders!'
        )


bot.infinity_polling()