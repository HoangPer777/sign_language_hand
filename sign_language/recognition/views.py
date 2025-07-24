from django.shortcuts import render

# handtracker/views.py
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os, json
import cv2
import mediapipe as mp

def extract_hand_landmarks(video_path, json_path):
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1)

    cap = cv2.VideoCapture(video_path)
    frame_data = []
    frame_index = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        landmarks = []
        if results.multi_hand_landmarks:
            for lm in results.multi_hand_landmarks[0].landmark:
                landmarks.append({'x': lm.x, 'y': lm.y, 'z': lm.z})

        frame_data.append({
            'frame_index': frame_index,
            'landmarks': landmarks
        })
        frame_index += 1

    cap.release()

    with open(json_path, 'w') as f:
        json.dump(frame_data, f, indent=2)

def upload_view(request):
    if request.method == 'POST' and request.FILES.get('video_file'):
        video = request.FILES['video_file']
        fs = FileSystemStorage()
        video_path = fs.save(video.name, video)
        video_full_path = os.path.join(settings.MEDIA_ROOT, video_path)

        json_path = os.path.join(settings.BASE_DIR, 'hand_keypoints.json')
        extract_hand_landmarks(video_full_path, json_path)

        return render(request, 'upload.html', {'message': '✅ Phân tích hoàn tất! Dữ liệu đã lưu vào hand_keypoints.json'})

    return render(request, 'upload.html')

