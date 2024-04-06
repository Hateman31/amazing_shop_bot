
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
