import mysql.connector
from flask import Flask
from flask_bcrypt import Bcrypt 

app = Flask(__name__)
bcrypt = Bcrypt(app) 

# Creating connection to MySQL
def create_server_connection(host_name, user_name, user_password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host = host_name,
            user =  user_name,
            password = user_password
        )
        print("MySQL Database connection successful")
    except:
        print("Error while attemping to connect to MySQL")
    return connection

# use face attendance database
def use_face_attendance_database(connection, database):
    cursor = connection.cursor()
    try:
        cursor.execute(f'use {database}')
        print("Using database successfully")
    except:
        print("Cannot use database")

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< USERS TABLE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# get username and password of all users
def fetch_all_users(connection):
    cursor = connection.cursor(dictionary=True)
    try:
        query = "select * from users"
        cursor.execute(query)
        print("Get all users successfully")
    except:
        print("Cannot get all users")
    return cursor.fetchall()

# get username and password of user admin
def get_user_admin(connection, username, password):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("""select users.* from users 
                 left join userrole on users.id = userrole.userid 
                 left join roles on userrole.roleid = roles.id 
                 where roles.id = 'AD' and username = %s and password = %s""")
        cursor.execute(query, (username, password))
        print("Get user successfully")
    except:
        print("Cannot get user")
    return cursor.fetchone()

# get username and password of user teacher
def get_user_teacher(connection, username, password):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("""select users.* from users 
                 left join userrole on users.id = userrole.userid 
                 left join roles on userrole.roleid = roles.id 
                 where roles.id = 'TC' and username = %s and password = %s""")
        cursor.execute(query, (username, password))
        print("Get user successfully")
    except:
        print("Cannot get user")
    return cursor.fetchone()


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< STUDENTS TABLE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# add new student
def add_new_student(connection, id, fullname, phone, address, email):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("insert into students (id, fullname, phone, address, email) values (%s, %s, %s, %s, %s)")
        cursor.execute(query, (id, fullname, phone, address, email))
        print("Add new student successfully")
        connection.commit()
    except Exception as e:
        print(e)
        print("Cannot add new student")

# get all students
def fetch_all_students(connection):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("select * from students")
        cursor.execute(query)
        print("Get all students successfully")
    except:
        print("Cannot get all students")
    return cursor.fetchall()

# get available students
def fetch_available_students(connection, teacher_id, course_id):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("""select id, fullname from students where id not in
                    (select studentid from studentgroups sg where sg.classid in (
                        select c.id
                            from classes c, users u, courses cs 
                            where c.teacherid = u.id 
                            and c.courseid = cs.id
                            and c.teacherid = %s
                            and c.courseid = %s 
                            order by c.id asc))""")
        cursor.execute(query, (teacher_id, course_id))
        print("Get available students successfully")
    except:
        print("Cannot get available students")
    return cursor.fetchall()

def update_the_student(connection, id, fullname, phone, address, email):
    cursor = connection.cursor(dictionary=True)
    existed_student = check_student_existed(connection=connection, id=id)
    # if student has already existed
    if existed_student != None:
        try:
            query = ("update students set id = %s, fullname = %s, phone = %s, address = %s, email = %s where id = %s")
            cursor.execute(query, (id, fullname, phone, address, email, id))
            connection.commit()
            print("Update student successfully")
            return True
        except Exception as e:
            print(e)
            print("Cannot update student")
    else:
        print("Student has not existed yet")
        return False

    
# check if student existed
def check_student_existed(connection, id):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("select * from students where id = %s")
        cursor.execute(query, (id,))
        return cursor.fetchone()
    except Exception as e: 
        print(e)
        print("Cannot check student")


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< COURSES TABLE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# add new course
def add_new_course(connection, id, name, description, active):
    cursor = connection.cursor(dictionary=True)
    existed_course = check_course_existed(connection=connection, id=id)
    # if course did not exist yet
    if existed_course == None:
        try:
            query = ("insert into courses (id, name, description, active) values (%s, %s, %s, %s)")
            cursor.execute(query, (id, name, description, active))
            connection.commit()
            print("Add new course successfully")
            message = "Add new course successfully"
            return True, message
        except Exception as e:
            print(e)
            print("Cannot add new course")
    else:
        message = "Course '" + id + "' has already existed."
        print("Course has already existed")
        return False, message
    
