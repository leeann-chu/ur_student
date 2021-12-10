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

@app.route("/courses/<int:uid>", methods=['GET', 'POST'])
def courses(uid): #*

    student = Student.query.filter_by(userID=uid).first()
    Registered = [int(course.courseID) for course in student.rel_courses]

    try:
        Course_ID = int(request.form['Delete'])
        course = Courses.query.filter_by(courseID=Course_ID).first()
        db.session.delete(course)
        db.session.commit()
    
    except: pass

    try:
        Num = int(request.form['LoopCounter'])

    except: pass

    try:  # Hey, Im almost positive we never need to have course_ids as str. Change it up in Registereed too so everything agrees
        # actually no, I dont think we need registered anymore do we? control f and see.
        # hmm, but can we make it so we only have to commit once?
        Num = int(request.form['LoopCounter'])
        #print(Registered)
        print("student.rel_courses", student.rel_courses)
        COURSE = []
        for i in range(Num):
            COURSEID = int(request.form[str(i + 1)])
            print(COURSEID)
            COURSE.append(COURSEID)
        COURSE.sort()
        print('sorted', COURSE)
        for i in COURSE:  ## change registered to ints
            if i < 0:
                x = i * -1
                print('to be removed', x)
                cor = Courses.query.filter_by(courseID=x).first()
                if cor in student.rel_courses:
                    #Registered.remove(x)
                    #Course = Courses.query.filter_by(courseID=x).first()
                    student.rel_courses.remove(cor)
                    db.session.commit()
                    print('rel_courses deleted', student.rel_courses)
                else: pass
            else:
                cor = Courses.query.filter_by(courseID=i).first()
                if cor not in student.rel_courses:
                    Days = [(str(course.days), str(course.time)) for course in student.rel_courses]
                    #Course = Courses.query.filter_by(courseID=x).first()
                    Day = (str(cor.days), str(cor.time))

                    if Day in Days:
                        Index = Days.index(Day)
                        Conflict = student.rel_courses[Index].numTitle
                        message = Markup("<h2>Unable to register for {0}. Conflict detected with {1}.</h2>".format(cor.numTitle, Conflict))
                        flash(message)

                    else:
                        #Registered.append(x)
                        #Course = Courses.query.filter_by(courseID=x).first() ###
                        student.rel_courses.append(cor) ###
                        db.session.commit() ###
                else: pass
    except: pass


                # remove it. Figure out tomorrow. I need a shower. 


    '''try:
        for i in range(Num):
            try:
                COURSE_ID = request.form[str(i + 1)]

                if int(COURSE_ID) < 0:
                    COURSE_ID = COURSE_ID.replace('-', '')

                    if COURSE_ID in Registered:
                        Registered.remove(COURSE_ID)
                        Course = Courses.query.filter_by(courseID=int(COURSE_ID)).first() ###
                        student.rel_courses.remove(Course) ###
                        db.session.commit() ###

                    else: pass

                else:
                    if COURSE_ID not in Registered:
                        Days = [(str(course.days), str(course.time)) for course in student.rel_courses]
                        Course = Courses.query.filter_by(courseID=COURSE_ID).first()
                        Day = (str(Course.days), str(Course.time))

                        if Day in Days:
                            Index = Days.index(Day)
                            Conflict = student.rel_courses[Index].numTitle
                            message = Markup("<h2>Unable to register for {0}. Conflict detected with {1}.</h2>".format(Course.numTitle, Conflict))
                            flash(message)

                        else:
                            Registered.append(COURSE_ID)
                            Course = Courses.query.filter_by(courseID=int(COURSE_ID)).first() ###
                            student.rel_courses.append(Course) ###
                            db.session.commit() ###

                    else: pass

            except: pass
    except: pass'''

    '''REGISTERED_COURSES = []
    for i in Registered:
        Course = Courses.query.filter_by(courseID=int(i)).first()
        REGISTERED_COURSES.append(Course)

    student.rel_courses = REGISTERED_COURSES
    db.session.commit()'''

    #except: pass

    try:
        Search = (request.form['SearchButton']).lower()
        Search_Fields = []
    
    except:
        Search_Fields = None

    try:
        check_ = request.form["Professor"]
        Search_Fields.append('Professor')
    
    except: pass
    
    try:
        check_ = request.form['Title']
        Search_Fields.append('Title')
    
    except: pass

    try:
        check_ = request.form['Credits']
        Search_Fields.append('Credits')

    except: pass
    
    All_Courses = Courses.query.all()
    if Search_Fields == None:
        Course_List = All_Courses

    else:
        Course_List = []
        for Course in All_Courses:
            if 'Professor' in Search_Fields:
                if Search in (Course.profName).lower():
                    Course_List.append(Course)

            if 'Title' in Search_Fields:
                if Search in (Course.numTitle).lower():
                    Course_List.append(Course)
            
            if 'Credits' in Search_Fields:
                if Search in str(Course.numCredits):
                    Course_List.append(Course)
            
            if Search_Fields == []:
                if Search in (Course.numTitle).lower() or Search in (Course.profName).lower() or Search in str(Course.numCredits):
                    Course_List.append(Course)

    To_Shade = [str(course.courseID) for course in student.rel_courses]
    return render_template('courses.html', title='Course Selection', To_Shade=To_Shade, Course_List=Course_List, Registered=Registered, uid=uid, student=student, color='green', info="Course Selection") ##

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
    def __init__(self, cid, name, day1, day2, time, slotNum):
        self.cid = cid
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
        event = Event(course.courseID, course.numTitle.split(":")[0], course.days[:1].lower(), course.days[-1].lower(), course.time, course.slotNum)
        eventList.append(event)
    return render_template('schedule.html', title='Schedule', uid=uid, color='darkred', eventList = eventList, info="Your Schedule") ##

@app.route("/schedule/vcourse.html/<int:cid>")
def vcourse(cid):
    course = Courses.query.filter_by(courseID=cid).first()
    print(course)
    return render_template('vcourse.html', cid=cid, Course=course, title=course.numTitle, color='green', info=course.numTitle)

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
