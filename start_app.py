import traceback
from flask import Flask, redirect, render_template, request, url_for
from parser_data import db_config, OpenDatabase

app = Flask(__name__, static_folder="frontend/", template_folder="frontend")


def get_addons(cursor):
    """
    Returns a dictionary of addons retrieved from the database
    :param cursor: cursor for database
    :return: dictionary of addons
    """
    sql = """
        SELECT addon_id, addon_name
        FROM addon;
        """
    cursor.execute(sql)
    addons = dict(cursor.fetchall())
    return addons


def get_rarities(cursor):
    """
    Returns a dictionary of rarities retrieved from the database
    :param cursor: cursor for database
    :return: dictionary of rarities
    """
    sql = """
        SELECT rare_id, rare_name
        FROM rare;
        """
    cursor.execute(sql)
    rarities = dict(cursor.fetchall())
    return rarities


def log_error():
    """
    Saves error records to log_error file
    :return: nothing
    """
    err = traceback.format_exc()
    with open('log_error.txt', 'a') as txt_file:
        print(f'{err}', file=txt_file)


@app.errorhandler(404)
def error(err):
    return render_template('error.html')


@app.route('/')
def index():
    return render_template(
        'index.html',
        the_title='Главная'
        )


@app.route('/add')
@app.route('/add/<addon>', methods=['GET', 'POST'])
def insert(addon=None):
    try:
        with OpenDatabase(db_config) as cursor:

            # get all addons
            addons = get_addons(cursor)

            # choice addon
            if not addon:
                return render_template(
                    'add.html',
                    the_addons=addons,
                    the_title='Выбор аддона'
                    )

            elif addon:

                # insert data
                if addon != 'new':

                    # data input for a pack
                    addon = int(addon)
                    if addon in addons:

                        # adding to the database
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

                        # prepare to adding to the database
                        else:

                            # get rare_id: rare_name for html-form
                            rarities = get_rarities(cursor)

                            return render_template(
                                'add.html',
                                the_addon_id=addon,
                                the_addon_name=addons[addon],
                                the_rare=rarities,
                                the_title='Добавление данных'
                                )

                    # return to the home
                    else:
                        return redirect(url_for('index'))

                # add a new addon
                else:
                    if request.method == 'POST':
                        sql = """
                            SELECT MAX(addon_id)
                            FROM addon;
                            """
                        cursor.execute(sql)
                        addon_id = cursor.fetchone()[0] + 1

                        addon_name = request.form.get('the_addon_name')
                        sql = """
                            INSERT INTO addon (
                                addon_id,
                                addon_name
                                )
                            VALUES (
                                %s,
                                %s
                                );
                            """
                        cursor.execute(sql, (
                            addon_id,
                            addon_name
                            )
                        )

                        file = request.files.get('the_logo')
                        file.save('frontend/img/addons/%s.png' % addon_id)
                        """file.save(url_for('static', filename='img/addons/%s.png' % addon_id))  # why dont work?"""
                        return render_template('add.html',
                                               the_addon_added=addon_name,
                                               the_title='Аддон добавлен')
                    else:
                        return render_template('add.html',
                                               the_new_addon='new',
                                               the_title='Добавить аддон')
    except Exception:
        log_error()
        return render_template('error.html')


@app.route('/view')
@app.route('/view/data', methods=['POST'])
def view():
    try:
        with OpenDatabase(db_config) as cursor:

            # show the result table
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
                    rare
                    )
                )

                data = ((addon_pack_id, addon_name, pack, date.strftime('%d.%m.%Y %H:%M:%S'))
                        for addon_pack_id, addon_name, pack, date in cursor.fetchall())

                return render_template(
                    'view.html',
                    the_data=data,
                    the_title='Результаты запроса'
                    )

            # show the choice-result-form
            else:
                # get all addons
                addons = get_addons(cursor)

                # get all rarities
                rarities = get_rarities(cursor)

                return render_template(
                    'view.html',
                    the_addon=addons,
                    the_rare=rarities,
                    the_title='Запрос данных'
                    )
    except Exception:
        log_error()
        return render_template('error.html')


if __name__ == '__main__':
    app.run(host='192.168.0.2', port='80', debug=True)
