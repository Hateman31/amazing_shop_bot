import config
import telebot
from telebot import types
import logging
telebot.logger.setLevel(logging.INFO)
from db_actions import SQL
from db_config import CONN_STR
from vedis import Vedis
from keyboards import *

db_client = SQL(CONN_STR)
shopping_cart = Vedis(':mem:')

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

    catalog = db_client.get_catalog()
    kb = get_catalog_kb(catalog)

    bot.send_message(
        chat_id=query.message.chat.id
        , text='Choose item for your order:'
        , reply_markup=kb
    )


@bot.callback_query_handler(func=lambda q: q.data.startswith('add_item'))
def add_item(query):
    # bot.answer_callback_query(
    #     callback_query_id=query.id
    #     , text=query.data
    # )
    # return

    customer_id = query.from_user.id
    product_id = int(query.data.replace('add_item_', ''))

    product = db_client.get_product(product_id)
    quantity = 1
    # 1. Создать заказ (таблица Orders)
    # 2. Получить order_id
    order_id = db_client.create_order(customer_id)
    # 3. Добавить запись в Order_Items , quantity = 1
    # 4. Получить order_item_id
    order_item_id = db_client.add_item_to_order(order_id, product_id)
    shopping_cart.incr(order_item_id)
    # 5. Вывести меню:
    #     - Добавить 1 шт.
    #     - Отнять 1 шт.
    #     - Ок
    #     - Отмена

    kb = Order_Item_Menu(order_item_id)


    bot.send_message(
        chat_id=query.message.chat.id
        , text= f'{product.name}({product.price}): {quantity} units'
        ,reply_markup=kb
    )


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

@bot.callback_query_handler(func=lambda x: x.data.startswith('add_one'))
def order_menu(query):
    order_item_id = query.data.replace('add_one', '')
    # shopping_cart[order_item_id] += 1

    product_name = query.message.text.split(':')[0]
    quantity = shopping_cart.incr(order_item_id)

    kb = Order_Item_Menu(order_item_id)

    bot.edit_message_text(
        message_id=query.message.id
        ,chat_id=query.message.chat.id
        , text=f'{product_name}: {quantity} units'
        , reply_markup=kb
    )


@bot.callback_query_handler(func=lambda x: x.data.startswith('confirm_item'))
def confirm_item(query):
    order_item_id = query.data.replace('confirm_item', '')
    order_id = db_client.get_order_id(order_item_id)
    print(order_id)
    catalog = db_client.get_catalog(order_id)
    kb = get_catalog_kb(catalog, order_id)

    quantity = int(shopping_cart[order_item_id])
    db_client.set_item_quantity(order_item_id, quantity)

    del shopping_cart[order_item_id]

    bot.send_message(
        chat_id=query.message.chat.id
        , text='Choose item for your order:'
        , reply_markup=kb
    )

@bot.callback_query_handler(func=lambda x: x.data.startswith('confirm_order') )
def confirm_order(query):
    order_id = query.data.replace('confirm_order', '')

    summary = db_client.get_order_summary(order_id)

    bot.send_message(
        chat_id=query.message.chat.id
        , text= summary
        , parse_mode='Markdown'
        , reply_markup=order_confirmation_kb(order_id)
    )

@bot.callback_query_handler(func=lambda x: True )
def answer_any(query):
    bot.answer_callback_query(
        callback_query_id=query.id
        ,text=query.data
    )

bot.infinity_polling()