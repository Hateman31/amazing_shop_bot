from telebot import types

def Order_Item_Menu(order_item_id):
    return types.InlineKeyboardMarkup(row_width=4).add(
        types.InlineKeyboardButton('+1', callback_data=f'add_one{order_item_id}')
        , types.InlineKeyboardButton('🆗', callback_data=f'confirm_item{order_item_id}')
        , types.InlineKeyboardButton('❌', callback_data=f'cancel{order_item_id}')
        , types.InlineKeyboardButton('-1', callback_data=f'reduce_one{order_item_id}')
    )


def order_confirmation_kb(order_id):
    return types.InlineKeyboardMarkup(row_width=4).add(
        types.InlineKeyboardButton('🆗', callback_data=f'confirm_order{order_id}')
        , types.InlineKeyboardButton('❌', callback_data=f'cancel_order{order_id}')
    )

def get_catalog_kb(catalog, order_id = None):
    kb = types.InlineKeyboardMarkup()

    order_id = order_id or ''

    cancel_btn = types.InlineKeyboardButton(
                text='Cancel'
                ,callback_data=f'cancel_order{order_id}'
            )
    for item in catalog:
        item_id, product_name, price,  _ = item
        kb.add(
            types.InlineKeyboardButton(
                text=f'{product_name}({price}$)'
                , callback_data=f'add_item_{item_id}'
            )
        )
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



