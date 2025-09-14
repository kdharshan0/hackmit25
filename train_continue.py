from ultralytics import YOLO

# Load a model
model = YOLO("runs/pose/train/weights/last.pt") # load a pretrained model (recommended for training)

# Train the model
results = model.train(resume=True)