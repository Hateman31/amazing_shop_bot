import config
import telebot
from telebot import formatting
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
    show_start_menu(msg)

def show_start_menu(event):
    chat_id = None
    if type(event) == types.Message:
        chat_id = event.chat.id
    else:
        chat_id = event.message.chat.id

    client = db_client.get_customer(event.from_user.id)
    print(f'show_start_menu__func {client=} {event.from_user.id=}')

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
            chat_id=chat_id
            ,text='What do you wish?'
            ,reply_markup=kb
        )
    else:
        db_client.add_new_customer(event.from_user.id)
        bot.send_message(
            chat_id=chat_id
            , text=f'Welcome to our online store,  {event.from_user.first_name}!'
            , reply_markup=kb
        )

@bot.callback_query_handler(func=lambda q: q.data.startswith('make_order'))
def make_order(query):
    customer_id = query.from_user.id
    order_id = db_client.create_order(customer_id)

    shopping_cart[customer_id] = order_id

    catalog = db_client.get_catalog(order_id)
    kb = get_catalog_kb(catalog)

    bot.delete_message(
        chat_id=query.message.chat.id
        ,message_id=query.message.id
    )

    bot.send_message(
        chat_id=query.message.chat.id
        , text='Choose item for your order:'
        , reply_markup=kb
    )


@bot.callback_query_handler(func=lambda q: q.data.startswith('add_item'))
def add_item(query):
    customer_id = query.from_user.id
    product_id = int(query.data.replace('add_item_', ''))

    product = db_client.get_product(product_id)
    quantity = 1
    # 1. Создать заказ (таблица Orders)
    # 2. Получить order_id
    order_id = int(shopping_cart[customer_id])

    # 3. Добавить запись в Order_Items , quantity = 1
    # 4. Получить order_item_id
    try:
        order_item_id = db_client.add_item_to_order(order_id, product_id)
    except:
        # print('add_item ', order_id)
        raise SystemExit

    shopping_cart.incr(order_item_id)
    # 5. Вывести меню:
    #     - Добавить 1 шт.
    #     - Отнять 1 шт.
    #     - Ок
    #     - Отмена


    kb = Order_Item_Menu(order_item_id)


    bot.delete_message(
        chat_id=query.message.chat.id
        ,message_id=query.message.id
    )

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
def item_menu(query):
    order_item_id = int(query.data.replace('add_one', ''))

    product_name = query.message.text.split(':')[0]
    quantity = shopping_cart.incr(order_item_id)

    db_client.set_item_quantity(order_item_id, quantity)

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

    catalog = db_client.get_catalog(order_id)
    kb = get_catalog_kb(catalog, order_id)

    quantity = int(shopping_cart[order_item_id])
    db_client.set_item_quantity(order_item_id, quantity)

    del shopping_cart[order_item_id]

    bot.delete_message(
        query.message.chat.id
        , query.message.id)

    bot.send_message(
        chat_id=query.message.chat.id
        , text='Choose item for your order:'
        , reply_markup=kb
    )

@bot.callback_query_handler(func=lambda x: x.data.startswith('confirm_order') )
def confirm_order(query):
    order_id = query.data.replace('confirm_order', '')
    summary = db_client.get_order_summary(order_id)

    bot.delete_message(
        chat_id=query.message.chat.id
        ,message_id=query.message.id
    )

    bot.answer_callback_query(
        callback_query_id=query.id
        , text=f'Ваш заказ #{order_id} готов к оплате.'
    )

    bot.send_message(
        chat_id=query.message.chat.id
        , text = summary
        , parse_mode='Markdown'
        , reply_markup=order_confirmation_kb(order_id)
    )

@bot.callback_query_handler(func=lambda x: x.data.startswith('pay_order'))
def pay_order(query):
    pass

@bot.callback_query_handler(func=lambda x: x.data.startswith('edit_order'))
def pay_order(query):
    pass


@bot.callback_query_handler(func=lambda x: x.data.startswith('cancel_order'))
def pay_order(query):
    order_id = query.data.replace('cancel_order', '')

    db_client.cancel_order(order_id)

    bot.delete_message(
        chat_id=query.message.chat.id
        ,message_id=query.message.id
    )

    show_start_menu(query)




@bot.callback_query_handler(func=lambda x: x.data.startswith('orders_history') )
def orders_history(query):
    orders_history_table = 'Nothing'

    bot.answer_callback_query(
        callback_query_id=query.id
        ,text=orders_history_table
    )

@bot.callback_query_handler(func=lambda x: True )
def answer_any(query):
    bot.answer_callback_query(
        callback_query_id=query.id
        ,text=query.data
    )

# bot.delete_my_commands(
#     scope=types.BotCommandScopeDefault()
# )

bot.set_my_commands(
    commands=[
        types.BotCommand('/start', 'Deal with shopping!'),
    ]
)

bot.polling()