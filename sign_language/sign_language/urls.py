"""
URL configuration for sign_language project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls.py import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls.py'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from recognition.views import upload_view, hand_keypoints_api, hand_simulation_view, export_hand_video

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', upload_view, name='upload'),  # Trang: upload video
    path('hand-keypoints-api/', hand_keypoints_api, name='hand_keypoints_api'),
    path('hand-simulation/', hand_simulation_view, name='hand_simulation'),
    path('export-hand-video/', export_hand_video, name='export_hand_video'),
]

# Cho phép truy cập file media (video tải lên) trong quá trình dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

