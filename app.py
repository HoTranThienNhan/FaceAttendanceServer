from flask import Flask, jsonify, request, Response, abort, json, stream_with_context
from flask_bcrypt import Bcrypt 
import mysql.connector
import cv2
from PIL import Image
import numpy as np
import os
import sys
import shutil
from flask_cors import CORS
from mysql_connector import *
from utils import *
import base64
import time
import pickle
import src.face_recognition as face_recog
 
app = Flask(__name__)
CORS(app, origins='http://localhost:3000')
CORS(app, origins='http://localhost:3001')
bcrypt = Bcrypt(app) 


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< MYSQL DATABASE CONNECTION >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
connection = create_server_connection("localhost", "root", "root")
use_face_attendance_database(connection, "face_attendance")
cursor = connection.cursor(dictionary=True)


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< IMAGES ALIGNMENT >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def align_images(class_name):
    import src.align_dataset_mtcnn as mtcnn
    from src.align_dataset_mtcnn import parse_arguments
    mtcnn.main(parse_arguments([
        'Dataset/raw',      # input directory
        class_name,     # input class directory name
        'Dataset/processed',    # output directory
        '--image_size', '160',      # aligned image size
        '--margin', '32',   # margin bounding box
        '--random_order',   # shuffling the order of aligned images
        '--gpu_memory_fraction', '0.25'     # the amount of gpu memory
    ]))
    


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< GENERATE IMAGES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def generate_images(id, fullname, phone, address, email, gender):
    wCam, hCam = 500, 400
 
    cap = cv2.VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4, hCam)
    i = 0
    step = 0
    print(id)
    while (True):
        ret, frame = cap.read() 
        if step % 2 == 1:
            cv2.putText(frame, str(i), (60, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_4)
            cv2.imshow('frame', frame)

            buffer = cv2.imencode('.jpg', frame)[1].tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')

            cv2.imwrite(f'Dataset/raw/{id}/'+str(i)+'.png', frame) 

            i += 1
        step += 1
        if cv2.waitKey(1) & 0xFF == ord('q') or i == 30: 
            break

    # release video capture
    cap.release()
    cv2.destroyAllWindows()

    # add new student to database       
    add_new_student(connection=connection, id=id, fullname=fullname, phone=phone, address=address, email=email, gender=gender)


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< APP ROUTES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< VIDEO FRAMES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/video_feed')
def open_video():
    id = request.args['id']
    fullname = request.args['fullname']
    phone = request.args['phone']
    address = request.args['address']
    email = request.args['email']
    gender = request.args['gender']
    # Video streaming route. Put this in the src attribute of an img tag
    return Response(
        generate_images(id=id, fullname=fullname, phone=phone, address=address, email=email, gender=gender),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< SIGN IN >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/signin_admin', methods = ['POST'])
def sign_in_admin():
    username = request.args.get('username', None)
    password = request.args.get('password', None)

    this_user = get_user_admin(connection, username=username, password=password)

    if this_user != None:
        response = jsonify(this_user)
        return response
    else:
        abort(404)

@app.route('/signin_teacher', methods = ['POST'])
def sign_in_teacher():
    username = request.args.get('username', None)
    password = request.args.get('password', None)

    this_user = get_user_teacher(connection, username=username, password=password)

    if this_user != None:
        response = jsonify(this_user)
        return response
    else:
        abort(404)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< ADD NEW STUDENT >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/add_new', methods = ['POST'])
def add_new():
    studentId = request.args.get('studentId', None)
    # check if Dataset/raw has at least a subdirectory
    hasSubdirectory = False
    for root, directories, files in os.walk('Dataset/raw'):
        if (directories):
            # align images
            align_images(studentId)
            hasSubdirectory = True
    # classifying aligned face folder from MTCNN steps
    # import src.face_recognition as face_recog
    import src.classifier as clf
    from src.classifier import parse_arguments
    clf.main(parse_arguments([
        'TRAIN',      # mode ['TRAIN', 'CLASSIFY']
        'Dataset/processed',     # aligned face folder
        'Models/20180402-114759.pb',    # model
        'Models/facemodel.pkl',      # pickle file (classifier_filename)
        '--batch_size', '1000'   # number of images to process in a batch
    ]))
    # global sess, MINSIZE, IMAGE_SIZE, INPUT_IMAGE_SIZE, pnet, rnet, onet, THRESHOLD, FACTOR, model, class_names, images_placeholder, phase_train_placeholder, embeddings, embedding_size, people_detected, person_detected 
    # sess, MINSIZE, IMAGE_SIZE, INPUT_IMAGE_SIZE, pnet, rnet, onet, THRESHOLD, FACTOR, model, class_names, images_placeholder, phase_train_placeholder, embeddings, embedding_size, people_detected, person_detected = face_recog.Face_Rec().main()
    global model, class_names 
    CLASSIFIER_PATH = 'Models/facemodel.pkl'
    with open(CLASSIFIER_PATH, 'rb') as file:
        model, class_names = pickle.load(file)
        
    if hasSubdirectory == False:
        abort(404)
    return '', 200

@app.route('/readd', methods = ['POST'])
def readd():
    studentId = request.args.get('studentId', None)
    # check if Dataset/raw has at least a subdirectory
    hasSubdirectory = False
    for root, directories, files in os.walk('Dataset/raw'):
        if (directories):
            # remove old class folder in processed
            processed_directory = 'Dataset/processed'
            path = os.path.join(processed_directory, studentId)
            shutil.rmtree(path)
            # align images
            align_images(studentId)
            hasSubdirectory = True
    if hasSubdirectory == False:
        abort(404)
    return '', 200


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< SCAN >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/create_scan', methods = ['POST'])
def create_directory_for_new_user():
    newuser = request.args.get('newuser', None).upper()
    raw_directory = 'Dataset/raw'
    path = os.path.join(raw_directory, newuser)
    try:
        os.mkdir(path) 
    except FileExistsError:
        message = "Student ID '" + newuser + "' has been already scanned."
        pass
        return jsonify(message=message), 404
    return '', 200

@app.route('/refresh_scan', methods = ['POST'])
def remove_directory_of_new_user():
    newuser = request.args.get('newuser', None)
    raw_directory = 'Dataset/raw'
    path = os.path.join(raw_directory, newuser)
    try:
        shutil.rmtree(path)
    except FileExistsError:
        pass
        abort(404)
    return '', 200

@app.route('/rescan', methods = ['POST'])
def rescan_for_this_user():
    studentId = request.args.get('studentId', None)
    raw_directory = 'Dataset/raw'
    path = os.path.join(raw_directory, studentId)
    try:
        shutil.rmtree(path)
        os.mkdir(path) 
    except FileExistsError:
        pass
        abort(404)
    return '', 200


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< USERS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/get_all_users', methods = ['GET'])
def get_all_users():
    all_users = fetch_all_users(connection)

    if all_users != None:
        response = jsonify(all_users)
        return response
    else:
        abort(404)


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< STUDENTS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/get_all_students', methods = ['GET'])
def get_all_students():
    all_students = fetch_all_students(connection)

    if all_students != None:
        response = jsonify(all_students)
        return response
    else:
        abort(404)

@app.route('/get_available_students', methods = ['GET'])
def get_available_students():
    teacher_id = request.args.get('teacherid', None)
    course_id = request.args.get('courseid', None)
    all_students = fetch_available_students(connection=connection, teacher_id=teacher_id, course_id=course_id)

    if all_students != None:
        response = jsonify(all_students)
        return response
    else:
        abort(404)

@app.route('/update_student', methods = ['POST'])
def update_student():
    id = request.args['id']
    fullname = request.args['fullname']
    phone = request.args['phone']
    address = request.args['address']
    email = request.args['email']
    gender = request.args['gender']
    try:
        success = update_the_student(connection=connection, id=id, fullname=fullname, phone=phone, address=address, email=email, gender=gender)
        if success == True:
            return '', 200
        else:
            abort(404)
    except:
        abort(404)

@app.route('/get_all_students_by_class', methods = ['GET'])
def get_all_students_by_class():
    class_id  = request.args.get('classid', None)
    all_students_by_class = fetch_all_students_by_class(connection, class_id)
    if all_students_by_class != None:
        response = jsonify(all_students_by_class)
        return response
    else:
        abort(404)

@app.route('/get_student_image', methods = ['GET'])
def get_student_image():
    student_id  = request.args.get('studentid', None)
    file_img_name = 'Dataset/processed/' + student_id + '/0.png'
    with open(file_img_name, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        return jsonify({'img': "data:image/png;base64," + encoded_string})


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< COURSES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/create_course', methods = ['POST'])
def create_course():
    id = request.args.get('id', None)
    name = request.args.get('name', None)
    description = request.args.get('description', None)
    active = request.args.get('active', 1)
    try:
        success, message = add_new_course(connection=connection, id=id, name=name, description=description, active=active)
        if success == True:
            return message, 200
        else:
            return jsonify(message=message), 404
    except:
        abort(404)

@app.route('/update_course', methods = ['POST'])
def update_course():
    id = request.args.get('id', None)
    name = request.args.get('name', None)
    description = request.args.get('description', None)
    try:
        success = update_the_course(connection=connection, id=id, name=name, description=description)
        if success == True:
            return '', 200
        else:
            abort(404)
    except:
        abort(404)

@app.route('/update_status_course', methods = ['POST'])
def update_status_course():
    id = request.args.get('id', None)
    active = request.args.get('active', 1)
    try:
        success = update_the_status_course(connection=connection, id=id, active=active)
        if success == True:
            return '', 200
        else:
            abort(404)
    except:
        abort(404)

@app.route('/get_all_courses', methods = ['GET'])
def get_all_courses():
    all_courses = fetch_all_courses(connection)

    if all_courses != None:
        response = jsonify(all_courses)
        return response
    else:
        abort(404)

@app.route('/get_all_active_courses', methods = ['GET'])
def get_all_active_courses():
    all_courses = fetch_all_active_courses(connection=connection)

    if all_courses != None:
        response = jsonify(all_courses)
        return response
    else:
        abort(404)


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< TEACHERS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/get_all_teachers', methods = ['GET'])
def get_all_teachers():
    all_teachers = fetch_all_teachers(connection)

    if all_teachers != None:
        response = jsonify(all_teachers)
        return response
    else:
        abort(404)

@app.route('/add_teacher', methods = ['POST'])
def add_teacher():
    request_data = json.loads(request.data)
    try:
        success, message = add_new_teacher(connection=connection, request_data=request_data)
        if success == True:
            return message, 200
        else:
            return jsonify(message=message), 404
    except:
        abort(404)

@app.route('/update_teacher', methods = ['POST'])
def update_teacher():
    request_data = json.loads(request.data)
    try:
        success, message = update_the_teacher(connection=connection, request_data=request_data)
        if success == True:
            return message, 200
        else:
            abort(404)
    except:
        abort(404)


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CLASSES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/create_class', methods = ['POST'])
def create_class():
    request_data = json.loads(request.data)
    try:
        success, message = create_new_class(connection=connection, request_data=request_data)
        if success == True:
            return message, 200
        else:
            return jsonify(message=message), 404
    except:
        abort(404, message)

@app.route('/get_all_classes', methods = ['GET'])
def get_all_classes():
    all_classes = fetch_all_classes(connection)
    if all_classes != None:
        # convert any type (time type) to string
        response = json.dumps(all_classes, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404)    

@app.route('/get_class_by_class_id', methods = ['GET'])
def get_class_by_class_id(class_id):
    class_id = request.args.get('class_id', None)
    class_by_class_id = fetch_class_by_class_id(connection, class_id)
    if class_by_class_id != None:
        response = jsonify(class_by_class_id)
        return response
    else:
        abort(404)    

@app.route('/get_all_classes_by_teacher_today', methods = ['GET'])
def get_all_classes_by_teacher():
    semesterMonths = {1: [1, 2, 3, 4, 5], 2: [6, 7, 8, 9, 10, 11, 12]}  # semester 1 beginning from month 1 to 5 and semester 2 from 6 to 9
    teacher_id  = request.args.get('teacherid', None)
    day = get_day_of_today()
    # day = "Monday"  #??? remove this, this line for test
    month = get_this_month()
    year = get_this_year()
    all_classes_by_teacher = fetch_all_classes_by_teacher_today(connection, teacher_id, day)

    if all_classes_by_teacher != None:
        for eachClass in all_classes_by_teacher:
            for eachSemester in semesterMonths:
                if eachClass['semester'] == eachSemester and year == int(eachClass['year']):    
                    if month in semesterMonths[eachSemester]:
                        # convert any type (time type) to string
                        response = json.dumps(all_classes_by_teacher, indent=4, sort_keys=True, default=str)
                        return response
        return '', 200
    else:
        abort(404)

@app.route('/get_class_by_teacher_and_class_id', methods = ['GET'])
def get_class_by_teacher_and_class_id():
    teacher_id  = request.args.get('teacherid', None)
    class_id  = request.args.get('classid', None)
    day = get_day_of_today()
    # day = "Monday" # this for test
    class_by_teacher_and_class_id = fetch_class_by_teacher_and_class_id(connection, teacher_id, day, class_id)
    if class_by_teacher_and_class_id != None:
        # convert any type (time type) to string
        response = json.dumps(class_by_teacher_and_class_id, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404)

@app.route('/get_all_classes_by_year_semester_teacher', methods = ['GET'])
def get_all_classes_by_year_semester_teacher():
    year  = request.args.get('year', None)
    semester  = request.args.get('semester', None)
    teacher_id  = request.args.get('teacherid', None)

    all_classes_by_year_semester_teacher = fetch_all_classes_by_year_semester_teacher(connection, year, semester, teacher_id)
    if all_classes_by_year_semester_teacher != None:
        response = jsonify(all_classes_by_year_semester_teacher)
        return response
    else:
        abort(404)


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CLASSTIME >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  
@app.route('/get_all_class_time', methods = ['GET'])
def get_all_class_time():
    all_class_time = fetch_all_class_time(connection)
    if all_class_time != None:
        # convert any type (time type) to string
        response = json.dumps(all_class_time, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404)

@app.route('/get_class_time_by_class_id', methods = ['GET'])
def get_class_time_by_class_id():
    class_id  = request.args.get('classid', None)
    class_time = fetch_class_time_by_class_id(connection, class_id)
    if class_time != None:
        # convert any type (time type) to string
        response = json.dumps(class_time, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404)  

@app.route('/get_time_in_and_out_by_teacher_id_and_day', methods = ['GET'])
def get_time_in_and_out_by_teacher_id_and_day():
    teacher_id = request.args.get('teacherid', None)
    day = request.args.get('day', None)
    time_in_and_out = fetch_time_in_and_out_by_teacher_id_and_day(connection=connection, teacher_id=teacher_id, day=day)
    if time_in_and_out != None:
        # convert any type (time type) to string
        response = json.dumps(time_in_and_out, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404)  

# @app.route('/get_class_time_by_teacher_id_and_course_id', methods = ['GET'])
# def get_class_time_by_teacher_id_and_course_id():
#     teacher_id  = request.args.get('teacherid', None)
#     course_id  = request.args.get('courseid', None)
#     class_time = fetch_class_time_by_teacher_id_and_course_id(connection, teacher_id, course_id)
#     if class_time != None:
#         # convert any type (time type) to string
#         response = json.dumps(class_time, indent=4, sort_keys=True, default=str)
#         return response
#     else:
#         abort(404)  

    
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< TIMESHEET >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>     
@app.route('/create_today_class_timesheet', methods = ['POST'])
def create_today_class_timesheet():
    class_id = request.args.get('classid', None)
    day = get_day_of_today()
    today = date.today()
    try:
        success = create_class_timesheet_of_today(connection, class_id, day, today)
        if success == True:
            return '', 200
        else:
            abort(404)
    except:
        abort(404)

@app.route('/get_in_attendance', methods = ['GET'])
def get_in_attendance():
    class_id  = request.args.get('classid', None)
    today = date.today()
    in_attendance = is_in_attendance_taken(connection, class_id, today)
    if in_attendance != None:
        # convert any type (time type) to string
        response = json.dumps(in_attendance, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404)

@app.route('/get_out_attendance', methods = ['GET'])
def get_out_attendance():
    class_id  = request.args.get('classid', None)
    today = date.today()
    out_attendance = is_out_attendance_taken(connection, class_id, today)
    if out_attendance != None:
        # convert any type (time type) to string
        response = json.dumps(out_attendance, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404)

@app.route('/get_standard_in_out_attendance', methods = ['GET'])
def get_standard_in_out_attendance():
    class_id  = request.args.get('classid', None)
    day  = request.args.get('day', None)
    in_out_attendance = fetch_standard_in_out_attendance(connection, class_id, day)
    if in_out_attendance != None:
        # convert any type (time type) to string
        response = json.dumps(in_out_attendance, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404)

@app.route('/get_full_attendance', methods = ['GET'])
def get_full_attendance():
    class_id = request.args.get('classid', None)
    date = request.args.get('date', None)
    full_attendance = fetch_full_attendance(connection, class_id, date)
    if full_attendance != None:
        # convert any type (time type) to string
        response = json.dumps(full_attendance, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404)

@app.route('/get_timesheet_by_class_id', methods = ['GET'])
def get_timehseet_by_class_id():
    class_id = request.args.get('classid', None)
    full_attendance_by_classid = fetch_timesheet_by_class_id(connection, class_id)
    if full_attendance_by_classid != None:
        # convert any type (time type) to string
        response = json.dumps(full_attendance_by_classid, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404)

@app.route('/get_full_attendance_by_class_id', methods = ['GET'])
def get_full_attendance_by_class_id():
    class_id = request.args.get('classid', None)
    full_attendance_by_class_id = fetch_full_attendance_by_class_id(connection, class_id)
    if full_attendance_by_class_id != None:
        # convert any type (time type) to string
        response = json.dumps(full_attendance_by_class_id, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404) 

@app.route('/get_full_attendance_by_student_id', methods = ['GET'])
def get_full_attendance_by_student_id():
    class_id = request.args.get('classid', None)
    student_id = request.args.get('studentid', None)
    full_attendance_by_student_id = fetch_full_attendance_by_student_id(connection, class_id, student_id)
    if full_attendance_by_student_id != None:
        # convert any type (time type) to string
        response = json.dumps(full_attendance_by_student_id, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404) 


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< STATS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   
@app.route('/get_total_number_late_soon_stats', methods = ['GET'])
def get_total_number_late_soon_stats():
    class_id = request.args.get('classid', None)
    total_number_late_soon_stats = fetch_total_number_late_soon_stats(connection, class_id)
    if total_number_late_soon_stats != None:
        # convert any type (time type) to string
        response = json.dumps(total_number_late_soon_stats, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404) 


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< FACE RECOGNITION >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
stop_cam = False
student_attendance_info = []    # list of students who are attended
student_attendance_list = []    # list of students who needed to be attended
attendance_class_id = ''    # attendance class id
attendance_type = ''    # attendance type [in, out]


@app.route('/set_attendance')
def set_attendance():
    class_id  = request.args.get('classid', None)
    type  = request.args.get('attendancetype', None)
    teacher_id  = request.args.get('teacherid', None)
    global student_attendance_list
    global attendance_type
    global attendance_class_id
    global attendance_teacher_id
    global stop_cam

    student_attendance_info = []
    student_attendance_list = []
    attendance_type = type
    attendance_class_id = class_id
    attendance_teacher_id = teacher_id
    stop_cam = False

    try:
        all_students_by_class = fetch_all_students_by_class(connection, class_id)
        for student in all_students_by_class:
            student_attendance_list.append(student['studentid'])
        return '', 200
    except:
        abort(404)


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< JSON STREAM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/json_stream')
def json_stream():
    global student_attendance_info 
    global showed_student_attendance
    student_attendance_info = []
    showed_student_attendance = []  # student who is attended and showed in client side
    def generator():
        while stop_cam == False:
            time.sleep(1)
            if len(student_attendance_info) > 0:
                if student_attendance_info[-1]['student'] not in showed_student_attendance:
                    object_showed_student_attendance = {'student': student_attendance_info[-1]['student'], 'time': str(student_attendance_info[-1]['time'])}
                    yield str(object_showed_student_attendance)
                showed_student_attendance.append(student_attendance_info[-1]['student'])
    return Response(stream_with_context(generator()), status=200, content_type='application/json')


def videoStream(sess, MINSIZE, IMAGE_SIZE, INPUT_IMAGE_SIZE, pnet, rnet, onet, THRESHOLD, FACTOR, model, class_names, images_placeholder, phase_train_placeholder, embeddings, embedding_size, people_detected, person_detected):
    from imutils.video import VideoStream
    import imutils
    from src.align.detect_face import detect_face
    from src.facenet import prewhiten

    cap  = VideoStream(src=0).start()
    global stop_cam
    stop_cam = False
    global student_attendance_info 
    student_attendance_info = []
    global student_attendance_list
    global attendance_type
    global attendance_class_id
    global attendance_teacher_id

    while (True):
        frame = cap.read()
        frame = imutils.resize(frame, width=600)
        frame = cv2.flip(frame, 1)

        bounding_boxes, _ = detect_face(frame, MINSIZE, pnet, rnet, onet, THRESHOLD, FACTOR)

        faces_found = bounding_boxes.shape[0]
        try:
            if faces_found > 1:
                cv2.putText(frame, "Only one face", (0, 100), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                            1, (255, 255, 255), thickness=1, lineType=2)
            elif faces_found > 0:
                det = bounding_boxes[:, 0:4]
                bb = np.zeros((faces_found, 4), dtype=np.int32)
                for i in range(faces_found):
                    bb[i][0] = det[i][0]
                    bb[i][1] = det[i][1]
                    bb[i][2] = det[i][2]
                    bb[i][3] = det[i][3]
                    print(bb[i][3]-bb[i][1])
                    print(frame.shape[0])
                    print((bb[i][3]-bb[i][1])/frame.shape[0])
                    if (bb[i][3]-bb[i][1])/frame.shape[0]>0.25:
                        cropped = frame[bb[i][1]:bb[i][3], bb[i][0]:bb[i][2], :]
                        scaled = cv2.resize(cropped, (INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE),
                                            interpolation=cv2.INTER_CUBIC)
                        scaled = prewhiten(scaled)
                        scaled_reshape = scaled.reshape(-1, INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE, 3)
                        feed_dict = {images_placeholder: scaled_reshape, phase_train_placeholder: False}
                        emb_array = sess.run(embeddings, feed_dict=feed_dict)

                        predictions = model.predict_proba(emb_array)
                        best_class_indices = np.argmax(predictions, axis=1)
                        best_class_probabilities = predictions[
                            np.arange(len(best_class_indices)), best_class_indices]
                        best_name = class_names[best_class_indices[0]]
                        print("Name: {}, Probability: {}".format(best_name, best_class_probabilities))

                        if best_class_probabilities > 0.8:
                            cv2.rectangle(frame, (bb[i][0], bb[i][1]), (bb[i][2], bb[i][3]), (0, 255, 0), 2)
                            text_x = bb[i][0]
                            text_y = bb[i][3] + 20

                            name = class_names[best_class_indices[0]]
                            cv2.putText(frame, name, (text_x, text_y), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                                        1, (255, 255, 255), thickness=1, lineType=2)
                            cv2.putText(frame, str(round(best_class_probabilities[0], 3)), (text_x, text_y + 17),
                                        cv2.FONT_HERSHEY_COMPLEX_SMALL,
                                        1, (255, 255, 255), thickness=1, lineType=2)
                            person_detected[best_name] += 1


                            ###########################
                            ### get current time
                            now = datetime.now()
                            current_time = now.strftime("%H:%M:%S")
                            today = date.today()
                            day = get_day_of_today()
                            ### get standard time in and time out
                            class_by_teacher_and_class_id = fetch_class_by_teacher_and_class_id(connection, attendance_teacher_id, day, attendance_class_id)
                            standard_time_in = class_by_teacher_and_class_id['timein']
                            standard_time_out = class_by_teacher_and_class_id['timeout']


                            ### if student not exists in student_attendance_info list and student belongs to student_attendance_list
                            ### then add student attendance to student_attendance_info list 
                            if not any(obj['student'] == name for obj in student_attendance_info) \
                            and any(obj == name for obj in student_attendance_list):
                                # creating today timesheet for this class
                                create_class_timesheet_of_today(connection, attendance_class_id, day, today)
                                # add to list
                                student_attendance_info.append({
                                    'student': name,
                                    'time': current_time
                                })
                                if (attendance_type == 'in'):
                                    late = calculate_late_between_in_and_standard(current_time, str(standard_time_in))
                                    add_in_timesheet(connection=connection, class_id=attendance_class_id, student_id=name, date=today, time_in=current_time, late=late)
                                elif (attendance_type == 'out'):
                                    soon = calculate_soon_between_out_and_standard(current_time, str(standard_time_out))
                                    add_out_timesheet(connection=connection, class_id=attendance_class_id, student_id=name, date=today, time_out=current_time, soon=soon)


                        else:
                            cv2.rectangle(frame, (bb[i][0], bb[i][1]), (bb[i][2], bb[i][3]), (0, 0, 255), 2)
                            text_x = bb[i][0]
                            text_y = bb[i][3] + 20

                            name = "Unknown"
                            cv2.putText(frame, name, (text_x, text_y), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                                        1, (255, 255, 255), thickness=1, lineType=2)
                            cv2.putText(frame, str(round(best_class_probabilities[0], 3)), (text_x, text_y + 17),
                                        cv2.FONT_HERSHEY_COMPLEX_SMALL,
                                        1, (255, 255, 255), thickness=1, lineType=2)

        except:
            pass

        cv2.imshow('Face Recognition', frame)

        buffer = cv2.imencode('.jpg', frame)[1].tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')

        if cv2.waitKey(1) & 0xFF == ord('q') or stop_cam == True:
            break

    cap.stream.release()
    cv2.destroyAllWindows()

# loading model of face recognition using Facenet and SVM 
# sess, MINSIZE, IMAGE_SIZE, INPUT_IMAGE_SIZE, pnet, rnet, onet, THRESHOLD, FACTOR, model, class_names, images_placeholder, phase_train_placeholder, embeddings, embedding_size, people_detected, person_detected = face_recog.Face_Rec().main()
    

@app.route('/face_rec')
def face_rec():
    global stop_cam

    # classifying aligned face folder from MTCNN steps
    # import src.face_recognition as face_recog
    # import src.classifier as clf
    # from src.classifier import parse_arguments
    # clf.main(parse_arguments([
    #     'TRAIN',      # mode ['TRAIN', 'CLASSIFY']
    #     'Dataset/processed',     # aligned face folder
    #     'Models/20180402-114759.pb',    # model
    #     'Models/facemodel.pkl',      # pickle file (classifier_filename)
    #     '--batch_size', '1000'   # number of images to process in a batch
    # ]))

    # sess, MINSIZE, IMAGE_SIZE, INPUT_IMAGE_SIZE, pnet, rnet, onet, THRESHOLD, FACTOR, model, class_names, images_placeholder, phase_train_placeholder, embeddings, embedding_size, people_detected, person_detected = face_recog.Face_Rec().main()
    # return Response(
    #     videoStream(sess, MINSIZE, IMAGE_SIZE, INPUT_IMAGE_SIZE, pnet, rnet, onet, THRESHOLD, FACTOR, model, class_names, images_placeholder, phase_train_placeholder, embeddings, embedding_size, people_detected, person_detected),
    #     mimetype='multipart/x-mixed-replace; boundary=frame'
    # )

    # using Facenet and SVM to predict face in each frame through video stream
    global sess, MINSIZE, IMAGE_SIZE, INPUT_IMAGE_SIZE, pnet, rnet, onet, THRESHOLD, FACTOR, model, class_names, images_placeholder, phase_train_placeholder, embeddings, embedding_size, people_detected, person_detected
    return Response(
        videoStream(sess, MINSIZE, IMAGE_SIZE, INPUT_IMAGE_SIZE, pnet, rnet, onet, THRESHOLD, FACTOR, model, class_names, images_placeholder, phase_train_placeholder, embeddings, embedding_size, people_detected, person_detected),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

from datetime import datetime
@app.route('/stop_video_stream')
def stop_video_stream():
    global stop_cam 
    stop_cam = True
    for item in student_attendance_info:
        print(item)
    return jsonify(student_attendance_info)


if __name__ == "__main__":
    app.run(host='localhost', port=7000, debug=True)

# if __name__ == "__main__" means run python command with this file
#app.run(host='localhost', port=7000, debug=True)


