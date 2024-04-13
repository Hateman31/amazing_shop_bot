from telebot import types

def Order_Item_Menu(order_item_id):
    return types.InlineKeyboardMarkup(row_width=4).add(
        types.InlineKeyboardButton('+1', callback_data=f'add_one{order_item_id}')
        , types.InlineKeyboardButton('🆗', callback_data=f'confirm_item{order_item_id}')
        , types.InlineKeyboardButton('❌', callback_data=f'cancel{order_item_id}')
        , types.InlineKeyboardButton('-1', callback_data=f'reduce_one{order_item_id}')
    )


def order_confirmation_kb(order_id, payable = True):
    if payable:
        return types.InlineKeyboardMarkup(row_width=4).add(
            types.InlineKeyboardButton('Pay 💲', callback_data=f'pay_order{order_id}')
            , types.InlineKeyboardButton('Edit 📝', callback_data=f'edit_order{order_id}')
            , types.InlineKeyboardButton('Cancel ❌', callback_data=f'cancel_order{order_id}')
        )
    return types.InlineKeyboardMarkup(row_width=4).add(
        types.InlineKeyboardButton('Edit 📝', callback_data=f'edit_order{order_id}')
        , types.InlineKeyboardButton('Cancel ❌', callback_data=f'cancel_order{order_id}')
    )

def get_period_options_kb():
    return types.InlineKeyboardMarkup(row_width=4).add(
        types.InlineKeyboardButton('1 month', callback_data=f'history_1')
        , types.InlineKeyboardButton('3 month', callback_data=f'history_3')
        , types.InlineKeyboardButton('6 month', callback_data=f'history_6')
    ).add(
        types.InlineKeyboardButton(
            'Go Back'
            , callback_data='show_start_menu'
        )
    )

def get_catalog_kb(catalog, order_id = None,page_num=0,  prev_page = False, next_page = False):
    kb = types.InlineKeyboardMarkup()

    order_id = order_id or ''

    next_btn = types.InlineKeyboardButton(
        text='>>'
        ,callback_data=f'get_page{page_num+1}'
    )

    prev_btn = types.InlineKeyboardButton(
        text='<<'
        , callback_data=f'get_page{page_num - 1}'
    )

    cancel_btn = types.InlineKeyboardButton(
                text='Cancel'
                ,callback_data=f'cancel_order{order_id}'
            )
    for item in catalog:
        item_id, product_name, price, category = item
        kb.add(
            types.InlineKeyboardButton(
                text=f'{product_name}({price}$)({category})'
                , callback_data=f'add_item_{item_id}'
            )
        )

    if prev_page and next_page:
        kb.add(prev_btn, next_btn)
    elif prev_page:
        kb.add(prev_btn)
    else:
        kb.add(next_btn)

    if order_id:
        ok_btn = types.InlineKeyboardButton(
                text='OK'
                , callback_data=f'confirm_order{order_id}'
            )
        kb.add(
            ok_btn
            , cancel_btn
        )
    else:
        kb.add(cancel_btn )
    return kb


PERIOD_OPTIONS = get_period_options_kb()

