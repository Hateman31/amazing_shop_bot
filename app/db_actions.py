import psycopg2
from collections import namedtuple
from dataclasses import  dataclass

@dataclass
class Product:
    name: str
    price: int

class SQL:
    def __init__(self, conn_str):
        self.conn_str = conn_str

    def execute_sql(self, sql, *params):
        try:
            with psycopg2.connect(self.conn_str) as conn:
                with conn.cursor() as cursor:
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                conn.commit()
        except psycopg2.DatabaseError as err:
            raise err

    def add_new_customer(self, user_id):
        query_ = (
            'insert into customers(customer_id) '
            'values (%s)')

        self.execute_sql(
                query_, user_id
        )

        return True

    def get_customer(self, user_id):
        with psycopg2.connect(self.conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    'select * from Customers where customer_id = %s '
                    , [user_id]
                )

                return cursor.fetchone()

    def get_orders_history(self, user_id):
        with psycopg2.connect(self.conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    'select order_date, full_price from '
                      + 'Orders_history_vw where customer_id = %s '
                    , [user_id]
                )

                return cursor.fetchall()

    def get_catalog(self):
        catalog_query = 'select * from Products'
        with psycopg2.connect(self.conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    catalog_query
                )

                return cursor.fetchall()


    def create_order(self, customer_id):
        new_order_query = (
            'insert into Orders(customer_id, order_date) '
            'values (%s, now()::date)'
        )
        last_order_query = (
            'select order_id from Orders where customer_id=%s '
            'order by order_id desc limit 1'
        )

        with psycopg2.connect(self.conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    new_order_query, [customer_id]
                )
                conn.commit()
                cursor.execute(
                    last_order_query, [customer_id]
                )
                return cursor.fetchone()[0]

    def add_item_to_order(self, order_id, product_id):
        new_item_query = (
            'insert into Order_Items(order_id, product_id, quantity) '
            'values (%s, %s, 1)'
        )
        last_item_query = (
            'select order_item_id from Order_Items '
            'where order_id=%s and product_id=%s'
        )

        with psycopg2.connect(self.conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    new_item_query, [order_id, product_id]
                )
                conn.commit()
                cursor.execute(
                    last_item_query, [order_id, product_id]
                )
                return cursor.fetchone()[0]


    def get_product(self, prodcut_id):
        sql = 'select product_name, price from Products where product_id=%s'
        with psycopg2.connect(self.conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, [prodcut_id])
                product = cursor.fetchone()
                return Product(product[0], product[1])
