# face_detection.py
import cv2
import base64
import numpy as np

cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(cascade_path)

def detect_face_from_base64(b64str: str):
    """
    Accepts raw base64 string (no data: prefix).
    Returns dict: faces_detected, boxes, status (ok/alert)
    """
    try:
        b = base64.b64decode(b64str)
        arr = np.frombuffer(b, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return {"faces_detected": 0, "status": "decode_failed"}
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60,60))
        boxes = [{"x": int(x), "y": int(y), "w": int(w), "h": int(h)} for (x,y,w,h) in faces]
        status = "ok" if len(faces) == 1 else "alert"
        h, w = img.shape[:2]
        return {"faces_detected": len(faces), "boxes": boxes, "status": status, "image_w": w, "image_h": h}
    except Exception as e:
        return {"faces_detected": 0, "status": f"error: {e}"}
