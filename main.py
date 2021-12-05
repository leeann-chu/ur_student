from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from static.api_keys import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
Bootstrap(app)

from utils.models import User, Student, Courses
import utils.routes 
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Student' : Student, 'Courses' : Courses}
