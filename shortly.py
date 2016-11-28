# -*- coding: utf-8 -*-
import os
import redis
import urllib.parse
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.utils import redirect
from werkzeug.wsgi import DispatcherMiddleware
from functools import wraps
from jinja2 import Environment, FileSystemLoader
from jinja2 import utils
import db


def base36_encode(number):
    assert number >= 0, 'positive integer required'
    if number == 0:
        return '0'
    base36 = []
    while number != 0:
        number, i = divmod(number, 36)
        base36.append('0123456789abcdefghijklmnopqrstuvwxyz'[i])
    return ''.join(reversed(base36))


def is_valid_url(url):
    parts = urlparse.urlparse(url)
    return parts.scheme in ('http', 'https')


def get_hostname(url):
    return urlparse.urlparse(url).netloc

class SpaceShips(object):
    def __init__(self, config):
        self.redis = redis.Redis(config['redis_host'], config['redis_port'])
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                     autoescape=True)
        self.jinja_env.filters['hostname'] = get_hostname

        self.url_map = Map([
            Rule("/",endpoint="mainpage"),
            Rule("/send",endpoint="feedback")
        ])
        db.mysql_db.connect()
    def on_mainpage(self,request):
        error = None
        url = ''
        blocks = db.InfoBlock.select()
        page_info = db.PageInfo.select()
        return self.render_template('main.html', error=error, url=url,
                                    blocks=blocks, page_info=page_info)
    def valid_feedback(self,name,email,message):
        return True
    def db_feedback(self,name,email,message):
        new_user = db.Registered(name=name, email=email, message = message)
        new_user.save()
    def on_feedback(self,request):
        error = None
        url = ''
        if request.method == 'POST':
            name = str(utils.escape(request.form['name']))
            email = str(utils.escape(request.form['email']))
            message = str(utils.escape(request.form['message']))
            if not self.valid_feedback(name,email,message):
                error = 'Please enter a valid info'
            else:
                self.db_feedback(name,email,message)
                return redirect('/send')
        return self.render_template('success_1.html', error=error, url=url)
    def error_404(self):
        response = self.render_template('404.html')
        response.status_code = 404
        return response
    def render_template(self, template_name, **context):
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype='text/html')

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, 'on_' + endpoint)(request, **values)
        except NotFound as e:
            return self.error_404()
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

def create_app(redis_host='localhost', redis_port=6379, with_static=True):
    app = SpaceShips({
        'redis_host':       redis_host,
        'redis_port':       redis_port
    })
    if with_static:
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/static':  os.path.join(os.path.dirname(__file__), 'static')
        })
    return app

class SpaceShips_admin(object):

    def __init__(self, users, realm='login required'):
        self.users = users
        self.realm = realm
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                     autoescape=True)
        self.url_map = Map([
            Rule('/',endpoint='admin_page'),
            Rule('/update_users',endpoint = 'update_user_page'),
            Rule('/update_blocks',endpoint = 'update_blocks_page'),
            Rule('/update_pageinfo', endpoint = 'update_page_info')
        ])
    def check_auth(self, username, password):
        return username in self.users and self.users[username] == password

    def auth_required(self, request):
        return Response('Could not verify your access level for that URL.\n'
                        'You have to login with proper credentials', 401,
                        {'WWW-Authenticate': 'Basic realm="%s"' % self.realm})
    def valid_user_page(self,login,email,password,name):
        return True
    def valid_blocks_page(self,title,description,image):
        return True
    def valid_page_info(self,page_info):
        return True
    def error_404(self):
        response = self.render_template('404.html')
        response.status_code = 404
        return response

    def db_user_page(self,login,email,password,name):
        new_user = db.User(login=login, email=email, password=password, name=name)
        new_user.save()
    def db_blocks_page(self,title,description,image):
        new_info_block = db.InfoBlock(title=title, image=image, description=description)
        new_info_block.save()
    def db_page_info(self,start_date,menu_1,menu_2,menu_3,menu_4):
        new_page_info = db.PageInfo(start_date=start_date, menu_1=menu_1, menu_2=menu_2, menu_3=menu_3, menu_4=menu_4)
        new_page_info.save()
    def on_update_user_page(self,request):
        error = None
        url = ''
        if request.method == 'POST':
            login = str(utils.escape(request.form['login']))
            email = str(utils.escape(request.form['email']))
            password = str(utils.escape(request.form['password']))
            name = str(utils.escape(request.form['name']))
            if not self.valid_user_page(login,email,password,name):
                error = 'Please enter a valid info'
            else:
                self.db_user_page(login,email,password,name)
                return redirect('/admin/update_users')
        return self.render_template('success.html', error=error, url=url)
    def on_update_blocks_page(self,request):
        error = None
        url = ''
        if request.method == 'POST':
            title = str(utils.escape(request.form['block_title']))
            description = str(utils.escape(request.form['block_descr']))
            image = str(utils.escape(request.form['image_path']))
            if not self.valid_blocks_page(title,description,image):
                error = 'Please enter a valid info'
            else:
                self.db_blocks_page(title,description,image)
                return redirect('/admin/update_blocks')
        return self.render_template('success.html', error=error, url=url)
    def on_update_page_info(self,request):
        error = None
        url = url
        if request.method == 'POST':
            datetime = str(utils.escape(request.form['datetime']))
            menu_1 = str(utils.escape(request.form['menu_1']))
            menu_2 = str(utils.escape(request.form['menu_2']))
            menu_3 = str(utils.escape(request.form['menu_3']))
            menu_4 = str(utils.escape(request.form['menu_4']))
            if not self.valid_blocks_page(datemtime):
                error = 'Please enter a valid info'
            else:
                self.db_page_info(datemtime)
                return redirect('admin/update_pageinfo')
        return self.render_template('success.html', error=error, url=url)
    def on_admin_page(self,request):
        error = None
        url = ''
        blocks = db.InfoBlock.select()
        page_info = db.PageInfo.select()
        users = db.User.select()
        registered = db.Registered.select()
        return self.render_template('admin.html', error=error, url=url,
                                    blocks=blocks, page_info=page_info,
                                    users=users, registered=registered)

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, 'on_' + endpoint)(request, **values)
        except NotFound as e:
            return self.error_404()
        except HTTPException as e:
            return e
    def render_template(self, template_name, **context):
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype='text/html')

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        request = Request(environ)
        auth = request.authorization
        if not auth or not self.check_auth(auth.username, auth.password):
            response = self.auth_required(request)
        else:
            response = self.dispatch_request(request)
        return response(environ, start_response)

def create_app_admin(redis_host='localhost', redis_port=6379, with_static=True):
    db.mysql_db.connect()
    users = {}
    for user in db.User.select():
        users[user.login] = user.password
    app = SpaceShips_admin(users)
    if with_static:
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/static':  os.path.join(os.path.dirname(__file__), 'static')
        })
    return app
if __name__ == '__main__':
    from werkzeug.serving import run_simple
    app = create_app()
    db.mysql_db.connect()
    users = {}
    for user in db.User.select():
        users[user.login] = user.password
    application = create_app_admin()#SpaceShips_admin(users)
    app = DispatcherMiddleware(app, {
    '/admin':     application
    })
    run_simple('127.0.0.1', 5000, app, use_debugger=True, use_reloader=True)
