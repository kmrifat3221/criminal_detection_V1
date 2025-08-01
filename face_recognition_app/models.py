from django.db import models
from django.utils import timezone

class Criminal(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    crime_type = models.CharField(max_length=100)
    description = models.TextField()
    photo = models.ImageField(upload_to='criminal_photos/')
    date_added = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.crime_type}"

class Detection(models.Model):
    criminal = models.ForeignKey(Criminal, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=200)
    confidence_score = models.FloatField()
    camera_id = models.CharField(max_length=100)
    image_captured = models.ImageField(upload_to='detections/', null=True, blank=True)
    video_clip = models.FileField(upload_to='detection_videos/', null=True, blank=True)
    video_start_time = models.DateTimeField(null=True, blank=True)
    video_end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.criminal.name} detected at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']  # Show newest detections first

class Camera(models.Model):
    camera_id = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    url = models.URLField(max_length=500, blank=True, null=True, help_text="URL for IP camera (optional)")
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.location} - {self.camera_id}"