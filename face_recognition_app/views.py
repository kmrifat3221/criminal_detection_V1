from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from .models import Criminal, Detection, Camera
from .forms import CameraForm  # Import CameraForm
import cv2
import numpy as np
from datetime import datetime, timedelta
import os
from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib import messages

class CriminalListView(LoginRequiredMixin, ListView):
    model = Criminal
    template_name = 'face_recognition_app/criminal_list.html'
    context_object_name = 'criminals'
    ordering = ['-date_added']

class CriminalDetailView(LoginRequiredMixin, DetailView):
    model = Criminal
    template_name = 'face_recognition_app/criminal_detail.html'

class CriminalCreateView(LoginRequiredMixin, CreateView):
    model = Criminal
    template_name = 'face_recognition_app/criminal_form.html'
    fields = ['name', 'age', 'gender', 'crime_type', 'description', 'photo']
    success_url = '/criminals/'

def save_detection_with_video(frame, criminal, camera_id, confidence, location):
    # Create a new detection instance
    detection = Detection.objects.create(
        criminal=criminal,
        location=location,
        confidence_score=confidence,
        camera_id=camera_id
    )

    # Save the detection image
    success, buffer = cv2.imencode('.jpg', frame)
    if success:
        image_content = ContentFile(buffer.tobytes())
        detection.image_captured.save(
            f'detection_{detection.id}.jpg',
            image_content
        )

    # Start recording video clip
    video_path = os.path.join(settings.MEDIA_ROOT, 'temp_videos', f'detection_{detection.id}.mp4')
    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    # Set video writer properties
    frame_height, frame_width = frame.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, 20.0, (frame_width, frame_height))

    # Record for 1 minute after detection
    detection.video_start_time = timezone.now()
    frames_to_record = 20 * 60  # 20 fps * 60 seconds
    frame_buffer = []

    try:
        cap = cv2.VideoCapture(camera_id if camera_id.isdigit() else camera_id)
        frame_count = 0

        while frame_count < frames_to_record:
            ret, frame = cap.read()
            if not ret:
                break

            out.write(frame)
            frame_count += 1

        cap.release()
        out.release()

        # Save the video file to the detection
        with open(video_path, 'rb') as f:
            detection.video_clip.save(
                f'detection_{detection.id}.mp4',
                File(f)
            )
        
        detection.video_end_time = timezone.now()
        detection.save()

        # Clean up temporary file
        if os.path.exists(video_path):
            os.remove(video_path)

    except Exception as e:
        print(f"Error recording video: {str(e)}")

    return detection

