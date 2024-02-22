from flask import Flask, jsonify, request, Response, abort, json
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
 
app = Flask(__name__)
CORS(app, origins='http://localhost:3000')
bcrypt = Bcrypt(app) 


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< MYSQL DATABASE CONNECTION >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
connection = create_server_connection("localhost", "root", "root")
use_face_attendance_database(connection, "face_attendance")


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< IMAGES ALIGNMENT >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def align_images(class_name):
    import src.align_dataset_mtcnn as mtcnn
    from src.align_dataset_mtcnn import parse_arguments
    sys.argv[1:] = [
        'Dataset/raw',      # input directory
        class_name,     # input class directory name
        'Dataset/processed',    # output directory
        '--image_size', '160',      # aligned image size
        '--margin', '32',   # margin bounding box
        '--random_order',   # shuffling the order of aligned images
        '--gpu_memory_fraction', '0.25'     # the amount of gpu memory
    ]
    mtcnn.main(parse_arguments(sys.argv[1:]))
    


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< GENERATE IMAGES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def generate_images(id, fullname, phone, address, email):
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
        if cv2.waitKey(1) & 0xFF == ord('q') or i == 20: 
            break

    # release video capture
    cap.release()
    cv2.destroyAllWindows()

    # add new student to database       
    add_new_student(connection=connection, id=id, fullname=fullname, phone=phone, address=address, email=email)
    
    

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< APP ROUTES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< VIDEO FRAMES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/video_feed')
def open_video():
    id = request.args['id']
    fullname = request.args['fullname']
    phone = request.args['phone']
    address = request.args['address']
    email = request.args['email']
    # Video streaming route. Put this in the src attribute of an img tag
    return Response(
        generate_images(id=id, fullname=fullname, phone=phone, address=address, email=email),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< SIGN IN >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/signin', methods = ['POST'])
def sign_in():
    username = request.args.get('username', None)
    password = request.args.get('password', None)

    this_user = get_user(connection, username=username, password=password)

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

###
@app.route('/test', methods = ['GET'])
def test():
    response = jsonify(hi="Welcome Xin Chao")
    return response
###

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< SCAN >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/create_scan', methods = ['POST'])
def create_directory_for_new_user():
    newuser = request.args.get('newuser', None)
    raw_directory = 'Dataset/raw'
    path = os.path.join(raw_directory, newuser)
    try:
        os.mkdir(path) 
    except FileExistsError:
        pass
        abort(404)
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

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< STUDENTS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/get_all_students', methods = ['GET'])
def get_all_students():
    all_students = fetch_all_students(connection)

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
    try:
        success = update_the_student(connection=connection, id=id, fullname=fullname, phone=phone, address=address, email=email)
        if success == True:
            return '', 200
        else:
            abort(404)
    except:
        abort(404)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< COURSES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/create_course', methods = ['POST'])
def create_course():
    id = request.args.get('id', None)
    name = request.args.get('name', None)
    description = request.args.get('description', None)
    active = request.args.get('active', 1)
    try:
        success = add_new_course(connection=connection, id=id, name=name, description=description, active=active)
        if success == True:
            return '', 200
        else:
            abort(404)
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
        success = add_new_teacher(connection=connection, request_data=request_data)
        if success == True:
            return '', 200
        else:
            abort(404)
    except:
        abort(404)

@app.route('/update_teacher', methods = ['POST'])
def update_teacher():
    request_data = json.loads(request.data)
    try:
        success = update_the_teacher(connection=connection, request_data=request_data)
        if success == True:
            return '', 200
        else:
            abort(404)
    except:
        abort(404)


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CLASSES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/create_class', methods = ['POST'])
def create_class():
    request_data = json.loads(request.data)
    try:
        success = create_new_class(connection=connection, request_data=request_data)
        if success == True:
            return '', 200
        else:
            abort(404)
    except:
        abort(404)


if __name__ == "__main__":
    app.run(host='localhost', port=7000, debug=True)

# if __name__ == "__main__" means run python command with this file
#app.run(host='localhost', port=7000, debug=True)


