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
    
def play_chord(notes, duration=0.5, velocity=100):
    def worker():
        for note in notes:
            fs.noteon(0, note, velocity)
        time.sleep(duration)
        for note in notes:
            fs.noteoff(0, note)
    threading.Thread(target=worker, daemon=True).start()

def is_hand_open(kpts):
    # kpts shape: (num_keypoints, 2)
    wrist_x, wrist_y = kpts[0]  # wrist
    fingertip_ids = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky
    
    dists = []
    for i in fingertip_ids:
        if i < len(kpts):
            fx, fy = kpts[i]
            dists.append(((fx - wrist_x)**2 + (fy - wrist_y)**2)**0.5)
    avg_dist = sum(dists) / len(dists)
    # print("Avg dist:", avg_dist)
    return avg_dist > 300

# Load your trained model
model = YOLO("runs/pose/train/weights/best.pt")

# RTMP stream URL from MediaMTX
rtmp_url = "rtmp://localhost:1935/s/streamKey"
cap = cv2.VideoCapture(rtmp_url)

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
            
            # Check if index finger tip exists
            if len(kpts) > 20 and is_hand_open(kpts):
                play_chord([60, 64, 67], duration=1.0)
        
        # Display locally
        cv2.imshow("YOLO Overlay", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
