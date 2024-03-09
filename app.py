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
from utils import *
 
app = Flask(__name__)
CORS(app, origins='http://localhost:3000')
CORS(app, origins='http://localhost:3001')
bcrypt = Bcrypt(app) 


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< MYSQL DATABASE CONNECTION >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
connection = create_server_connection("localhost", "root", "root")
use_face_attendance_database(connection, "face_attendance")


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

@app.route('/get_all_students_by_class', methods = ['GET'])
def get_all_students_by_class():
    class_id  = request.args.get('classid', None)
    print(class_id)
    all_students_by_class = fetch_all_students_by_class(connection, class_id)
    if all_students_by_class != None:
        response = jsonify(all_students_by_class)
        return response
    else:
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

@app.route('/get_all_classes_by_teacher', methods = ['GET'])
def get_all_classes_by_teacher():
    teacher_id  = request.args.get('teacherid', None)
    day = get_day_of_today()
    all_classes_by_teacher = fetch_all_classes_by_teacher(connection, teacher_id, day)
    if all_classes_by_teacher != None:
        # convert any type (time type) to string
        response = json.dumps(all_classes_by_teacher, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404)

@app.route('/get_class_by_teacher_and_class_id', methods = ['GET'])
def get_class_by_teacher_and_class_id():
    teacher_id  = request.args.get('teacherid', None)
    class_id  = request.args.get('classid', None)
    day = get_day_of_today()
    class_by_teacher_and_class_id = fetch_class_by_teacher_and_class_id(connection, teacher_id, day, class_id)
    if class_by_teacher_and_class_id != None:
        # convert any type (time type) to string
        response = json.dumps(class_by_teacher_and_class_id, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404)

    
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< TIMESHEET >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/get_in_attendance', methods = ['GET'])
def get_in_attendance():
    class_id  = request.args.get('classid', None)
    date='2024-03-04'
    in_attendance = is_in_attendance_taken(connection, class_id, date)
    if in_attendance != None:
        # convert any type (time type) to string
        response = json.dumps(in_attendance, indent=4, sort_keys=True, default=str)
        return response
    else:
        abort(404)

@app.route('/get_out_attendance', methods = ['GET'])
def get_out_attendance():
    class_id  = request.args.get('classid', None)
    date='2024-03-04'
    out_attendance = is_out_attendance_taken(connection, class_id, date)
    if out_attendance != None:
        # convert any type (time type) to string
        response = json.dumps(out_attendance, indent=4, sort_keys=True, default=str)
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

    student_attendance_info = []
    student_attendance_list = []
    attendance_type = type
    attendance_class_id = class_id
    attendance_teacher_id = teacher_id

    try:
        all_students_by_class = fetch_all_students_by_class(connection, class_id)
        for student in all_students_by_class:
            student_attendance_list.append(student['studentid'])
        return '', 200
    except:
        abort(404)


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
                            class_by_teacher_and_class_id = fetch_class_by_teacher_and_class_id(connection, attendance_teacher_id, 'Monday', attendance_class_id)
                            standard_time_in = class_by_teacher_and_class_id['timein']
                            standard_time_out = class_by_teacher_and_class_id['timeout']

                            ### if student not exists in student_attendance_info list and student belongs to student_attendance_list
                            ### then add student attendance to student_attendance_info list 
                            if not any(obj['student'] == name for obj in student_attendance_info) \
                            and any(obj == name for obj in student_attendance_list):
                                student_attendance_info.append({
                                    'student': name,
                                    'time': current_time
                                })
                                if (attendance_type == 'in'):
                                    late = calculate_late_between_in_and_standard(current_time, str(standard_time_in))
                                    # change day=day and date=today
                                    add_in_timesheet(connection=connection, classid=attendance_class_id, studentid=name, day='Monday', date='2024-03-04', timein=current_time, late=late)
                                elif (attendance_type == 'out'):
                                    soon = calculate_soon_between_out_and_standard(current_time, str(standard_time_out))
                                    # change day=day and date=today
                                    add_out_timesheet(connection=connection, classid=attendance_class_id, studentid=name, date='2024-03-04', timeout=current_time, soon=soon)


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


@app.route('/face_rec')
def face_rec():
    global stop_cam

    # classifying aligned face folder from MTCNN steps
    import src.face_recognition as face_recog
    import src.classifier as clf
    from src.classifier import parse_arguments
    clf.main(parse_arguments([
        'TRAIN',      # mode ['TRAIN', 'CLASSIFY']
        'Dataset/processed',     # aligned face folder
        'Models/20180402-114759.pb',    # model
        'Models/facemodel.pkl',      # pickle file
        '--batch_size', '1000'   # number of images to process in a batch
    ]))

    # using Facenet and SVM to predict face in each frame through video stream
    sess, MINSIZE, IMAGE_SIZE, INPUT_IMAGE_SIZE, pnet, rnet, onet, THRESHOLD, FACTOR, model, class_names, images_placeholder, phase_train_placeholder, embeddings, embedding_size, people_detected, person_detected = face_recog.Face_Rec().main()
    return Response(
        videoStream(sess, MINSIZE, IMAGE_SIZE, INPUT_IMAGE_SIZE, pnet, rnet, onet, THRESHOLD, FACTOR, model, class_names, images_placeholder, phase_train_placeholder, embeddings, embedding_size, people_detected, person_detected),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

from datetime import datetime
@app.route('/stop_video_stream')
def stop_video_stream():
    # global stop_cam 
    # stop_cam = True
    for item in student_attendance_info:
        print(item)
    return jsonify(student_attendance_info)



if __name__ == "__main__":
    app.run(host='localhost', port=7000, debug=True)

# if __name__ == "__main__" means run python command with this file
#app.run(host='localhost', port=7000, debug=True)


