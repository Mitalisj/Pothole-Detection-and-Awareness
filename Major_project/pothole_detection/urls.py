from django.contrib import admin
from django.urls import path, include
from pothole_detection import views
urlpatterns = [
    path("", views.main, name="main"),
    path("upload_image/", views.upload_image, name="upload_image"),
     path('display_map/', views.display_map, name='display_map'), 
     path('aboutus/', views.about_us, name ="aboutus")
]