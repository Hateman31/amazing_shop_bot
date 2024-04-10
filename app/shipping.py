from telebot.types import ShippingOption, LabeledPrice


def getShippingOptions():

    Regular_Post_Shipping = ShippingOption(
        title='Regular Post Shipping'
        ,id='regular'
    )
    for price in [
        LabeledPrice(
            label='With Ensurance'
            , amount=200_00
        ),
        LabeledPrice(
            label='Without Ensurance'
            , amount=50_00
        ),
    ]: Regular_Post_Shipping = Regular_Post_Shipping.add_price(price)

    Courier_Shipping  = ShippingOption(
        title='Courier Shipping'
        ,id='courier'
    )
    for price in [
        LabeledPrice(
            label='With Ensurance'
            , amount=500_00
        ),
        LabeledPrice(
            label='Without Ensurance'
            , amount=150_00
        ),
    ]:
        # Courier_Shipping = Courier_Shipping.add_price(price)
        Courier_Shipping.add_price(price)

    Itself_Shipping = ShippingOption(
        title='Itself Shipping'
        , id='itself'
    ).add_price(
        LabeledPrice(
            label='Without Ensurance'
            , amount=20_00
        )
    )

    # return [Courier_Shipping]

    return [
        Regular_Post_Shipping
        , Courier_Shipping
        , Itself_Shipping
    ]

if __name__ == '__main__':
    opts = getShippingOptions()[0]

    for price in opts.prices:
        print(
            price.label
            ,price.amount
        )
