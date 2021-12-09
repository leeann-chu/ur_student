import enum
from flask import render_template, flash, redirect, request, url_for
from flask_login import login_user, logout_user, current_user, login_required
from utils.forms import LoginForm, RegistrationForm, TwoFactorForm, EditForm, CourseCreation, EditPassword, ResetPasswordForm
from utils.models import User, Student, Courses
from main import db, app
from random import randrange, choice
from datetime import datetime
from utils.emails import EmailClass

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home', color='blue', info="Home Page")

email = EmailClass()
slotTimes = {
    9:  '1',
    10: '2',
    11: '3',
    2:  '4',
    3:  '5',
    4:  '6',
    6:  '7',
    7:  '8'
}
@app.route("/login", methods=['GET', 'POST'])
def login(): #*
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    loginForm = LoginForm()
    if loginForm.validate_on_submit():
        user = User.query.filter_by(username=loginForm.username.data).first()
        if user is None:
            user = User.query.filter_by(email=loginForm.username.data).first()

        if user is None or not user.check_password(loginForm.password.data):
            flash('Invalid username or password', "alert-error")
            return redirect(url_for('login'))

        email.regenAuth()
        email.sendEmail(email.createVerifMsg(user.email))
        flash('Please check your email for your authentication code', "alert-success")
        return redirect(url_for('validate', uid=user.id))

    return render_template('login.html', title='Sign In', form=loginForm, color='blue', info='URStudent') ##

@app.route("/validate/<int:uid>", methods=['GET', 'POST'])
def validate(uid): #*
    user = User.query.filter_by(id=uid).first()
    form = TwoFactorForm()
    if form.validate_on_submit():
        if str(email.auth) == form.verification.data:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Verification code failed.", "alert-error")
    return render_template('validate.html', title='Verification', form=form, color='blue', uid=user.id) ##

@app.route("/profile/<int:uid>")
def profile(uid): #*
    student = Student.query.filter_by(userID=uid).first()
    # Error handling with empty entries
    if not student.dob:
        student.dob = "2001-01-01"
    age = datetime.now() - datetime.strptime(student.dob, '%Y-%m-%d')
    dt = datetime.strptime(student.dob, '%Y-%m-%d')

    if not student.pfp:
        with open("static/profile_images.txt", "r") as f:
            pfp_list = f.readlines()
        student.pfp = choice(pfp_list)

    return render_template('profile.html', uid=uid, title='Profile', name=student.fullName, id=student.studentID,
                           dob=f'{dt:%A}, {dt:%B} {dt.day}, {dt.year}', pfp=student.pfp, gradYear=student.gradYear, age=int(age.days/365),
                           color="purple", info=f"Personal Information for {student.fullName}" ) ##

@app.route("/edit/<newUser><int:uid>", methods=['GET', 'POST'])
def edit(uid, newUser): #*
    form = EditForm()
    student = Student.query.filter_by(userID=uid).first()
    if student.dob != None:
        newUser = "False"
        title = f'Edit Your {student.rel_user.userType} Profile'
        info = 'Edit Your Profile'
    else:
        title = f'Create Your {student.rel_user.userType} Profile'
        info = 'Create Your Profile'
    if request.method == 'GET':
        form.email.data = student.rel_user.email
        if newUser == "False":
            form.name.data = student.fullName
            if not student.dob:
                student.dob = "2001-01-01"
            form.dob.data = datetime.strptime(student.dob, '%Y-%m-%d')
            if student.rel_user.userType == "Student":
                form.gradYear.data = student.gradYear
            form.pfp.data = student.pfp

    if form.validate_on_submit():
        student.fullName = form.name.data
        student.dob = form.dob.data
        student.gradYear = form.gradYear.data
        student.pfp = form.pfp.data
        student.rel_user.email = form.email.data
        db.session.commit()
        if newUser == "True":
            return redirect(url_for("index"))
        return redirect(url_for("profile", uid=uid, edit=True))
    return render_template('edit.html', title=title, form=form,
                           uid=uid, newUser = newUser, userType = student.rel_user.userType, color='purple', info=info) ##

@app.route("/passedit/<int:uid>", methods=['GET', 'POST'])
def passedit(uid): #*
    form = EditPassword()
    if form.validate_on_submit():
        user = User.query.filter_by(id=uid).first()
        if user.check_password(form.oldPassword.data):
            user.set_password(form.newPassword.data)
            db.session.commit()
            email.sendEmail(email.confirmPassChange(user.email))
            return redirect(url_for('profile', uid=uid, edit=True))
        flash("Incorrect password", "alert-error")
    return render_template('passedit.html', title="Change Password", form=form, uid=uid, edit="Change", color='purple') ##

@app.route("/passemail/<edit>", methods=['GET', 'POST'])
def passemail(edit): #*
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if form.email.data:
            user = User.query.filter_by(email=form.email.data).first()
            if user is None:
                flash("Email unrecognized", "alert-error")
            else:
                email.sendEmail(email.resetPassword(form.email.data))
                return redirect(url_for('passemail', edit="Done"))
    return render_template('passedit.html', title="Reset Password", form=form, edit=edit, color='purple') ##

@app.route("/passreset/<edit>=<email>", methods=['GET', 'POST'])
def passreset(edit, email): #*
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if not form.email.data:
            user = User.query.filter_by(email=email).first()
            if user.check_password(form.password.data):
                flash("Password cannot be the same as old password!", "alert-error")
                return redirect(url_for('passreset', edit=edit, email=email))

            user.set_password(form.password.data)
            db.session.commit()
            flash("Password has been changed!", "alert-success")
            return redirect(url_for('login'))
    return render_template('passedit.html', title="Reset Password", form=form, edit=edit, color='purple') ##

