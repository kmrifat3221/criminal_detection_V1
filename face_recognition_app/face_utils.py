import numpy as np
import cv2
from .models import Criminal, Detection
import pickle

class FaceRecognitionSystem:
    def __init__(self):
        self.known_criminals = []
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def process_frame(self, frame, camera_id, location):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        
        detections = []
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        return frame, detections

    def update_encodings(self, criminal):
        if criminal.photo:
            self.known_criminals.append(criminal)
            return True
        return False