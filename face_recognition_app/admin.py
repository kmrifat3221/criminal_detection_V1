from django.contrib import admin
from .models import Criminal, Detection, Camera

# Register your models here.

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ('camera_id', 'location', 'is_active', 'last_checked')
    list_filter = ('is_active', 'location')
    search_fields = ('camera_id', 'location', 'description')
    ordering = ('camera_id',)

@admin.register(Criminal)
class CriminalAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'gender', 'crime_type', 'is_active', 'date_added')
    list_filter = ('is_active', 'gender', 'crime_type')
    search_fields = ('name', 'crime_type', 'description')
    ordering = ('-date_added',)

@admin.register(Detection)
class DetectionAdmin(admin.ModelAdmin):
    list_display = ('criminal', 'timestamp', 'location', 'camera_id', 'confidence_score')
    list_filter = ('timestamp', 'location', 'camera_id')
    search_fields = ('criminal__name', 'location', 'camera_id')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
