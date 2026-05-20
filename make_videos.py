import cv2
import os

images = {
    "video_q1.mp4": r"C:\Users\uzmam\.gemini\antigravity\brain\333398ec-fb3c-4e71-bb0c-6ce3f715cf07\video_scene_texting_1779207447108.png",
    "video_q2.mp4": r"C:\Users\uzmam\.gemini\antigravity\brain\333398ec-fb3c-4e71-bb0c-6ce3f715cf07\video_scene_sleepy_1779207461480.png",
    "video_q3.mp4": r"C:\Users\uzmam\.gemini\antigravity\brain\333398ec-fb3c-4e71-bb0c-6ce3f715cf07\video_scene_child_1779207481556.png",
    "video_q4.mp4": r"C:\Users\uzmam\.gemini\antigravity\brain\333398ec-fb3c-4e71-bb0c-6ce3f715cf07\video_scene_passenger_1779207494500.png",
    "video_q5.mp4": r"C:\Users\uzmam\.gemini\antigravity\brain\333398ec-fb3c-4e71-bb0c-6ce3f715cf07\video_scene_rain_1779207508843.png",
}

fps = 30
duration = 3 # seconds
frames_count = fps * duration

for filename, img_path in images.items():
    if not os.path.exists(img_path):
        print(f"File not found: {img_path}")
        continue

    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to read image: {img_path}")
        continue
    
    height, width, _ = img.shape
    
    out_path = os.path.join(r"d:\taxi_driver_eva_APP\backend\static\videos", filename)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, float(fps), (width, height))
    
    center_x, center_y = width / 2, height / 2

    # A subtle push-in/zoom animation
    for i in range(frames_count):
        # Scale goes from 1.0 to 1.15 over 3 seconds
        scale = 1.0 + (i / frames_count) * 0.15
        M = cv2.getRotationMatrix2D((center_x, center_y), 0, scale)
        zoomed = cv2.warpAffine(img, M, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        out.write(zoomed)
    
    out.release()
    print(f"Generated {filename}")

print("All videos generated successfully.")
