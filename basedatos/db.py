from flask import Flask

app = Flask(__name__)


@app.route('/')
def index():
    return'hello word'


@app.route('/username')
def username():
    return 'username'


@app.route('/password')
def password():
    return 'password'

if __name__ == '__main__':
    app.run(port = 3000, debug=True)