def gen_frames(camera_id):
    # Load face detection cascade classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    try:
        # Try to get camera URL from database
        try:
            camera = Camera.objects.get(camera_id=camera_id)
            if camera.url:  # If camera has a URL, use it
                cap = cv2.VideoCapture(camera.url)
            else:  # Otherwise try camera_id
                cap = cv2.VideoCapture(int(camera_id) if camera_id.isdigit() else camera_id)
        except Camera.DoesNotExist:
            # Fallback to direct camera_id if not found in database
            cap = cv2.VideoCapture(int(camera_id) if camera_id.isdigit() else camera_id)

        if not cap.isOpened():
            print(f"Error: Could not open camera {camera_id}")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"Error: Could not read frame from camera {camera_id}")
                break

            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Draw rectangle around faces and process each face
            for (x, y, w, h) in faces:
                # Draw rectangle around face
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                # Get the face ROI (Region of Interest)
                face_roi = frame[y:y+h, x:x+w]
                
                try:
                    # Convert ROI to RGB for face recognition
                    rgb_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
                    
                    # Get all active criminals
                    criminals = Criminal.objects.filter(is_active=True)
                    
                    # Compare with each criminal's photo
                    for criminal in criminals:
                        if criminal.photo:
                            # Read criminal's photo
                            photo_path = criminal.photo.path
                            criminal_img = cv2.imread(photo_path)
                            if criminal_img is not None:
                                # Convert to RGB
                                criminal_rgb = cv2.cvtColor(criminal_img, cv2.COLOR_BGR2RGB)
                                
                                # Calculate similarity (using histogram comparison)
                                face_hist = cv2.calcHist([rgb_face], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                                criminal_hist = cv2.calcHist([criminal_rgb], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                                
                                # Normalize histograms
                                cv2.normalize(face_hist, face_hist)
                                cv2.normalize(criminal_hist, criminal_hist)
                                
                                # Compare histograms
                                similarity = cv2.compareHist(face_hist, criminal_hist, cv2.HISTCMP_CORREL)
                                
                                # If similarity is high enough
                                if similarity > 0.5:  # Adjust this threshold as needed
                                    # Get camera location
                                    try:
                                        camera = Camera.objects.get(camera_id=camera_id)
                                        location = camera.location
                                    except Camera.DoesNotExist:
                                        location = "Unknown"
                                    
                                    # Save detection with video
                                    detection = save_detection_with_video(
                                        frame,
                                        criminal,
                                        camera_id,
                                        similarity,
                                        location
                                    )
                                    
                                    # Draw name and confidence on frame
                                    cv2.putText(frame,
                                              f"{criminal.name} ({similarity:.2f})",
                                              (x, y-10),
                                              cv2.FONT_HERSHEY_SIMPLEX,
                                              0.9,
                                              (0, 255, 0),
                                              2)
                
                except Exception as e:
                    print(f"Error processing face: {str(e)}")
                    continue

            # Add timestamp to frame
            cv2.putText(frame, 
                       datetime.now().strftime('%Y-%m-d %H:%M:%S'),
                       (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       1,
                       (0, 255, 0),
                       2)

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print(f"Error: Could not encode frame from camera {camera_id}")
                break
                
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    except Exception as e:
        print(f"Error in gen_frames: {str(e)}")
    finally:
        if 'cap' in locals():
            cap.release()

@login_required
def video_feed(request, camera_id):
    """Video streaming route"""
    return StreamingHttpResponse(gen_frames(camera_id),
                               content_type='multipart/x-mixed-replace; boundary=frame')

@login_required
def dashboard(request):
    """Main dashboard view"""
    context = {
        'cameras': Camera.objects.filter(is_active=True),
        'recent_detections': Detection.objects.order_by('-timestamp')[:10],
        'total_criminals': Criminal.objects.count(),
        'total_detections': Detection.objects.count(),
    }
    return render(request, 'face_recognition_app/dashboard.html', context)

@login_required
def get_recent_detections(request):
    """AJAX endpoint for getting recent detections"""
    detections = Detection.objects.order_by('-timestamp')[:5]
    data = [{
        'criminal_name': d.criminal.name,
        'timestamp': d.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'location': d.location,
        'confidence': d.confidence_score,
        'camera_id': d.camera_id,
    } for d in detections]
    return JsonResponse({'detections': data})

@login_required
def recent_detections(request):
    # Get the last 10 detections
    detections = Detection.objects.select_related('criminal').order_by('-timestamp')[:10]
    return render(request, 'face_recognition_app/recent_detections.html', {'detections': detections})

@login_required
def add_camera(request):
    if request.method == 'POST':
        form = CameraForm(request.POST)
        if form.is_valid():
            try:
                camera = form.save()
                messages.success(request, 'Camera added successfully!')
                return redirect('camera-list')
            except Exception as e:
                messages.error(request, f'Error adding camera: {str(e)}')
    else:
        form = CameraForm()
    
    return render(request, 'face_recognition_app/camera_form.html', {'form': form})

@login_required
def edit_camera(request, id):
    camera = Camera.objects.get(id=id)  # Get the camera by ID
    if request.method == 'POST':
        form = CameraForm(request.POST, instance=camera)  # Bind the form to the camera instance
        if form.is_valid():
            form.save()  # Save the updated camera details
            messages.success(request, 'Camera updated successfully!')
            return redirect('camera_list.html')  # Redirect to the camera list after saving
    else:
        form = CameraForm(instance=camera)  # Create a form instance with the camera's current data

    return render(request, 'face_recognition_app/edit_camera.html', {'form': form})  # Render the form template

@login_required
def delete_camera(request, id):
    camera = Camera.objects.get(id=id)  # Get the camera by ID
    if request.method == 'POST':
        camera.delete()  # Delete the camera
        messages.success(request, 'Camera deleted successfully!')
        return redirect('camera_list')  # Redirect to the camera list after deletion
    return render(request, 'face_recognition_app/confirm_delete.html', {'camera': camera})  # Render a confirmation template

@login_required
def camera_list(request):
    cameras = Camera.objects.all()
    return render(request, 'face_recognition_app/camera_list.html', {'cameras': cameras})

@login_required
def test_camera(request, camera_id):
    try:
        camera = Camera.objects.get(id=camera_id)
        # Test camera connection
        if camera.camera_id.isdigit():
            cap = cv2.VideoCapture(int(camera.camera_id))
        else:
            cap = cv2.VideoCapture(camera.camera_id)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                messages.success(request, 'Camera test successful!')
            else:
                messages.error(request, 'Could not read frame from camera')
        else:
            messages.error(request, 'Could not connect to camera')
        cap.release()
    except Exception as e:
        messages.error(request, f'Error testing camera: {str(e)}')
    
    return redirect('camera-list')