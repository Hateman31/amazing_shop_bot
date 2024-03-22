import psycopg2
import db_config

schema_sql = open('schema.sql', encoding='utf-8').read()

def create_schema(conn_str, sql):
    try:
        with psycopg2.connect(conn_str) as conn:
            print('Connection is created!')
            with conn.cursor() as cursor:
                cursor.execute(sql)
                print('Database are configured!')
    except psycopg2.DatabaseError as err:
        raise err


if __name__ == '__main__':
    create_schema(db_config.CONN_STR, schema_sql)