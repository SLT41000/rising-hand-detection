from ultralytics import YOLO
import cv2
import numpy as np
import client_cam
import math
class temi_hand_dectecter:
    
    
    def __init__(self,  cam=0, hand_raise_threshold=0.3,ip="",port="",connection=True):
        self.cam = cam
        self.hand_raise_threshold= hand_raise_threshold
        self.model_pose = YOLO('yolov8n-pose.pt')  # for detect pose
        self.cap = cv2.VideoCapture(self.cam)
        
        self.left_wrist_idx = 9
        self.right_wrist_idx = 10
        self.result_object=None
        self.table_centers = []
        self.table_queue=[]
        self.ip=ip
        self.port=port
        self.connection=connection
        self.dot_locations = []  # Initialize an empty list for dot locations
        
    
        self.drawing = False
        self.start_x, self.start_y = -1, -1
        self.end_x, self.end_y = -1, -1

    def on_mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_x, self.start_y = x, y
            self.end_x, self.end_y = x, y
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.end_x, self.end_y = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing:
                self.end_x, self.end_y = x, y
                square_size = max(abs(self.end_x - self.start_x), abs(self.end_y - self.start_y))
                square_name = str(len(self.dot_locations) + 1)
                center_x = (self.start_x + self.end_x) // 2
                center_y = (self.start_y + self.end_y) // 2
                self.dot_locations.append((center_x, center_y, square_size, square_name))
                self.drawing = False
    
    def start(self):
        
        client_cam.connect(self.ip,self.port)
        client_cam.temi_stat="IDLE"
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        while self.cap.isOpened():
            success, frame = self.cap.read()
            cv2.namedWindow("YOLOv8")
            cv2.setMouseCallback("YOLOv8", self.on_mouse_click)
            if success:
                
                result_pose = self.model_pose(frame)
                
            
                
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
                       
                        
                        nearest_dot = None
                        min_distance = float('inf')
                    
                        for x, y, square_size, dot_name in self.dot_locations:
                            
                            dot_center_x = x
                            dot_center_y = y
                            
                            
                            distance_to_dot = np.linalg.norm(hand_location - np.array((dot_center_x, dot_center_y)))
                            
                            if distance_to_dot < min_distance:
                                min_distance = distance_to_dot
                                nearest_dot = dot_name
                                
                            if nearest_dot not in self.table_queue:
                                self.table_queue.append(nearest_dot)
                                print(nearest_dot)

                
                for dot_x, dot_y, square_size, dot_name in self.dot_locations:
                    cv2.rectangle(annotated_frame, (int(dot_x - square_size/2), int(dot_y - square_size/2)), (int(dot_x + square_size/2), int(dot_y + square_size/2)), (0, 255, 0), 2)
                    cv2.putText(
                        annotated_frame,
                        dot_name,
                        (int(dot_x), int(dot_y) + 15),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                        cv2.LINE_AA,
                    )
                print(self.table_queue)  
                print(client_cam.temi_stat)     
                print(self.dot_locations)
                if(client_cam.temi_stat=='IDLE' and len(self.table_queue)!=0 ):
                    client_cam.sentlocation(self.table_queue.pop(0))

                        

                
                cv2.imshow("YOLOv8", annotated_frame)
                
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    client_cam.disconnect()
                    break
            else:
                break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    test = temi_hand_dectecter(ip="ipv4",port="5000")
    test.start()