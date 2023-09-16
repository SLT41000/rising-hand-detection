from ultralytics import YOLO
import cv2
import numpy as np
import config
from server_cam import CustomSocketIOServer
import time


class temi_hand_dectecter:
    
    
    def __init__(self,  cam=0, hand_raise_threshold=0,ip="",port="",connection=True):
        self.hand_raise_threshold= hand_raise_threshold
        self.model_pose = YOLO('yolov8n-pose.pt')  # for detect pose
        self.cap = cv2.VideoCapture(cam)
        self.table_centers = []
        self.table_queue=[]
        self.connection=CustomSocketIOServer(ip=ip,port=port)
        self.dot_locations = []  
        self.pre_locations=[]
        self.drawing = False
        self.start_x, self.start_y = -1, -1
        self.end_x, self.end_y = -1, -1
        self.pre_locations=None
        self.last_append=0
        

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
    
    
    def label_person(self,result_pose,annotated_frame):
        #การใช้ pose_est ในการการคำนวนจาก keypoint มีข้อเสียที่คิดไว้คือ มันต้องใช้มุมที่เห็นคนตรงสรีระเท่านั้นเพื่อไม้ให้ค่า keypoint ที่คำนวนผิดพลาด
        #แล้วใช้มุมแบบ top view ไม่ได้ เพราะค่า xy ที่ได้จะจากข้อมือกับค่าที่ได้จากไหล่จะบอกไม่ได้ว่ามืออยู่สูงกว่าไหล่รึป่าว
        if(result_pose[0].keypoints.conf==None):
            return
        conf=result_pose[0].keypoints.conf.cpu().numpy()
        result_keypoints = result_pose[0].keypoints.xyn.cpu().numpy()
        print(conf[0][9:11])
        current_time = time.time()
        for i, box in enumerate(result_pose[0].boxes.xyxy): #check pose person who raising hand
            if np.any(conf[i][9:11]<0.25) or np.any(conf[i][5:7]<0.25):
                continue
            # Extract keypoint coordinates for wrists
            left_wrist = result_keypoints[i][9][:2]
            right_wrist = result_keypoints[i][10][:2]
            # Define a threshold for hand raising
            left_shoulder = result_keypoints[i][5][:2]
            right_shoulder = result_keypoints[i][6][:2]

            # Calculate the Y-coordinates of wrists and shoulders
            left_wrist_y = left_wrist[1]
            right_wrist_y = right_wrist[1]
            left_shoulder_y = left_shoulder[1]
            right_shoulder_y = right_shoulder[1]
            
            
            # Define a threshold for hand raise in relation to the shoulder
            self.hand_shoulder_threshold = 0 # You can adjust this threshold as needed
            
            # Check if both wrists are above their respective shoulders
            if (left_wrist_y+self.hand_shoulder_threshold < left_shoulder_y or right_wrist_y+self.hand_shoulder_threshold < right_shoulder_y) and  (left_shoulder_y <= 0.9 or right_shoulder_y  <=0.9):
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
                        
                if nearest_dot is not None and nearest_dot not in self.table_queue and (nearest_dot != self.pre_locations or current_time - self.last_append>= 5):
                    self.table_queue.append(nearest_dot)
                    self.last_append = current_time
    
    def label_zone(self,annotated_frame):
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
    
    def start(self):
        
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        while self.cap.isOpened():
            success, frame = self.cap.read()
            cv2.namedWindow("YOLOv8")
            cv2.setMouseCallback("YOLOv8", self.on_mouse_click)
            if success:
                
                result_pose = self.model_pose(frame)
                annotated_frame = frame.copy()  # Create a copy of the frame for annotation
                
                self.label_person(result_pose,annotated_frame)

                self.label_zone(annotated_frame)
                print(self.table_queue)  
                print(self.connection.status)     
                print(self.dot_locations)
                if(self.connection.status=='IDLE' and len(self.table_queue)!=0):
                    self.pre_locations=self.table_queue.pop(0)
                    self.connection.location_from_cam(self.pre_locations)
                    
                cv2.imshow("YOLOv8", annotated_frame)
                
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.cap.release()
                    cv2.destroyAllWindows()
                    self.connection.stop_server()
                    break
            else:
                break


if __name__ == '__main__':
    test = temi_hand_dectecter(ip=config.SERVER_SOCKET_IPV4,port=config.SERVER_SOCKET_PORT,cam=0)
    test.start()