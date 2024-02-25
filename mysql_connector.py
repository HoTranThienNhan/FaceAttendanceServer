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
def get_all_users(connection):
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
            return True
        except Exception as e:
            print(e)
            print("Cannot add new course")
    else:
        print("Course has already existed")
        return False
    
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
    try:
        query = ("insert into users (id, username, password, fullname, phone, address, email) values (%s, %s, %s, %s, %s, %s, %s)")
        cursor.execute(query, (id, username, hashed_pass, fullname, phone, address, email))
        query_user_role = ("insert into userrole (userid, roleid) values (%s, 'TC')")
        cursor.execute(query_user_role, (id))
        print("Add new teacher successfully")
        connection.commit()
        return True
    except Exception as e:
        print(e)
        print("Cannot add new teacher")
        return False
    
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
        return True
    except Exception as e:
        print(e)
        print("Cannot add new class")
    return False