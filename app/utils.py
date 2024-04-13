
def rows_to_csv(rows,filename, headers=None):
    with open(filename, 'w') as csv:
        if headers:
            for header in headers:
                csv.write(f"{header}\t")
            csv.write('\n')
        for row in rows:
            for value in row:
                csv.write(f"{value}\t")
            csv.write('\n')

    return True

def get_order_summary_msg(table):
    result = 'Product name  | Quantity | Full price\n'
    for _, product_name, quantity, full_price in table[1:]:
        table_row = f'{product_name} || {quantity} || {full_price}'
        result += table_row + '\n'

    total = table[0]
    total_str = f"{total[1]}: {total[2]} {total[3]} $"
    result += '-' * len(total_str) + '\n'
    result += total_str

    return result

if __name__ == '__main__':
    from db_actions import SQL
    from db_config import CONN_STR
    from pathlib import Path

    db_client = SQL(CONN_STR)

    fname = Path.cwd() / 'test.csv'
    rows = db_client.get_catalog()
    headers = 'product_id product_name price category'.split(' ')

    # print(rows)

    rows_to_csv(rows, fname, headers=headers)

    if fname.exists():
        print('CSV file successfully created!')
    else:
        print('CSV file creating failured!')
