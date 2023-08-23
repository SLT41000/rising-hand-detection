from ultralytics import YOLO
import cv2
import numpy as np

# Load a model_pose
model_pose = YOLO('yolov8n-pose.pt')  # for detect pose
model_detect = YOLO('yolov8n.pt')  # for detect table
model_detect.predict( save=True, classes=[60])
cap = cv2.VideoCapture(0)
left_wrist_idx = 9
right_wrist_idx = 10
result_object=None
table_centers = []
table_queue=[]
hand_raise_threshold = 0.3  # Adjust this value as needed

while cap.isOpened():
    success, frame = cap.read()
    
    if success:
        
        
        result_object = model_detect(frame)
            
        
        
        cv2.imshow("YOLOv8",result_object[0].plot())
        
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        break

cap.release()
cv2.destroyAllWindows()
