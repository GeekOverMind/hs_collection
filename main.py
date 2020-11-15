import mysql.connector
import pandas as pd

file_xlsx = 'database_table.xlsx'
table_name = 'Packs'
with pd.ExcelFile(file_xlsx) as table:
    data_frame = table.parse(table_name)

dbconfig = {
    'host': 'localhost',
    'user': 'user_pc',
    'password': '1235',
    'database': 'hs_collection'
}


class OpenDatabase:
    def __init__(self, config: dict):
        self.configuration = config

    def __enter__(self):
        try:
            self.conn = mysql.connector.connect(**self.configuration)
            self.cursor = self.conn.cursor()
            return self.cursor
        except mysql.connector.errors.InterfaceError as err:
            print(f'Ошибка: {err}')
        except mysql.connector.errors.ProgrammingError as err:
            print(f'Ошибка: {err}')

    def __exit__(self, exc_type, exc_value, exc_trace):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

        if exc_type:
            with open('log_error.txt', 'a') as txt_file:
                print(f'{exc_type}: {exc_value}', file=txt_file)


def get_columns_name(df):
    addon_name = {}
    x, y = 0, 1

    try:
        while df.columns[x]:
            # addon_name.append(df.columns[x])
            addon_name[y] = df.columns[x]
            x += 2
            y += 1
    except IndexError:
        return addon_name


def get_hash(df):
    addon_name = []
    x = 1
    for name in df[0:0]:  # first string in a table
        if 'Unnamed' in name:
            continue

        # addon_name[x] = name
        addon_name.append(name)
        x += 1
    return addon_name


def create_database():
    conn = mysql.connector.connect(
        host='localhost',
        user='user_pc',
        password='1235'
    )
    cursor = conn.cursor()
    sql = """CREATE DATABASE IF NOT EXISTS hs_collection"""
    cursor.execute(sql)
    cursor.close()
    conn.close()


def create_addon():
    with OpenDatabase(dbconfig) as cursor:
        addon_name = get_hash(data_frame)
        sql = """
            CREATE TABLE IF NOT EXISTS addon(
                addon_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                addon_name VARCHAR(50)
                );
            """
        cursor.execute(sql)
        for name in addon_name:
            sql = f"""INSERT INTO addon (addon_name) VALUES (%s);"""
            cursor.execute(sql, (name,))


def create_card():
    card_number = (
        'first',
        'second',
        'third',
        'fourth',
        'fifth',
        'empty'
    )

    with OpenDatabase(dbconfig) as cursor:
        sql = """
            CREATE TABLE IF NOT EXISTS card(
                card_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                card_number VARCHAR(6)
                );
            """
        cursor.execute(sql)

        for position in card_number:
            sql = f"""INSERT INTO card (card_number) VALUES (%s);"""
            cursor.execute(sql, (position,))


def create_rare_card():
    rare_name = (
        'common',
        'rare',
        'epic',
        'legendary',
        'gold common',
        'gold rare',
        'gold epic',
        'gold legendary',
        'empty'
    )

    with OpenDatabase(dbconfig) as cursor:
        sql = """
            CREATE TABLE IF NOT EXISTS rare(
                rare_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                rare_name VARCHAR(14)
                );
            """
        cursor.execute(sql)

        for rare_type in rare_name:
            sql = f"""INSERT INTO rare (rare_name) VALUES (%s);"""
            cursor.execute(sql, (rare_type,))


def create_main_table():
    with OpenDatabase(dbconfig) as cursor:
        sql = """
            CREATE TABLE IF NOT EXISTS main_table(
                num_record INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                addon_id INT NOT NULL,
                CONSTRAINT addon_addon_id_fk
                FOREIGN KEY (addon_id)
                REFERENCES addon (addon_id),
                addon_pack_id INT NOT NULL,
                card_id INT NOT NULL,
                CONSTRAINT card_card_id_fk
                FOREIGN KEY (card_id)
                REFERENCES card (card_id),
                rare_id INT NOT NULL,
                CONSTRAINT rare_rare_id_fk
                FOREIGN KEY (rare_id)
                REFERENCES rare (rare_id),
                UNIQUE KEY unduplicated_record (addon_id, addon_pack_id, card_id)
                );
            """
        cursor.execute(sql)


def parser_to_sql():
    with OpenDatabase(dbconfig) as cursor:

        addon_id = 1

        rare_name = (
            'common',
            'rare',
            'epic',
            'legendary',
            'gold common',
            'gold rare',
            'gold epic',
            'gold legendary',
            'empty'
        )

        for num, col in enumerate(data_frame.columns):
            if num % 2 != 0:
                for pack_id, value in enumerate(data_frame[data_frame.columns[num]], 1):
                    if isinstance(value, str):
                        pack = value.split(', ')
                        card_id = 1
                        for card in pack:
                            print(addon_id, pack_id, card_id, card, sep=': ')
                            rare_id = rare_name.index(card) + 1
                            sql = """
                                INSERT INTO main_table(
                                    addon_id,
                                    card_id,
                                    rare_id,
                                    addon_pack_id
                                    )
                                VALUES (%s, %s, %s, %s);
                                """
                            cursor.execute(sql, (addon_id,
                                                 card_id,
                                                 rare_id,
                                                 pack_id)
                                           )
                            card_id += 1
                    else:
                        check = str(data_frame.iloc[pack_id - 1][data_frame.columns[num - 1]])
                        if 'nan' in check:
                            # if isinstance(data_frame.iloc[pack_id - 1][data_frame.columns[num - 1]], float):
                            break
                        else:
                            print(addon_id, pack_id, 'NONE', sep=': ')
                            sql = """
                                INSERT INTO main_table(
                                    addon_id,
                                    card_id,
                                    rare_id,
                                    addon_pack_id
                                    )
                                VALUES (%s, %s, %s, %s);
                                """
                            cursor.execute(sql, (addon_id,
                                                 6,
                                                 9,
                                                 pack_id)
                                           )
                addon_id += 1


def start_pars():
    create_database()
    create_addon()
    create_card()
    create_rare_card()
    create_main_table()
    parser_to_sql()
