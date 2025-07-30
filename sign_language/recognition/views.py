from django.shortcuts import render
from django.http import JsonResponse
import os
import json
import cv2
import mediapipe as mp
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse
import numpy as np

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

    # Lưu dữ liệu vào file JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(frame_data, f, indent=2)

    # Ghi đè file hand_keypoints.json ở thư mục gốc project
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hand_keypoints_path = os.path.join(base_dir, 'hand_keypoints.json')
    with open(json_path, 'r', encoding='utf-8') as src, open(hand_keypoints_path, 'w', encoding='utf-8') as dst:
        dst.write(src.read())

def upload_view(request):
    if request.method == 'POST' and request.FILES.get('video_file'):
        video = request.FILES['video_file']
        fs = FileSystemStorage()
        video_path = fs.save(video.name, video)
        video_full_path = os.path.join(settings.MEDIA_ROOT, video_path)

        # Lấy tên file video, đổi đuôi sang .json
        base_name = os.path.splitext(video.name)[0]
        json_filename = base_name + '.json'
        json_path = os.path.join(settings.MEDIA_ROOT, json_filename)
        extract_hand_landmarks(video_full_path, json_path)

        return render(request, 'upload.html', {
            'message': f'✅ Phân tích hoàn tất! Dữ liệu đã lưu vào {json_filename}',
            'show_simulation': True,
            'json_url': f'/download-hand-keypoints/?filename={json_filename}'
        })
    return render(request, 'upload.html', {'show_simulation': False})

# def hand_keypoints_api(request):
#     base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     json_path = os.path.join(base_dir, 'hand_keypoints.json')
#     with open(json_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)
#     return JsonResponse({'frames': data})
def hand_keypoints_api(request):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, 'hand_keypoints.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    frames = []
    width, height = 640, 480  # canvas size
    for frame in data:
        points = []
        for lm in frame['landmarks']:
            # Chuyển từ giá trị chuẩn hóa sang pixel
            x = lm['x'] * width
            y = lm['y'] * height
            points.append([x, y])
        if points:  # chỉ thêm frame có đủ landmark
            frames.append(points)
    return JsonResponse({'frames': frames})

def hand_simulation_view(request):
    return render(request, 'hand_simulation.html')

def export_hand_video(request):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, 'hand_keypoints.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    width, height = 640, 480
    fps = 20
    video_path = os.path.join(settings.MEDIA_ROOT, 'hand_simulation.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
    # Định nghĩa màu sắc các ngón tay
    finger_colors = [
        (231, 76, 60),    # thumb - đỏ
        (241, 196, 15),   # index - vàng
        (46, 204, 113),   # middle - xanh lá
        (52, 152, 219),   # ring - xanh dương
        (155, 89, 182)    # pinky - tím
    ]
    palm_color = (85, 85, 85)
    # Định nghĩa connections
    finger_connections = [
        [[0,1],[1,2],[2,3],[3,4]],
        [[0,5],[5,6],[6,7],[7,8]],
        [[0,9],[9,10],[10,11],[11,12]],
        [[0,13],[13,14],[14,15],[15,16]],
        [[0,17],[17,18],[18,19],[19,20]]
    ]
    palm_connections = [[0,5],[5,9],[9,13],[13,17],[17,0]]
    for frame in data:
        points = []
        for lm in frame['landmarks']:
            x = int(lm['x'] * width)
            y = int(lm['y'] * height)
            points.append((x, y))
        img = 255 * np.ones((height, width, 3), dtype=np.uint8)
        if len(points) == 21:
            # Vẽ connections cho từng ngón tay
            for i, conns in enumerate(finger_connections):
                color = finger_colors[i]
                for start, end in conns:
                    cv2.line(img, points[start], points[end], color, 3)
            # Vẽ connections lòng bàn tay
            for start, end in palm_connections:
                cv2.line(img, points[start], points[end], palm_color, 2)
            # Vẽ các điểm của từng ngón tay
            for i, finger in enumerate(finger_connections):
                color = finger_colors[i]
                for idx in [c[1] for c in finger]:
                    cv2.circle(img, points[idx], 6, color, -1)
            # Vẽ điểm cổ tay
            cv2.circle(img, points[0], 7, palm_color, -1)
        out.write(img)
    out.release()
    return FileResponse(open(video_path, 'rb'), as_attachment=True, filename='hand_simulation.mp4')

def download_hand_keypoints(request):
    filename = request.GET.get('filename', 'hand_keypoints.json')
    json_path = os.path.join(settings.MEDIA_ROOT, filename)
    if not os.path.exists(json_path):
        from django.http import Http404
        raise Http404('File not found')
    return FileResponse(open(json_path, 'rb'), as_attachment=True, filename=filename)

