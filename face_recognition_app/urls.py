from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('criminals/', views.CriminalListView.as_view(), name='criminal-list'),
    path('criminals/add/', views.CriminalCreateView.as_view(), name='criminal-add'),
    path('criminals/<int:pk>/', views.CriminalDetailView.as_view(), name='criminal-detail'),
    path('cameras/', views.camera_list, name='camera-list'),
    path('cameras/add/', views.add_camera, name='add-camera'),
    path('cameras/test/<int:camera_id>/', views.test_camera, name='test-camera'),
    path('video-feed/<str:camera_id>/', views.video_feed, name='video_feed'),
    path('api/detections/', views.get_recent_detections, name='get-recent-detections'),
    path('detections/', views.recent_detections, name='recent-detections'),
    path('edit-camera/<int:id>/', views.edit_camera, name='edit-camera'),
    path('delete-camera/<int:id>/', views.delete_camera, name='delete-camera'),
]
