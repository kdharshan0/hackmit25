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

def is_hand_L(kpts):
    index_tip, pinky_tip, wrist = kpts[8], kpts[20], kpts[0]

    finger_dist = ((index_tip[0] - pinky_tip[0])**2 + (index_tip[1] - pinky_tip[1])**2)**0.5
    wrist_to_index = ((index_tip[0] - wrist[0])**2 + (index_tip[1] - wrist[1])**2)**0.5
    wrist_to_pinky = ((pinky_tip[0] - wrist[0])**2 + (pinky_tip[1] - wrist[1])**2)**0.5

    print("Finger dist:", finger_dist, "Wrist to Index:", wrist_to_index, "Wrist to Pinky:", wrist_to_pinky)

    return finger_dist < 250 and wrist_to_index > 200 and wrist_to_pinky < 225    

model = YOLO("runs/pose/train/weights/best.pt")
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, stream=True)

    for result in results:
        annotated_frame = result.plot()
        
        # Check if keypoints exist
        if hasattr(result, 'keypoints') and result.keypoints is not None:
            # Get keypoints
            kpts = result.keypoints.xy[0].cpu().numpy()

            if len(kpts) > 20 and is_hand_open(kpts):
                # play_midi_note_async(72)  # C5
                play_chord([60, 64, 67], duration=1.0)  # C4, E4, G4

            elif len(kpts) > 20 and is_hand_L(kpts):
                play_midi_note_async(72)  # C4

        cv2.imshow("Pose Piano", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()