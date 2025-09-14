import cv2
from ultralytics import YOLO
import fluidsynth, time
import threading
import math

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
    index_tip, pinky_tip, wrist = kpts[8], kpts[20], kpts[1]

    finger_dist = ((index_tip[0] - pinky_tip[0])**2 + (index_tip[1] - pinky_tip[1])**2)**0.5
    wrist_to_index = ((index_tip[0] - wrist[0])**2 + (index_tip[1] - wrist[1])**2)**0.5
    wrist_to_pinky = ((pinky_tip[0] - wrist[0])**2 + (pinky_tip[1] - wrist[1])**2)**0.5

    print("Finger dist:", finger_dist, "Wrist to Index:", wrist_to_index, "Wrist to Pinky:", wrist_to_pinky)

    return finger_dist < 250 and wrist_to_index > 175 and wrist_to_pinky < 250   

def normalize_hand_dist(kpts):
    index_palm, middle_palm, ring_palm = kpts[5], kpts[9], kpts[13]

    finger_avg = (index_palm[1] + middle_palm[1] + ring_palm[1]) / 3

    print("Finger avg:", finger_avg)
    
    return finger_avg

def clef(kpts):
    clef_notes = {
        700: 72,
        660: 74,
        620: 76,
        580: 77,
        540: 79,
        500: 81,
        460: 83,
        420: 84,
        380: 86,
        340: 88,
        300: 89
    }

    position = normalize_hand_dist(kpts)

    key = get_floor_key(position, clef_notes.keys())
    if key is not None:
        play_midi_note_async(clef_notes[key], duration=0.5)
    
    print("Position:", position)

def getChord(kpts):
    clef_chords = {
        700: [60, 64, 67],   # C major (C4, E4, G4)
        660: [62, 65, 69],   # D minor (D4, F4, A4)
        620: [64, 67, 71],   # E minor (E4, G4, B4)
        580: [65, 69, 72],   # F major (F4, A4, C5)
        540: [67, 71, 74],   # G major (G4, B4, D5)
        500: [69, 72, 76],   # A minor (A4, C5, E5)
        460: [71, 74, 77],   # B diminished (B4, D5, F5)
        420: [72, 76, 79],   # C major (C5, E5, G5)
        380: [74, 77, 81],   # D minor (D5, F5, A5)
        340: [76, 79, 83],   # E minor (E5, G5, B5)
        300: [77, 81, 84]    # F major (F5, A5, C6)
    }      


    position = normalize_hand_dist(kpts)

    position = normalize_hand_dist(kpts)
    key = get_floor_key(position, clef_chords.keys())

    if key is not None:
        play_chord(clef_chords[key], duration=1.0)



def get_floor_key(value, keys):
    """Return the largest key <= value, or None if no such key exists."""
    keys = sorted(keys, reverse=True)
    for k in keys:
        if value >= k:
            return k
    return None

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


            if len(kpts) > 20 and is_hand_L(kpts):
                #play_midi_note_async(72)  # C4
                print(clef(kpts))

            elif len(kpts) > 20 and is_hand_open(kpts):
                # play_midi_note_async(72)  # C5
                #play_chord([60, 64, 67], duration=1.0)  # C4, E4, G4
                print(getChord(kpts))

            # if len(kpts) > 20:
            #     print(normalize_hand_dist(kpts))
            #     print(clef(kpts))


        cv2.imshow("Pose Piano", annotated_frame)
        
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