# update course
def update_the_course(connection, id, name, description):
    cursor = connection.cursor(dictionary=True)
    existed_course = check_course_existed(connection=connection, id=id)
    # if course has already existed
    if existed_course != None:
        try:
            query = ("update courses set id = %s, name = %s, description = %s where id = %s")
            cursor.execute(query, (id, name, description, id))
            connection.commit()
            print("Update course successfully")
            return True
        except Exception as e:
            print(e)
            print("Cannot update course")
    else:
        print("Course has not existed yet")
        return False
    
# update status course
def update_the_status_course(connection, id, active):
    cursor = connection.cursor(dictionary=True)
    existed_course = check_course_existed(connection=connection, id=id)
    # if course has already existed
    if existed_course != None:
        try:
            query = ("update courses set id = %s, active = %s where id = %s")
            cursor.execute(query, (id, active, id))
            connection.commit()
            print("Update status course successfully")
            return True
        except Exception as e:
            print(e)
            print("Cannot update status course")
    else:
        print("Course has not existed yet")
        return False

# check if course existed
def check_course_existed(connection, id):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("select * from courses where id = %s")
        cursor.execute(query, (id,))
        return cursor.fetchone()
    except Exception as e: 
        print(e)
        print("Cannot check course")

# get all courses
def fetch_all_courses(connection):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("select * from courses")
        cursor.execute(query)
        print("Get all courses successfully")
    except:
        print("Cannot get all courses")
    return cursor.fetchall()

# get all active courses
def fetch_all_active_courses(connection):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("select * from courses where active = 1")
        cursor.execute(query)
        print("Get all active courses successfully")
    except:
        print("Cannot get all active courses")
    return cursor.fetchall()


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< TEACHERS TABLE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# get all teachers
def fetch_all_teachers(connection):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("""select users.* from users 
                 left join userrole on users.id = userrole.userid 
                 left join roles on userrole.roleid = roles.id 
                 where roles.id = 'TC'""")
        cursor.execute(query)
        print("Get all teachers successfully")
    except Exception as e:
        print(e)
        print("Cannot get all teachers")
    return cursor.fetchall()

# get teacher by id
def fetch_teacher_by_id(connection, id):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("""select * from users where users.id = %s""")
        cursor.execute(query, (id,))
        print("Get teacher by id successfully")
    except Exception as e:
        print(e)
        print("Cannot get teacher by id")
    return cursor.fetchone()

# add new teacher
def add_new_teacher(connection, request_data):
    cursor = connection.cursor(dictionary=True)
    id = request_data['id']
    fullname = request_data['fullname']
    phone = request_data['phone']
    address = request_data['address']
    email = request_data['email']
    username = request_data['username']
    password = request_data['password']
    hashed_pass = bcrypt.generate_password_hash(password).decode('utf-8')

    existed_teacher = fetch_teacher_by_id(connection=connection, id=id)
    if existed_teacher == None:
        try:
            query = ("insert into users (id, username, password, fullname, phone, address, email) values (%s, %s, %s, %s, %s, %s, %s)")
            cursor.execute(query, (id, username, hashed_pass, fullname, phone, address, email))
            query_user_role = ("insert into userrole (userid, roleid) values (%s, 'TC')")
            cursor.execute(query_user_role, (id))
            message = "Add new teacher successfully"
            print("Add new teacher successfully")
            connection.commit()
            return True, message
        except Exception as e:
            print(e)
            message = "Cannot add new teacher"
            print("Cannot add new teacher")
            return False, message
    else:
        message = "Teacher '" + id + "' has already existed."
        print("Teacher has already existed")
        return False, message
    
