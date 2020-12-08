import mysql.connector
import pandas as pd

# if __name__ == 'start_app':
#     from flask import render_template

file_xlsx = 'database_table.xlsx'
table_name = 'Packs'
with pd.ExcelFile(file_xlsx) as table:
    data_frame = table.parse(table_name)

db_config = {
    'host': 'localhost',
    'user': 'user_pc',
    'password': '1235',
    'database': 'hs_collection'
    }

rarities = (
    'common',
    'rare',
    'epic',
    'legendary',
    'gold common',
    'gold rare',
    'gold epic',
    'gold legendary'
    )


class OpenDatabase:
    def __init__(self, config: dict):
        self.configuration = config

    def __enter__(self):
        try:
            self.conn = mysql.connector.connect(**self.configuration)
            self.cursor = self.conn.cursor()
            return self.cursor
        except mysql.connector.errors.InterfaceError as err:
            if __name__ == '__main__':
                print(f'Ошибка: {err}')
            elif __name__ == 'start_app':
                return render_template('error.html')
        except mysql.connector.errors.ProgrammingError as err:
            if __name__ == '__main__':
                print(f'Ошибка: {err}')
            elif __name__ == 'start_app':
                return render_template('error.html')

    def __exit__(self, exc_type, exc_value, exc_trace):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

        if exc_type:
            with open('log_error.txt', 'a') as txt_file:
                print(f'{exc_type}: {exc_value}', file=txt_file)
                if __name__ == 'start_app':
                    return render_template(
                        'error.html',
                        the_message='Неполадки с базой данных'
                        )


# Old func. Delete it
def get_columns_name(dataframe):
    """
    Returns a dictionary of addons retrieved from the date_frame columns of the excel file
    :param dataframe: pandas dataframe
    :return: dictionary of addons
    """
    addons = {}
    x, y = 0, 1

    try:
        while dataframe.columns[x]:
            addons[y] = dataframe.columns[x]
            x += 2
            y += 1
    except IndexError:
        return addons


def get_addon_names(dataframe):
    """
    Returns a list of addons retrieved from the date_frame columns of the excel file
    :param dataframe: pandas dataframe
    :return: list of addons
    """

    """old version without generator
    addons = []
    for name in dataframe[0:0]:  # first string in a table
        if 'Unnamed' in name:
            continue

        addons.append(name)
    return addons, test
    """

    addons = [name for name in dataframe[0:0] if 'Unnamed' not in name]
    return addons


def create_database(config):
    """
    Creates a database
    :param config: dictionary with connection arguments for connector
    :return: nothing
    """
    new_config = config.copy()
    del new_config['database']
    with OpenDatabase(new_config) as cursor:
        sql = """
            DROP DATABASE IF EXISTS hs_collection;
            """
        cursor.execute(sql)

        sql = """
            CREATE DATABASE hs_collection;
            """
        cursor.execute(sql)


def create_table_addon(config):
    """
    Creates addons table
    :param config: dictionary with connection arguments for connector
    :return: nothing
    """
    with OpenDatabase(config) as cursor:
        addons = get_addon_names(data_frame)
        sql = """
            CREATE TABLE IF NOT EXISTS addon (
                addon_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                addon_name VARCHAR(50)
                );
            """
        cursor.execute(sql)

        for addon_names in addons:
            sql = f"""INSERT INTO addon (addon_name) VALUES (%s);"""
            cursor.execute(sql, (addon_names,))


def create_table_card(config):
    """
    Creates cards table
    :param config: dictionary with connection arguments for connector
    :return: nothing
    """
    card_number = (
        'first',
        'second',
        'third',
        'fourth',
        'fifth'
        )

    with OpenDatabase(config) as cursor:
        sql = """
            CREATE TABLE IF NOT EXISTS card (
                card_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                card_number VARCHAR(6)
                );
            """
        cursor.execute(sql)

        for position in card_number:
            sql = f"""INSERT INTO card (card_number) VALUES (%s);"""
            cursor.execute(sql, (position,))


def create_table_rare(config):
    """
    Creates tables of card rarity
    :param config: dictionary with connection arguments for connector
    :return: nothing
    """
    with OpenDatabase(config) as cursor:
        sql = """
            CREATE TABLE IF NOT EXISTS rare (
                rare_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                rare_name VARCHAR(14)
                );
            """
        cursor.execute(sql)

        for rare_name in rarities:
            sql = f"""INSERT INTO rare (rare_name) VALUES (%s);"""
            cursor.execute(sql, (rare_name,))


