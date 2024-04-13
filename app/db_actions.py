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

    def fetch_rows(self, sql, *params):
        with psycopg2.connect(self.conn_str) as conn:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                return cursor.fetchall()

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
                    'select * '
                        'from Customers where customer_id = %s '
                    , [user_id]
                )

                return cursor.fetchone()

    def get_catalog(self, order_id = None, page_num = 0):
        catalog_query = 'select product_id, product_name, price, category from Products '
        page = ' limit 5 offset 5 * %s'
        with psycopg2.connect(self.conn_str) as conn:
            with conn.cursor() as cursor:
                if order_id:
                    catalog_query += (
                        'where product_id not in ('
                            'select product_id from Order_Items where order_id = %s)'
                            + page
                    )
                    cursor.execute(
                        catalog_query, [order_id, page_num]
                    )
                else:
                    cursor.execute(
                        catalog_query + page
                        , [page_num]
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


    def get_order_id(self, order_item_id):
        sql = 'select order_id from order_items where order_item_id = %s'
        with psycopg2.connect(self.conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, [order_item_id])
                return cursor.fetchone()[0]


    def set_item_quantity(self, order_item_id, quantity):
        sql = ('update public.order_items set quantity = %s '
                + 'where order_item_id = %s')
        # print(f'{order_item_id=}, {quantity=}')
        with psycopg2.connect(self.conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, [quantity, order_item_id])
                conn.commit()


    def get_order_summary(self, order_id):
        sql = ("with main as ( "+
                "	select  1 x,product_name,  quantity::text quantity, (price * quantity) full_price  "+
                "	from Order_Items oims "+
                "	join Products p "+
                "		on p.product_id = oims.product_id "+
                "	where order_id = %s "+
                ")	 "+
                "select * from main "+
                "union  "+
                "select  0 x,'Total', count(1) || ' items', sum(full_price)  "+
                "from main "+
                "order by 1 ")
        # print(order_id)
        return self.fetch_rows(sql, order_id)

    def get_pages(self,order_id = None,  page_num = 0):
        prev_page , next_page = False, False
        catalog_query = (
            '''select 
                    %s > 0 prev_page
                    , %s < (count(1) / 5 )::int+1 next_page
            from products 
            where is_active = 1'''
        )
        if order_id:
            catalog_query += (
                    ' and product_id not in ('
                    'select product_id from Order_Items where order_id = %s)')
            result = self.fetch_rows(catalog_query, page_num, page_num, order_id)
        else:
            result = self.fetch_rows(catalog_query, page_num, page_num)

        if result:
            prev_page, next_page = result[0]
        return prev_page, next_page

    def get_order_total_price(self, order_id):
        sql = """select sum(price*quantity) full_price
                from Order_items oims
                join Products p
                    on p.product_id = oims.product_id
                    and order_id = %s
                group by order_id"""

        return self.fetch_rows(sql, order_id)[0][0]

    def pay_order(self, order_id):
        self.__set_order_status(order_id, 2)

    def cancel_order(self, order_id):
        self.__set_order_status(order_id, 3)


    def __set_order_status(self, order_id, status):
        sql = (
            'update orders set status = %s '
            'where order_id = %s'
        )
        self.execute_sql(sql, status, order_id)


    def get_orders_history(self, customer_id, period=None):
        sql = 'select order_date, full_price, status from Orders_history_vw where customer_id = %s'
        rows = []
        if not period:
            rows = self.fetch_rows(sql, customer_id)
        else:
            interval = f'{period} month'
            sql += " and order_date > (now()::date - interval %s )"
            rows = self.fetch_rows(sql, customer_id, interval)
        rows = [
            (order_date, f'{full_price:.2f}', status)
            for order_date, full_price, status in rows
        ]
        return rows

    def check_opened_order(self, customer_id):
        sql = """
                select order_id
                from orders
                where status = 1
                    AND customer_id = %s
                order by order_id
                limit 1"""

        rows = self.fetch_rows(sql, customer_id)
        return rows[0][0] if rows else None

if __name__ == '__main__':
    from db_config import CONN_STR

    db_client = SQL(CONN_STR)