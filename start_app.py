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
@app.route('/add/<addon>', methods=['GET', 'POST'])
def insert(addon=None):
    with OpenDatabase(db_config) as cursor:
        # get all addons
        sql = """
            SELECT addon_id
            FROM addon;
            """
        cursor.execute(sql)
        addon_id = [row[0] for row in cursor.fetchall()]

        if not addon:
            return render_template(
                'add.html',
                the_addons=addon_id,
                the_title='Выбор аддона'
                )

        elif addon:
            if int(addon) in addon_id:
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

                    """after refactor parser replace dict rare with this code:
                    rare = {0: ''}
                    data = dict(cursor.fetchall())
                    rare.update(data)
                    rare.fromkeys(data)
                    rare.pop(9)
                    """

                    return render_template(
                        'add.html',
                        the_addon_id=addon,
                        the_rare=rare,
                        the_title='Добавление данных'
                        )
            else:
                return redirect(url_for('index'))


@app.route('/view')
def view():
    pass


if __name__ == '__main__':
    app.run(host='192.168.0.2', port='80', debug=True)