def create_main_table(config):
    """
    Creates a main table
    :param config: dictionary with connection arguments for connector
    :return: nothing
    """
    with OpenDatabase(config) as cursor:
        sql = """
            CREATE TABLE IF NOT EXISTS main_table (
                num_record INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                
                addon_id INT NOT NULL,
                CONSTRAINT addon_addon_id_fk
                FOREIGN KEY (addon_id)
                REFERENCES addon (addon_id) ON DELETE CASCADE,
                
                addon_pack_id INT NOT NULL,
                
                card_id INT NOT NULL,
                CONSTRAINT card_card_id_fk
                FOREIGN KEY (card_id)
                REFERENCES card (card_id) ON DELETE CASCADE,
                
                rare_id INT NOT NULL,
                CONSTRAINT rare_rare_id_fk
                FOREIGN KEY (rare_id)
                REFERENCES rare (rare_id) ON DELETE CASCADE,
                
                UNIQUE KEY unduplicated_record (addon_id, addon_pack_id, card_id),
                
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
        cursor.execute(sql)


def parser_to_sql(config):
    """
    Inserting values into the main table from an excel file
    :param config: dictionary with connection arguments for connector
    :return: nothing
    """
    insert_record = """
        INSERT INTO main_table (
            addon_id,
            card_id,
            rare_id,
            addon_pack_id
            )
        VALUES (
            %s,
            %s,
            %s,
            %s
            );
        """

    def insert_card(rare):
        """
        Inserts a card depending on its rarity
        :param rare: id of rarity, integer
        :return: nothing
        """
        cursor.execute(insert_record, (
            addon_id,
            card_id,
            rare,
            pack_id
            )
        )
        print(addon_id, pack_id, card_id, rarities[rare - 1], sep=': ')

    with OpenDatabase(config) as cursor:
        addon_id = 1
        for num, col in enumerate(data_frame.columns):
            if num % 2 != 0:
                for pack_id, value in enumerate(data_frame[data_frame.columns[num]], 1):
                    if isinstance(value, str):
                        pack = value.split(', ')
                        card_id = 1
                        other_card = 5 - len(pack)
                        for card in pack:
                            print(addon_id, pack_id, card_id, card, sep=': ')
                            rare_id = rarities.index(card) + 1
                            cursor.execute(insert_record, (
                                addon_id,
                                card_id,
                                rare_id,
                                pack_id
                                )
                            )
                            card_id += 1
                        if other_card:
                            for other_card_id in range(other_card):
                                insert_card(rare=1)
                                card_id += 1
                    else:
                        check = str(data_frame.iloc[pack_id - 1][data_frame.columns[num - 1]])
                        if 'nan' in check:
                            # if isinstance(dataframe.iloc[pack_id - 1][dataframe.columns[num - 1]], float):
                            break
                        else:
                            for card_id in range(1, 6):
                                if card_id == 1:
                                    insert_card(rare=2)
                                else:
                                    insert_card(rare=1)
                addon_id += 1


def start_pars(config):
    create_database(config)
    create_table_addon(config)
    create_table_card(config)
    create_table_rare(config)
    create_main_table(config)
    parser_to_sql(config)


# Test function. Delete it
def insert_data(addon_name: str, rare_name=()):
    with OpenDatabase(db_config) as cursor:
        sql = """
            SELECT MAX(addon_pack_id)
            FROM main_table
            WHERE addon_id = (SELECT addon_id FROM addon WHERE addon_name = %s)
            """
        cursor.execute(sql, (addon_name,))
        addon_pack_id = cursor.fetchone()[0] + 1
        if rare_name:
            for card, rare_name in enumerate(rare_name, 1):
                sql = """
                    INSERT INTO main_table (
                        addon_id,
                        card_id,
                        rare_id,
                        addon_pack_id
                        )
                    VALUES (
                        (SELECT addon_id FROM addon WHERE addon_name = %s),
                        %s,
                        (SELECT rare_id FROM rare WHERE rare_name = %s),
                        %s
                        );
                    """
                cursor.execute(sql, (
                    addon_name,
                    card,
                    rare_name,
                    addon_pack_id
                    )
                )
        else:
            sql = """
                INSERT INTO main_table (
                    addon_id,
                    card_id,
                    rare_id,
                    addon_pack_id
                    )
                VALUES (
                    (SELECT addon_id FROM addon WHERE addon_name = %s),
                    %s,
                    %s,
                    %s
                    );
                """
            cursor.execute(sql, (
                addon_name,
                6,
                9,
                addon_pack_id
                )
            )


# Test function. Delete it
def show_results():
    with OpenDatabase(db_config) as cursor:
        sql = """
            SELECT
                m.addon_pack_id         'Addon Pack Number',
                a.addon_name            'Addon Name',
                c.card_number           'Card Number',
                r.rare_name             'Rare Type',
                m.date                  'Data'
            FROM
                addon                   a
            INNER JOIN
                main_table              m
                ON a.addon_id = m.addon_id
            INNER JOIN
                card                    c
                ON m.card_id = c.card_id
            INNER JOIN
                rare                    r
                ON m.rare_id = r.rare_id
            ORDER BY m.num_record;
            """
        cursor.execute(sql)
