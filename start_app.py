from flask import Flask, render_template, request, redirect, url_for, make_response
import mysql.connector


app = Flask(__name__, static_folder="frontend/", template_folder="frontend")
db_config = {
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
            return make_response(f'<h2>Ошибка: {err}</h2>')
        except mysql.connector.errors.ProgrammingError as err:
            return make_response(f'<h2>Ошибка: {err}</h2>')

    def __exit__(self, exc_type, exc_value, exc_trace):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

        if exc_type is mysql.connector.errors.ProgrammingError:
            with open('log_error.txt', 'a') as txt_file:
                print(f'{exc_type}: {exc_value}', file=txt_file)
            return make_response('<h2>Неполадки с базой данных</h2>')


@app.errorhandler(404)
def error(err):
    return redirect(url_for('index'))


@app.route('/')
def index():
    return render_template(
        'index.html',
        the_title='Главная'
        )


@app.route('/add')
@app.route('/add/<int:addon>', methods=['GET', 'POST'])
def insert(addon=None):
    with OpenDatabase(db_config) as cursor:
        # get all addons
        sql = """
            SELECT addon_id, addon_name
            FROM addon;
            """
        cursor.execute(sql)
        # addon_id = [row[0] for row in cursor.fetchall()]
        addons = dict(cursor.fetchall())

        if not addon:
            return render_template(
                'add.html',
                the_addons=addons,
                the_title='Выбор аддона'
                )

        elif addon:
            if addon in addons:
                if request.method == 'POST':
                    pack = request.form.getlist('the_pack')

                    # get current pack number
                    sql = """
                        SELECT MAX(addon_pack_id)
                        FROM main_table
                        WHERE addon_id = %s;
                        """
                    cursor.execute(sql, (addon,))
                    pack_id = cursor.fetchone()[0] + 1

                    # insert values from html-form
                    for card_id, rare_id in enumerate(pack, 1):
                        # after refactor parser add condition for check empty string in a pack
                        sql = """
                            INSERT INTO main_table (
                                addon_id,
                                addon_pack_id,
                                rare_id,
                                card_id
                                )
                            VALUES (
                                %s,
                                %s,
                                %s,
                                %s
                                );
                            """
                        cursor.execute(sql, (
                            addon,
                            pack_id,
                            int(rare_id),
                            card_id
                            )
                        )

                    return render_template(
                        'add.html',
                        the_finish=True,
                        the_title='Данные добавлены'
                        )

                else:
                    # get rare_id: rare_name for html-form
                    sql = """
                        SELECT rare_id, rare_name
                        FROM rare;
                        """
                    cursor.execute(sql)
                    rare = dict(cursor.fetchall())

                    return render_template(
                        'add.html',
                        the_addon_id=addon,
                        the_addon_name=addons[addon],
                        the_rare=rare,
                        the_title='Добавление данных'
                        )
            else:
                return redirect(url_for('index'))


@app.route('/view')
@app.route('/view/data', methods=['POST'])
def view():
    with OpenDatabase(db_config) as cursor:
        if request.method == 'POST':
            selected_addon_id = int(request.form.get('the_addon'))
            rare = int(request.form.get('the_rare'))

            sql = """
                SELECT
                    m.addon_pack_id                             'Addon Pack Number',
                    a.addon_name                                'Addon Name',
                    GROUP_CONCAT(r.rare_name SEPARATOR ', ')    'Rare Type',
                    m.date                                      'Data' 
                FROM
                    addon                                       a
                INNER JOIN
                    main_table                                  m
                ON a.addon_id = m.addon_id
                INNER JOIN
                    rare								        r
                ON m.rare_id = r.rare_id
                WHERE a.addon_id =
                CASE
                    WHEN %s = 0
                        THEN a.addon_id
                    ELSE %s
                END
                AND r.rare_id =
                CASE
                    WHEN %s = 0
                        THEN r.rare_id
                    ELSE %s
                    END
                GROUP BY m.addon_pack_id, a.addon_name
                ORDER BY m.num_record;
                """
            cursor.execute(sql, (
                selected_addon_id,
                selected_addon_id,
                rare,
                rare)
            )
            data = ((addon_pack_id, addon_name, pack, date.strftime('%d.%m.%Y %H:%M:%S'))
                    for addon_pack_id, addon_name, pack, date in cursor.fetchall())

            return render_template(
                'view.html',
                the_data=data,
                the_title='Результаты запроса'
                )
        else:
            sql = """
                SELECT addon_id, addon_name
                FROM addon;
                """
            cursor.execute(sql)
            addon = dict(cursor.fetchall())

            sql = """
                SELECT rare_id, rare_name
                FROM rare;
                """
            cursor.execute(sql)
            rare = dict(cursor.fetchall())

            return render_template(
                'view.html',
                the_addon=addon,
                the_rare=rare,
                the_title='Запрос данных'
                )


if __name__ == '__main__':
    app.run(host='192.168.0.2', port='80', debug=True)
