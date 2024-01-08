from flask import Blueprint, get_flashed_messages, redirect, render_template, request, flash, jsonify,  Response, session, url_for
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField, DecimalRangeField, IntegerRangeField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, NumberRange
import requests
import os
from .models import Camera
from . import db
import json
from ultralytics import YOLO
import cv2
import math
import time


# Required to run the YOLOv8 model
import cv2

views = Blueprint('views', __name__)


# Initialize global variables
global_label = ""

def video_detection(path_x):
    global global_label 

    video_capture = path_x
    cap = cv2.VideoCapture(video_capture)
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    model = YOLO("YOLO-Weights/drone_yolov8n_50.pt")
    classNames = ["drone"]
    threshold = 0.45

    while True:
        success, img = cap.read()
        detected_drone = False  

        results = model(img, stream=True)
        for r in results:
            boxes = r.boxes
            for box in boxes:
                conf = box.conf[0]
                if conf >= threshold:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
                    conf = math.ceil((conf * 100)) / 100
                    cls = int(box.cls[0])
                    class_name = classNames[cls]
                    center_x = int((x1 + x2) / 2)
                    center_y = int((y1 + y2) / 2)
                    cv2.circle(img, (center_x, center_y), 3, (255, 0, 255), -1)
                    label = f'{class_name} : X={center_x}-Y={center_y}'
                    koordinat = f'X={center_x}-Y={center_y}'
                    t_size = cv2.getTextSize(label, 0, fontScale=0.4, thickness=1)[0]
                    c2 = x1 + t_size[0], y1 - t_size[1] - 3
                    cv2.rectangle(img, (x1, y1), c2, [255, 0, 255], -1, cv2.LINE_AA)
                    cv2.putText(img, label, (x1, y1 - 2), 0, 0.4, [255, 255, 255], thickness=1, lineType=cv2.LINE_AA)

                    # Set the global label variable
                    global_label = koordinat

                    # Set the flag to indicate detection
                    detected_drone = True

        # If no drone is detected, reset the coordinate values
        if not detected_drone:
            global_label = 'X=0-Y=0'

        yield img

        
def generate_frames_web(path_x):
    yolo_output = video_detection(path_x)
    for detection_ in yolo_output:
        ref, buffer = cv2.imencode('.jpg', detection_)

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



@views.route('/', methods=['GET', 'POST'])
@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    messages = get_flashed_messages(with_categories=True)
    session.clear()
    cameras = Camera.query.all()
    print(cameras)
    return render_template('home.html', cameras = cameras, flashed_messages=messages)


last_coordinates = {"XCoord": None, "YCoord": None}
last_update_time = time.time()

@views.route('/get_coordinates')
def get_coordinates():
    global last_coordinates, last_update_time
    session.clear()
    data = global_label

    # Check if data has the expected format
    if '-' in data and '=' in data:
        x_value = data.split('-')[0].split('=')[1]
        y_value = data.split('-')[1].split('=')[1]

        coordinates = {
            "XCoord": x_value,
            "YCoord": y_value
        }

    else:
        coordinates = {"XCoord": "0", "YCoord": "0"}

    print(coordinates)
    return coordinates

@views.route('/send_coordinates')
def send_coordinates():
    global last_coordinates, last_update_time
    session.clear()
    data = global_label

    # Check if data has the expected format
    if '-' in data and '=' in data:
        x_value = data.split('-')[0].split('=')[1]
        y_value = data.split('-')[1].split('=')[1]

        # Creating a dictionary for the coordinates
        coordinates = {
            "XCoord": x_value,
            "YCoord": y_value
        }

    else:
        coordinates = {"XCoord": "0", "YCoord": "0"}

    # URL endpoint to send the coordinates
    endpoint_url = "http://192.168.0.2:5000/api"

    try:
        # Sending POST request with the coordinates data
        response = requests.post(endpoint_url, json=coordinates)

        if response.status_code == 200:
            print("Coordinates sent successfully!")
        else:
            print(f"Failed to send coordinates. Status code: {response.status_code}")

    except Exception as e:
        print(f"Error sending coordinates: {str(e)}")


@views.route("/ipcam", methods=['GET', 'POST'])
@login_required
def Ipcam():
    session.clear()

    # Mengecek apakah 'id' ada dalam parameter URL
    camera_id = request.args.get('id')
    if camera_id is not None:
        print(f"Camera ID: {camera_id}")
    else:
        print("No Camera ID found in the URL")

    return render_template('stream.html', camera = camera_id)