# update the teacher
def update_the_teacher(connection, request_data):
    cursor = connection.cursor(dictionary=True)
    id = request_data['id']
    fullname = request_data['fullname']
    phone = request_data['phone']
    address = request_data['address']
    email = request_data['email']
    username = request_data['username']
    try:
        query_user_role = ("update userrole set userid = %s where userid = %s")
        cursor.execute(query_user_role, (id, id))
        query = ("update users set id = %s, fullname = %s, phone = %s, address = %s, email = %s, username = %s where id = %s")
        cursor.execute(query, (id, fullname, phone, address, email, username, id))
        print("Update teacher successfully")
        connection.commit()
        return True
    except Exception as e:
        print(e)
        print("Cannot add new teacher")
        return False


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CLASSES TABLE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_new_class(connection, request_data):
    class_id = request_data['id']
    year = request_data['year']
    semester = request_data['semester']
    teacher_id = request_data['teacher']
    course_id = request_data['course']
    students = request_data['students']
    times = request_data['time']
    cursor = connection.cursor(dictionary=True)

    # check if class existed
    existed_class = fetch_class_by_class_id(connection=connection, class_id=class_id)
    if (existed_class != None):
        print("Class ID has already created")
        return False, "Class ID '" + class_id + "' has already created."
    else:
        try:
            # insert class table
            query_class = ("insert into classes (id, year, semester, teacherid, courseid) values (%s, %s, %s, %s, %s)")
            cursor.execute(query_class, (class_id, year, semester, teacher_id, course_id))
            print("Add class information successfully")
            # insert student groups table
            for student_id in students:
                query_student_groups = ("insert into studentgroups (classid, studentid) values (%s, %s)")
                cursor.execute(query_student_groups, (class_id, student_id))
            print("Add student groups successfully")
            # insert classtime table
            for each_day in times:
                if each_day['timeIn'] != '' and each_day['timeOut'] != '':  # only insert day that has time in and time out
                    query_class_time = ("insert into classtime (classid, day, timein, timeout) values (%s, %s, %s, %s)")
                    cursor.execute(query_class_time, (class_id, each_day['day'], each_day['timeIn'], each_day['timeOut']))
            print("Add class time successfully")
            connection.commit()
            return True, "Create new class sunccessfully"
        except Exception as e:
            print(e)
            print("Cannot add new class")
        return False, "Cannot add new class"

# get all classes 
def fetch_all_classes(connection):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("""select c.*, u.fullname as teachername, cs.name as coursename 
                 from classes c, users u, courses cs 
                 where c.teacherid = u.id 
                 and c.courseid = cs.id
                 order by c.id asc""")
        cursor.execute(query)
        print("Get all classes successfully")
    except:
        print("Cannot get all classes")
    return cursor.fetchall()

# get class by class id
def fetch_class_by_class_id(connection, class_id):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("""select * from classes where id = %s""")
        cursor.execute(query, (class_id,))
        print("Get class by class id successfully")
    except:
        print("Cannot get class by class id")
    return cursor.fetchone()

# get all classes by teacher
def fetch_all_classes_by_teacher_today(connection, teacher_id, day):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("""select classes.*, courses.name, classtime.timein, classtime.timeout from classes 
                 left join courses on classes.courseid = courses.id
                 left join classtime on classes.id = classtime.classid
                 where teacherid = %s
                 and classtime.day = %s""")
        cursor.execute(query, (teacher_id, day,))
        print("Get all classes by teacher successfully")
    except:
        print("Cannot get all classes by teacher")
    return cursor.fetchall()

# get all classes by teacher and class id
def fetch_class_by_teacher_and_class_id(connection, teacher_id, day, class_id):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("""select classes.*, courses.name, classtime.timein, classtime.timeout from classes 
                 left join courses on classes.courseid = courses.id
                 left join classtime on classes.id = classtime.classid
                 where teacherid = %s
                 and classtime.day = %s
                 and classes.id = %s""")
        cursor.execute(query, (teacher_id, day, class_id,))
        print("Get class by teacher and class id successfully")
    except:
        print("Cannot get class by teacher and class id")
    return cursor.fetchone()

# get all classes by year and semester and teacher id
def fetch_all_classes_by_year_semester_teacher(connection, year, semester, teacher_id):
    cursor = connection.cursor(dictionary=True)
    
    try:
        query = ("select * from classes where year = %s and semester = %s and teacherid = %s")
        cursor.execute(query, (year, semester, teacher_id,))
        print("Get all classes by year and semester and teacher id successfully")
    except:
        print("Cannot get all classes by year and semester and teacher id")
    return cursor.fetchall()

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< STUDENT GROUPS TABLE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# get all students by class
def fetch_all_students_by_class(connection, class_id):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("select * from studentgroups left join students on studentgroups.studentid = students.id where classid = %s")
        cursor.execute(query, (class_id,))
        print("Get all students by class successfully")
    except:
        print("Cannot get all students by class")
    return cursor.fetchall()


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< TIMESHEET TABLE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# create timesheet of today
def create_class_timesheet_of_today(connection, class_id, day, date):
    cursor = connection.cursor(dictionary=True)
    try:
        all_students_by_class = fetch_all_students_by_class(connection, class_id)
        for student in all_students_by_class:
            student_id = student['studentid']
            query = ("insert into timesheet (classid, studentid, day, date) values (%s, %s, %s, %s)")
            cursor.execute(query, (class_id, student_id, day, date))
        print("Create today class timesheet successfully")
        connection.commit()
        return True
    except Exception as e:
        print(e)
        print("Cannot create today class timesheet")
        return False

