import psycopg2

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