@views.route('/Ipapp')
def Ipapp():
    id_cam = request.args.get('id')
    data_cam = Camera.query.filter_by(id=id_cam).all()

    for camera in data_cam:
        print(camera.id, camera.lokasi, camera.ipcam)

        ipcam_length = len(camera.ipcam)

        if 0 < ipcam_length <= 2:
            # Jalankan fungsi tertentu jika panjang string antara 1 dan 10
            ipcam_value = int(camera.ipcam)
            return Response(generate_frames_web(path_x=ipcam_value), mimetype='multipart/x-mixed-replace; boundary=frame')
        else:
            return Response(generate_frames_web(path_x=f'{camera.ipcam}'), mimetype='multipart/x-mixed-replace; boundary=frame')
        

@views.route('/list-cam', methods=['GET', 'POST'])
@login_required
def list():
    messages = get_flashed_messages(with_categories=True)
    session.clear()
    cameras = Camera.query.all()
    print(cameras)
    return render_template('list_cam.html', cameras = cameras, flashed_messages=messages)

@views.route("/tambah-cam", methods=['GET', 'POST'])
@login_required
def tambahCam():
    session.clear()
    if request.method == 'POST':
        lokasi = request.form.get('lokasi')
        ipcam = request.form.get('ipcam')

        # Menggunakan current_user untuk mendapatkan pengguna yang sudah login
        user = current_user

        # Memeriksa apakah nilai formulir kosong
        if not lokasi or not ipcam:
            flash('Lokasi dan IP Camera harus diisi.', category='error')
            print('Formulir tidak lengkap.')
        else:
            # Memeriksa apakah ipcam sudah ada dalam tabel Camera
            existing_camera = Camera.query.filter_by(ipcam=ipcam).first()
            if existing_camera:
                flash('IP Camera already exists. Please use a different IP.', category='error')
                print('IP Camera already exists.')
            else:
                # Membuat objek Camera baru dan menyimpannya ke dalam database
                new_camera = Camera(lokasi=lokasi, ipcam=ipcam)
                db.session.add(new_camera)
                db.session.commit()
                
                flash('Camera added successfully!', category='success')
                print('Success')
                return redirect(url_for('views.list'))
    return render_template('tambah_cam.html')

@views.route("/hapus-cam", methods=['GET', 'POST'])
@login_required
def hapusCam():
    session.clear()
    id_cam = request.args.get('id')
    # Menggunakan current_user untuk mendapatkan pengguna yang sudah login
    user = current_user

    # Memeriksa apakah kamera dengan camera_id tertentu ada dalam tabel Camera
    camera_to_delete = Camera.query.get(id_cam)
    if camera_to_delete:
        # Menghapus kamera dari database
        db.session.delete(camera_to_delete)
        db.session.commit()

        flash('Camera deleted successfully!', category='success')
        print('Success')
    else:
        flash('Camera not found.', category='error')
        print('Camera not found.')
    return redirect(url_for('views.list'))

@views.route("/edit-cam", methods=['GET', 'POST'])
@login_required
def editCam():
    messages = get_flashed_messages(with_categories=True)
    session.clear()
    id_cam = request.args.get('id')
    data_cam = Camera.query.filter_by(id=id_cam).all()
    lokasi = request.form.get('lokasi')
    Newipcam = request.form.get('Newipcam')
    Oldipcam = request.form.get('Oldipcam')
    print(data_cam)
    

    # Menggunakan current_user untuk mendapatkan pengguna yang sudah login
    user = current_user

    # Memeriksa apakah nilai formulir kosong
    if request.method == 'POST':
        # Memeriksa apakah ipcam sudah ada dalam tabel Camera
        existing_camera = Camera.query.filter_by(ipcam=Newipcam).first()
        data = Camera.query.filter_by(id=id_cam).first()
        print(existing_camera)
        if existing_camera:
            # Check if the ipcam is the same as the old one
            if Newipcam == Oldipcam:
                existing_camera.lokasi = lokasi
                db.session.commit()

                flash('Camera updated successfully!', category='success')
                print('Update success')
                return redirect(url_for('views.list'))
            else:
                flash('IP Camera already exists. Please use a different IP.', category='error')
                print('IP Camera already exists.')
                return redirect(url_for('views.editCam', id=id_cam))
        else:
            # Membuat objek Camera baru dan menyimpannya ke dalam database
            data.lokasi = lokasi
            data.ipcam = Newipcam
            
            db.session.commit()

            flash('Camera updated successfully!', category='success')
            print('Success')
            return redirect(url_for('views.list'))
    return render_template('edit_cam.html', cameras=data_cam, flashed_messages=messages)



@views.route('/test')
def index():
    return render_template('test.html')
