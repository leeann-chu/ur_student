from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from main import db, login

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120),  unique=True)
    phone = db.Column(db.String(12))
    userType = db.Column(db.String(7), nullable=False)
    verificationType = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(128))

    rel_student = db.relationship('Student', back_populates='rel_user', cascade="all, delete, delete-orphan", lazy=True)

    def __repr__(self):
        return f'<User {self.username}, id: {self.id}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    __tablename__ = 'student'

    studentID = db.Column(db.Integer, unique=True)
    userID = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    fullName = db.Column(db.String(64))
    dob = db.Column(db.String(10))
    gradYear = db.Column(db.String(4))
    pfp = db.Column(db.Text)

    rel_user = db.relationship('User', back_populates='rel_student')
    rel_courses = db.relationship('Courses', back_populates='rel_seats')

    def __repr__(self):
        return f'<Student {self.studentID}: {self.fullName}, Born: {self.dob}, Graduates: {self.gradYear}>'

class Courses(db.Model):
    __tablename__ = 'courses'

    courseID = db.Column(db.Integer, primary_key=True)
    studentID = db.Column(db.Integer, db.ForeignKey('student.studentID'))
    numTitle = db.Column(db.String(60), nullable=False, index=True, unique=True)
    desc = db.Column(db.Text)
    profName = db.Column(db.String)
    numCredits = db.Column(db.Integer, nullable=False)
    roomNum = db.Column(db.String(9))
    days = db.Column(db.String(3))
    time = db.Column(db.String(12))
    slotNum = db.Column(db.Integer)

    rel_seats = db.relationship('Student', back_populates='rel_courses')

    def __repr__(self):
        return f'<Course {self.courseID}, Title {self.numTitle}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