# add in timesheet
def add_in_timesheet(connection, class_id, student_id, date, time_in, late):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("""update timesheet set timein = %s, late = %s where classid = %s and studentid = %s and date = %s""")
        cursor.execute(query, (time_in, late, class_id, student_id, date))
        print("Add new in timesheet successfully")
        connection.commit()
        return True
    except Exception as e:
        print(e)
        print("Cannot add new in timesheet")
        return False
    
# add out timesheet
def add_out_timesheet(connection, class_id, student_id, date, time_out, soon):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("""update timesheet set timeout = %s, soon = %s where classid = %s and studentid = %s and date = %s""")
        cursor.execute(query, (time_out, soon, class_id, student_id, date))
        print("Add new out timesheet successfully")
        connection.commit()
        return True
    except Exception as e:
        print(e)
        print("Cannot add new out timesheet")
        return False

#
def is_in_attendance_taken(connection, class_id, date):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("select * from timesheet where classid = %s and date = %s and timein is not null")
        cursor.execute(query, (class_id, date))
        print("Check if in attendance taken successfully")
    except:
        print("Cannot check if in attendance taken")
    return cursor.fetchall()

#
def is_out_attendance_taken(connection, class_id, date):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("select * from timesheet where classid = %s and date = %s and timeout is not null")
        cursor.execute(query, (class_id, date))
        print("Check if out attendance taken successfully")
    except:
        print("Cannot check if out attendance taken")
    return cursor.fetchall()

#
def fetch_full_attendance(connection, class_id, date):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("""select * from timesheet left join students on timesheet.studentid = students.id 
                 where classid = %s and date = %s""")
        cursor.execute(query, (class_id, date))
        print("Get full attendance successfully")
    except:
        print("Cannot get full attendance")
    return cursor.fetchall()

def fetch_full_attendance_by_student_id(connection, class_id, student_id):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("""select t.classid, studentid, t.day, t.date, t.timein, t.timeout, late, soon, 
                 fullname, c.timein as stdtimein, c.timeout as stdtimeout from timesheet t
                 left join students s on t.studentid = s.id 
                 left join classtime c on t.classid = c.classid and t.day = c.day 
                 where t.classid = %s and studentid = %s""")
        cursor.execute(query, (class_id, student_id))
        print("Get full attendance by student id successfully")
    except:
        print("Cannot get full attendance by student id")
    return cursor.fetchall()


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CLASSTIME TABLE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
def fetch_all_class_time(connection):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("select * from classtime")
        cursor.execute(query)
        print("Get all class time successfully")
    except:
        print("Cannot get all class time")
    return cursor.fetchall()

#
def fetch_class_time_by_class_id(connection, class_id):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("select * from classtime where classid = %s")
        cursor.execute(query, (class_id,))
        print("Get class time by class id successfully")
    except:
        print("Cannot get class time by class id")
    return cursor.fetchall()

#
def fetch_time_in_and_out_by_teacher_id_and_day(connection, teacher_id, day):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("select * from classes c, classtime ct where c.id = ct.classid and c.teacherid = %s and ct.day = %s")
        cursor.execute(query, (teacher_id, day))
        print("Get time in and out by teacher id and day successfully")
    except:
        print("Cannot get time in and out by teacher id and day")
    return cursor.fetchall()

#
def fetch_standard_in_out_attendance(connection, class_id, day):
    cursor = connection.cursor(dictionary=True)
    try:
        query = ("select * from classtime where classid = %s and day = %s")
        cursor.execute(query, (class_id, day))
        print("Get standard time in/out successfully")
    except:
        print("Cannot get standard time in/out")
    return cursor.fetchone()