@app.route('/courses/<view><int:uid>', methods=['GET', 'POST'])
def courses(uid, view): #*
    student = Student.query.filter_by(userID=uid).first()
    Course_List = Courses.query.all()
    try: #* Search Operation
        search = (request.form['searchInput']).lower()
        searchFields = []
        try:
            check = request.form["Professor"]
            searchFields.append('Professor')
        except: pass
        try:
            check = request.form['Title']
            searchFields.append('Title')
        except: pass
        try:
            check = request.form['Credits']
            searchFields.append('Credits')
        except: pass

        All_Courses = Courses.query.all()
        Course_List = []
        for Course in All_Courses:
            if 'Professor' in searchFields:
                if search in Course.profName.lower():
                    Course_List.append(Course)

            if 'Title' in searchFields:
                if search in Course.numTitle.lower():
                    Course_List.append(Course)

            if 'Credits' in searchFields:
                if search in str(Course.numCredits):
                    Course_List.append(Course)

            if not searchFields:
                if search in (Course.numTitle).lower() or search in (Course.profName).lower() or search in str(Course.numCredits):
                        Course_List.append(Course)
    except: pass  ##
    if view == "True":
        return render_template('courses.html', title='Course Selection', Course_List=Course_List, uid=uid, registered_courses=student.rel_courses, view=view, color='green', info="View Course Selection")
    
    try: #* Register for Classes 
        tempRegCourses = []
        print(request.form)
        for course in Course_List:
            try:
                check = request.form[str(course.courseID)]
                tempRegCourses.append(course)
            except: pass
            try:
                del_course = f"-{course.courseID}"
                check = request.form[del_course]
                db.session.delete(course)
                db.session.commit()
                return redirect(url_for('courses', uid=uid, view='True'))
            except: pass
        student.rel_courses = tempRegCourses
        db.session.commit()
    except: pass ##
    return render_template('courses.html', title='Course Selection', Course_List=Course_List, uid=uid, registered_courses=student.rel_courses, view='False', color='green', info="View Course Selection") ##

@app.route("/ccreation/<int:cid>", methods=['GET', 'POST'])
def ccreation(cid): #*
    form = CourseCreation()
    if request.method == 'GET' and cid != 0:
        course = Courses.query.filter_by(courseID=cid).first()
        form.numTitle.data = course.numTitle
        form.desc.data = course.desc
        form.profName.data = course.profName
        form.roomNum.data = course.roomNum
        form.numCredits.data = course.numCredits
        form.days.data = course.days
        form.time.data = course.time

    if form.validate_on_submit():
        if cid == 0:
            course = Courses(numTitle=form.numTitle.data, desc=form.desc.data,
                         profName=form.profName.data, numCredits=form.numCredits.data,
                         roomNum=form.roomNum.data, days=form.days.data, time=form.time.data)
            db.session.add(course)

            time = form.time.data.split(":")[0]
            course.slotNum = slotTimes.get(int(time), "invalid time")
            db.session.commit()
            return redirect(url_for('ccreation', edit=True, cid=0))
        else:
            course = Courses.query.filter_by(courseID=cid).first()
            course.numTitle = form.numTitle.data
            course.desc = form.desc.data
            course.profName = form.profName.data
            course.roomNum = form.roomNum.data
            course.numCredits = form.numCredits.data
            course.days = form.days.data
            course.time = form.time.data
    
            time = form.time.data.split(":")[0]
            course.slotNum = slotTimes.get(int(time), "invalid time")
            db.session.commit()
            return redirect(url_for('courses', view='True', uid=current_user.id))
    return render_template('ccreation.html', title='Course Creation', form=form, color='green', info="Course Creation") ##

class Event:
    def __init__(self, name, day1, day2, time, slotNum):
        self.name = name
        self.day1 = day1
        self.day2 = day2
        self.time = time
        self.slotNum = slotNum
        
@app.route("/schedule/<int:uid>")
def schedule(uid): #*
    student = Student.query.filter_by(userID=uid).first()
    eventList = []
    for course in student.rel_courses:
        event = Event(course.numTitle.split(":")[0], course.days[:1].lower(), course.days[-1].lower(), course.time, course.slotNum)
        eventList.append(event)
    print(eventList)
    return render_template('schedule.html', title='Schedule', uid=uid, color='darkred', eventList = eventList, info="Your Schedule") ##

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register(): #*
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, userType=form.userType.data)
        user.set_password(form.password.data)
        db.session.add(user)
        studentID = randrange(11111, 99999)
        while studentID in [student.studentID for student in Student.query.all()]:
            studentID = randrange(11111, 99999)
        student = Student(studentID=studentID, userID=user.id)
        db.session.add(student)
        user.rel_student.append(student)
        db.session.commit()
        flash(f'Congratulations, you\'re now a registered {user.userType}!', "alert-success")
        return redirect(url_for('edit', uid = user.id, newUser = "True"))
    return render_template('register.html', title='Register', form=form, color='blue') ##

@app.errorhandler(500)
@app.errorhandler(400)
@app.errorhandler(404)
@app.route('/error')
def not_found(error): #*
    with open("static/Waldo_Imgs.txt", "r") as f:
        Waldo_List = f.readlines()
    return render_template("error.html", error=error, Waldo = choice(Waldo_List)) ##
