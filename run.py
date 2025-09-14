from ultralytics import YOLO

YOLO('runs/pose/train/weights/best.pt').predict(source=0, show=True, save=True, project='runs/pose/output', name='tests')