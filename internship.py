from flask import Flask, render_template, request, redirect, Response

import psycopg2
import psycopg2.extras
import datetime
import os
from functools import wraps
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import ssl


app = Flask(__name__)

connections_string = "postgresql://postgres:test@localhost/postgres"

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == os.environ["USERNAME"] and password == os.environ["PASSWORD"]

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/secret-page')
@requires_auth
def secret_page():
    return render_template('secret_page.html')

@app.route('/')
def hello_world():
    conn = psycopg2.connect(connections_string)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)


    cursor.execute('SELECT * FROM "temperature" ORDER BY reading_date DESC LIMIT 6')
    records = cursor.fetchall()

    cursor.execute('SELECT * FROM "temperature" ORDER BY temperature DESC limit 1')
    highest = cursor.fetchall()
    max = highest[0]

    cursor.execute('SELECT * FROM "temperature" ORDER BY temperature ASC limit 1')
    lowest = cursor.fetchall()
    min = lowest[0]
    # TODO read the highest temperature

    conn.commit()
    conn.close()

    return render_template('index.html', temperature=37, records=records, highest=max, lowest=min)




@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/me')
def me():
    return render_template('me.html', my_name='Magnus Esmann')

@app.route('/handle', methods=['POST'])
@requires_auth
def handle():
    temperature = request.form['temperature']
    current_date = datetime.date.today().isoformat()
    conn = psycopg2.connect(connections_string)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)


    query = "INSERT INTO temperature (temperature, reading_date) values (%s , '%s')" % (temperature, current_date)
    cursor.execute(query)

    conn.commit()
    conn.close()

    return redirect("/")

@app.route('/form')
@requires_auth
def form():
     return render_template('form.html')


@app.route('/led', methods=['POST'])
def led():
    url = "https://api.particle.io/v1/devices/%s/led?access_token=%s" % (os.environ['DEVICE_ID'], os.environ['ACCESS_TOKEN'])
    arg = request.form['arg']
    post_fields = {'arg': arg}
    gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    req = Request(url, urlencode(post_fields).encode())
    urlopen(req, context=gcontext)
    return arg

@app.route('/ledstate')
def ledstate():
    url = "https://api.particle.io/v1/devices/%s/ledstate?access_token=%s" % (os.environ['DEVICE_ID'], os.environ['ACCESS_TOKEN'])
    gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    return urlopen(url, context=gcontext).read()




if __name__ == '__main__':
    app.run()                                                           
