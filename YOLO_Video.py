from ultralytics import YOLO
import cv2
import math
from flask import Flask, render_template, Response, jsonify

def video_detection(path_x):
    video_capture = path_x
    # Create a Webcam Object
    cap = cv2.VideoCapture(video_capture)
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    model = YOLO("../YOLO-Weights/drone_yolov8n_50.pt")
    classNames = ["drone"]
    threshold = 0.45  # Set your desired threshold value

    while True:
        success, img = cap.read()
        results = model(img, stream=True)
        for r in results:
            boxes = r.boxes
            for box in boxes:
                conf = box.conf[0]
                if conf >= threshold:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    print(x1, y1, x2, y2)
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
                    conf = math.ceil((conf * 100)) / 100
                    cls = int(box.cls[0])
                    class_name = classNames[cls]
                    # Calculate the center of the rectangle
                    center_x = int((x1 + x2) / 2)
                    center_y = int((y1 + y2) / 2)
                    cv2.circle(img, (center_x, center_y), 3, (255, 0, 255), -1)
                    label = f'{class_name} : X={center_x}-Y={center_y}'
                    t_size = cv2.getTextSize(label, 0, fontScale=0.4, thickness=1)[0]
                    print(t_size)
                    c2 = x1 + t_size[0], y1 - t_size[1] - 3
                    cv2.rectangle(img, (x1, y1), c2, [255, 0, 255], -1, cv2.LINE_AA)  # filled
                    cv2.putText(img, label, (x1, y1 - 2), 0, 0.4, [255, 255, 255], thickness=1, lineType=cv2.LINE_AA)
        yield img


cv2.destroyAllWindows()