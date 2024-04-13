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
from shipping import getShippingOptions

db_client = SQL(CONN_STR)
shopping_cart = Vedis(':mem:')

bot = telebot.TeleBot(config.token)

SHIPPING_OPTIONS = getShippingOptions()

@bot.message_handler(commands=['start'])
def start(msg):
    show_start_menu(msg)

@bot.callback_query_handler(func=lambda x: x.data == 'show_start_menu')
def start_menu(query):
    bot.delete_message(
        chat_id=query.message.chat.id
        ,message_id=query.message.id
    )

    show_start_menu(query)

def show_start_menu(event):
    chat_id = None
    if type(event) == types.Message:
        chat_id = event.chat.id
    else:
        chat_id = event.message.chat.id

    client = db_client.get_customer(event.from_user.id)

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
    bot.delete_message(
        chat_id=query.message.chat.id
        ,message_id=query.message.id
    )

    page_num = 0
    order_id = db_client.check_opened_order(customer_id)
    if order_id:
        bot.send_message(
            chat_id=query.message.chat.id
            , text='You have 1 unpaid order! Do you want to proceed your purchase ?'
            , reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton('Proceed purchase', callback_data=f'confirm_order{order_id}')
                    ,types.InlineKeyboardButton('Get back', callback_data='show_start_menu')
            )
        )

        return

    order_id = db_client.create_order(customer_id)
    shopping_cart[customer_id] = order_id
    catalog = db_client.get_catalog(order_id, page_num=page_num)
    prev_page, next_page = db_client.get_pages(order_id, page_num)
    kb = get_catalog_kb(catalog, next_page=next_page, prev_page=prev_page)

    msg = {
        True:'Choose item for your order:'
        , False: "We have nothing to offer you 😟"
    }

    bot.send_message(
        chat_id=query.message.chat.id
        , text=msg[bool(catalog)]
        , reply_markup=kb
    )

@bot.callback_query_handler(func=lambda q: q.data.startswith('get_page'))
def get_catalog_page(query):
    customer_id = query.from_user.id
    order_id = db_client.check_opened_order(customer_id)
    page_num = int(query.data.replace('get_page', ''))

    catalog = db_client.get_catalog(order_id, page_num)
    prev_page, next_page = db_client.get_pages(order_id, page_num)

    kb = get_catalog_kb(catalog, order_id, page_num, prev_page, next_page)

    bot.edit_message_text(
        text='Choose item for purchase'
        , chat_id=query.message.chat.id
        , message_id=query.message.id
        ,reply_markup=kb
    )

@bot.callback_query_handler(func=lambda q: q.data.startswith('add_item'))
def add_item(query):
    customer_id = query.from_user.id
    product_id = int(query.data.replace('add_item_', ''))

    product = db_client.get_product(product_id)
    quantity = 1
    # 1. Создать заказ (таблица Orders)
    # 2. Получить order_id
    # order_id = int(shopping_cart[customer_id])
    order_id = db_client.check_opened_order(customer_id)

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

@bot.callback_query_handler(func=lambda x: x.data.startswith('history'))
def get_orders_history(query):
    user_id = query.from_user.id
    period = query.data.replace('history_', '')
    orders = db_client.get_orders_history(user_id, period)

    now = datetime.now()
    headers = 'order_date full_price order_status'.split(' ')

    folder = Path.cwd().parent / "docs" / f'{user_id}'

    if not folder.exists():
        folder.mkdir()

    period_name = f"{period} months" if period > '1' else f"{period} month"
    fname = folder / f'{now:%Y-%m-%d_%H-%M}({period_name}).csv'
    utils.rows_to_csv(orders, fname, headers=headers)

    bot.delete_message(
        chat_id=query.message.chat.id
        , message_id=query.message.id
    )

    if orders:
        bot.send_document(
            chat_id=query.message.chat.id
            , document=open(fname, 'rb').read()
            , visible_file_name=fname.name
        )
    else:
        bot.send_message(
            chat_id=query.message.chat.id
            , text='You dont have any orders!'
        )

@bot.callback_query_handler(func=lambda q: q.data.startswith('orders_history'))
def get_orders_history_options(query):
    bot.delete_message(
        chat_id=query.message.chat.id
        , message_id=query.message.id
    )

    bot.send_message(
        chat_id=query.message.chat.id
        ,text='Choose period for report:'
        ,reply_markup = PERIOD_OPTIONS
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
    payable = len(summary) > 1

    summary_msg = utils.get_order_summary_msg(summary)

    bot.edit_message_text(
        chat_id=query.message.chat.id
        , message_id=query.message.id
        , text=summary_msg
        , parse_mode='Markdown'
        , reply_markup=order_confirmation_kb(order_id, payable = payable)
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
    total_amount=int(total_price * 100)

    prices = [
        LabeledPrice(label='Working Time Machine', amount=total_amount)
    ]

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=f'Pay {total_price: .2f}', pay=True))
    kb.add(types.InlineKeyboardButton(text='Reject payment ❌', callback_data='reject_payment'))

    invoice = bot.send_invoice(
        query.message.chat.id,  # chat_id
        'Working Time Machine',  # title
        ' Want to visit your great-great-great-grandparents? Make a fortune at the races? Shake hands with Hammurabi and take a stroll in the Hanging Gardens? Order our Working Time Machine today!',
        # description
        'HAPPY FRIDAYS COUPON',  # invoice_payload
        config.payment_api_token,  # provider_token
        'rub',  # currency
        prices,  # prices
        reply_markup = kb,
        photo_url='http://erkelzaar.tsudao.com/models/perrotta/TIME_MACHINE.jpg',
        photo_height=512,  # !=0/None or picture won't be shown
        photo_width=512,
        photo_size=512,
        is_flexible=True,  # True If you need to set up Shipping Fee
        need_shipping_address= True
    )

@bot.callback_query_handler(func=lambda q: q.data.startswith('reject_payment'))
def reject_payment(query):
    bot.delete_message(
        query.message.chat.id
        ,query.message.id
    )
    show_start_menu(query)

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    print(pre_checkout_query)
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Aliens tried to steal your card's CVV, but we successfully protected your credentials,"
                                                " try to pay again in a few minutes, we need a small rest.")
@bot.shipping_query_handler(func=lambda query: True)
def shipping(shipping_query):
    # print(SHIPPING_OPTIONS)
    bot.answer_shipping_query(
        shipping_query.id,
        ok=True,
        shipping_options=SHIPPING_OPTIONS,
        error_message='Oh, seems like our Dog couriers are having a lunch right now. Try again later!')


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
    customer_id = query.from_user.id
    order_id = db_client.check_opened_order(customer_id)

    bot.edit_message_text(
        text='What do you want to do?'
        ,chat_id=query.message.chat.id
        ,message_id=query.message.id
        , reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton('➕Add one item', callback_data=f'get_page0'),
        ).add(
            types.InlineKeyboardButton('➖Delete one item', callback_data=f'del_one{order_id}'),
        ).add(
            types.InlineKeyboardButton('📝Item amount edit', callback_data=f'edit_amount{order_id}'),
        ).add(
            types.InlineKeyboardButton('❌Cancel', callback_data=f'confirm_order{order_id}'),
        )
    )




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


bot.set_my_commands(
    commands=[
        types.BotCommand('/start', 'Deal with shopping!'),
    ]
)

bot.polling()