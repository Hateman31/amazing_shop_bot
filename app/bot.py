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
from telebot.types import LabeledPrice, ShippingOption
import utils
from pathlib import Path
from datetime import datetime

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
    user_id = query.from_user.id
    orders = db_client.get_orders_history(user_id)
    now = datetime.now()
    headers = 'order_date full_price'.split(' ')

    folder = Path.cwd().parent / "docs" / f'{user_id}'

    if not folder.exists():
        folder.mkdir()

    fname = folder / f'{now.year}-{now.month}-{now.day}_{now.hour}-{now.minute}.csv'
    utils.rows_to_csv(orders, fname, headers=headers)

    bot.delete_message(
        chat_id=query.message.chat.id
        ,message_id=query.message.id
    )
    if orders:
        bot.send_document(
            chat_id=query.message.chat.id
            , document= open(fname, 'rb').read()
            , visible_file_name=fname.name
        )
        bot.send_message(
            chat_id=query.message.chat.id
            , text='This file is containing all your purchases!'
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

    order_id = query.data.replace('pay_order', '')

    # print(order_id)
    total_price = db_client.get_order_total_price(order_id)

    bot.edit_message_reply_markup(
        chat_id=query.message.chat.id
        ,message_id=query.message.id
        ,reply_markup=None
    )

    prices = [
        LabeledPrice(label='Working Time Machine', amount=int(total_price * 100))
    ]

    customer_id = query.from_user.id
    shopping_cart[customer_id] = order_id

    invoice = bot.send_invoice(
        query.message.chat.id,  # chat_id
        'Working Time Machine',  # title
        ' Want to visit your great-great-great-grandparents? Make a fortune at the races? Shake hands with Hammurabi and take a stroll in the Hanging Gardens? Order our Working Time Machine today!',
        # description
        'HAPPY FRIDAYS COUPON',  # invoice_payload
        config.payment_api_token,  # provider_token
        'rub',  # currency
        prices,  # prices
        photo_url='http://erkelzaar.tsudao.com/models/perrotta/TIME_MACHINE.jpg',
        photo_height=512,  # !=0/None or picture won't be shown
        photo_width=512,
        photo_size=512,
        is_flexible=False,  # True If you need to set up Shipping Fee
        start_parameter='time-machine-example'
    )




@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    print(pre_checkout_query)
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Aliens tried to steal your card's CVV, but we successfully protected your credentials,"
                                                " try to pay again in a few minutes, we need a small rest.")
@bot.shipping_query_handler(func=lambda query: True)
def shipping(shipping_query):
    print(shipping_query)
    # bot.answer_shipping_query(shipping_query.id, ok=True, shipping_options=shipping_options,
    #                           error_message='Oh, seems like our Dog couriers are having a lunch right now. Try again later!')


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    customer_id = message.from_user.id
    order_id = int(shopping_cart[customer_id])

    db_client.pay_order(order_id)

    bot.send_message(message.chat.id,
                     'Hoooooray! Thanks for payment! We will proceed your order for `{} {}` as fast as possible! '
                     'Stay in touch.\n\nUse /buy again to get a Time Machine for your friend!'.format(
                         message.successful_payment.total_amount / 100, message.successful_payment.currency),
                     parse_mode='Markdown')

@bot.callback_query_handler(func=lambda x: x.data.startswith('edit_order'))
def edit_order(query):
    pass


@bot.callback_query_handler(func=lambda x: x.data.startswith('cancel_order'))
def cancel_order(query):
    order_id = query.data.replace('cancel_order', '')

    if order_id:
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

# bot.send_invoice()

bot.set_my_commands(
    commands=[
        types.BotCommand('/start', 'Deal with shopping!'),
    ]
)

bot.polling()