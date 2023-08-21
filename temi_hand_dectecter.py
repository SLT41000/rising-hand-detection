from ultralytics import YOLO
import cv2
import numpy as np
from client_cam import setup_connection

class temi_hand_dectecter:
    
    
    def __init__(self,  cam=0, hand_raise_threshold=0.3,ip="",port=""):
        self.cam = cam
        self.hand_raise_threshold= hand_raise_threshold
        self.model_pose = YOLO('yolov8n-pose.pt')  # for detect pose
        self.model_detect = YOLO('yolov8n.pt')  # for detect table
        self.model_detect.predict( save=True, classes=[60])
        self.cap = cv2.VideoCapture(self.cam)
        self.left_wrist_idx = 9
        self.right_wrist_idx = 10
        self.result_object=None
        self.table_centers = []
        self.table_queue=[]
        self.ip=ip
        self.port=port
        
    
    def start(self):
        connection = setup_connection(self.ip,self.port)
        connection.connect()
        while self.cap.isOpened():
            success, frame = self.cap.read()
            
            if success:
                print(self.table_queue)
                result_pose = self.model_pose(frame)
                if(self.result_object==None):
                    self.result_object = self.model_detect(frame)
                    
                    for box in self.result_object[0].boxes.xyxy:
                        xmin, ymin, xmax, ymax = box
                        table_center = ((xmin + xmax) / 2, (ymin + ymax) / 2)
                        self.table_centers.append(table_center)
            
                
                result_keypoints = result_pose[0].keypoints.xyn.cpu().numpy()
                annotated_frame = frame.copy()  # Create a copy of the frame for annotation
                
                for i, box in enumerate(result_pose[0].boxes.xyxy): #check pose person who raising hand
                    
                    # Extract keypoint coordinates for wrists
                    left_wrist = result_keypoints[i][self.left_wrist_idx][:2]
                    right_wrist = result_keypoints[i][self.right_wrist_idx][:2]
                    # Define a threshold for hand raising
                    
                    
                    # Check if the y-coordinate of either wrist is above the threshold
                    if left_wrist[1] < self.hand_raise_threshold or right_wrist[1] < self.hand_raise_threshold:
                        # Draw bounding box and annotate the frame with the hand raise message
                        xmin, ymin, xmax, ymax = box
                        person_center = ((xmin + xmax) / 2, (ymin + ymax) / 2)
                        cv2.rectangle(annotated_frame, (int(xmin), int(ymin)), (int(xmax), int(ymax)), (0, 255, 0), 2)
                        cv2.putText(
                            annotated_frame,
                            "Hand Raised",
                            (int(xmin), int(ymin) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 0),
                            2,
                            cv2.LINE_AA,
                        )
                        hand_location = np.array(person_center)
                        distances = [np.linalg.norm(hand_location - np.array(table_center)) for table_center in self.table_centers]
                        
                        # Find the index of the nearest table
                        if(len(distances)!=0):
                            nearest_table_idx = np.argmin(distances)
                            if(nearest_table_idx not in self.table_queue):
                                self.table_queue.append(nearest_table_idx)
                if(connection.temi_stat=='idle' and len(self.table_queue)!=0):
                    connection.sentlocation(nearest_table_idx)
                    
                    self.table_queue.pop(0)
                
                                
                                    
                    
                        

                
                cv2.imshow("YOLOv8", annotated_frame)
                
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    connection.disconnect()
                    break
            else:
                break

        self.cap.release()
        cv2.destroyAllWindows()




