from flask import Flask, render_template, request, session, redirect, url_for, make_response

app = Flask(__name__, static_folder="frontend/", template_folder="frontend")

@app.route('/')
def enter_page():
    return render_template('index.html')

@app.route('/add')
def add():
    return render_template('add.html')

if __name__ == '__main__':
    app.run(host='192.168.0.2', port='80', debug=True)