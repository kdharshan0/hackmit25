import cv2
from ultralytics import YOLO
import fluidsynth, time
import threading


# Initialize synthesizer
fs = fluidsynth.Synth()
fs.start(driver="coreaudio")
sfid = fs.sfload("Piano.sf2")
fs.program_select(0, sfid, 0, 0)

def play_midi_note_async(note=72, duration=0.5, velocity=100):
    def worker():
        fs.noteon(0, note, velocity)
        time.sleep(duration)
        fs.noteoff(0, note)
    threading.Thread(target=worker, daemon=True).start()

# Load your trained model
model = YOLO("runs/pose/train/weights/best.pt")

# RTMP stream URL from MediaMTX
rtmp_url = "rtmp://localhost:1935/s/streamKey"
cap = cv2.VideoCapture(rtmp_url)

start_time = time.time()

frame_count = 0
print_interval = 30  # print every 30 frames

if not cap.isOpened():
    print("Error: Could not open RTMP stream")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Run YOLO on the frame
    results = model(frame)

    for result in results:
        annotated_frame = result.plot()
        
        # Check if keypoints exist
        if hasattr(result, 'keypoints') and result.keypoints is not None:
            # Get keypoints
            kpts = result.keypoints.xy[0].cpu().numpy()
            
            # Index finger tip is usually keypoint 8 (adjust if needed)
            INDEX_FINGER_TIP = 8
            
            # Check if index finger tip exists
            if len(kpts) > INDEX_FINGER_TIP:
                tip_x, tip_y = kpts[INDEX_FINGER_TIP]
                
                # If coordinates are not zero, finger tip is detected
                if tip_x > 0 and tip_y > 0:
                    play_midi_note_async(72)
                    # print("Index finger tip detected!")
        
        # Display locally
        cv2.imshow("YOLO Overlay", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
