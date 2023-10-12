from ultralytics import YOLO
import cv2
import numpy as np
import config
from server_cam import CustomSocketIOServer
import time
from client_cam import client_cam
import math

class temi_hand_dectecter:

    def __init__(self,  cam=0, ip:str="",port:str="",connection:bool=True,range:int=40)->None:
        self.model_pose = YOLO('yolov8n-pose.pt')  # for detect pose
        self.cap = cv2.VideoCapture(cam)
        self.table_queue=[]
        self.connection=client_cam(ip=ip,port=str(port),connection=connection)
        self.dot_locations = []  
        self.drawing = False
        self.start_x, self.start_y = -1, -1
        self.end_x, self.end_y = -1, -1
        self.pre_locations=None
        self.last_append=0
        self.window_name="hand detector"
        self.max_in_range_table=range
        
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
                if(self.end_x<self.start_x and self.start_y > self.end_y):
                    up_left =np.array([self.end_x,self.end_y])
                    down_right = np.array([self.start_x,self.start_y])
                elif(self.end_x<self.start_x and self.start_y <self.end_y):
                    up_left = np.array([self.end_x, self.start_y])
                    down_right = np.array([self.start_x, self.end_y])
                elif(self.start_y>self.end_y and self.end_x>self.start_x):
                    up_left =np.array([self.start_x,self.end_y])
                    down_right = np.array([self.end_x,self.start_y])
                else:#up_left on a left top rectangle down_right is on the right down
                    up_left =np.array([self.start_x,self.start_y])
                    down_right = np.array([self.end_x,self.end_y])
                self.dot_locations.append((up_left, down_right, square_size, square_name))
                self.drawing = False
    
    def calculate_person_size(self, box):
    # Calculate the width and height of the bounding box
        xmin, ymin, xmax, ymax = box
        width = xmax - xmin
        height = ymax - ymin
        size_in_pixels = width * height
        return size_in_pixels
    
    def label_person(self,result_pose,annotated_frame):
        #การใช้ pose_est ในการการคำนวนจาก keypoint มีข้อเสียที่คิดไว้คือ มันต้องใช้มุมที่เห็นคนตรงสรีระเท่านั้นเพื่อไม้ให้ค่า keypoint ที่คำนวนผิดพลาด
        #แล้วใช้มุมแบบ top view ไม่ได้ เพราะค่า xy ที่ได้จะจากข้อมือกับค่าที่ได้จากไหล่จะบอกไม่ได้ว่ามืออยู่สูงกว่าไหล่รึป่าว
        if(result_pose[0].keypoints.conf==None):
            return
        conf=result_pose[0].keypoints.conf.cpu().numpy()
        result_keypoints = result_pose[0].keypoints.xyn.cpu().numpy()
        for i, box in enumerate(result_pose[0].boxes.xyxy): #check pose person 
            if np.any(conf[i][5:11]<0.25):
                continue
            left_wrist = result_keypoints[i][9][:2]
            right_wrist = result_keypoints[i][10][:2]
            left_shoulder = result_keypoints[i][5][:2]
            right_shoulder = result_keypoints[i][6][:2]
            left_elbow = result_keypoints[i][7][:2]
            right_elbow = result_keypoints[i][8][:2]
            try:
                l_degree=self.find_degree(left_shoulder[0],left_elbow[0],left_wrist[0],left_shoulder[1],left_elbow[1],left_wrist[1])
                r_degree=self.find_degree(right_shoulder[0],right_elbow[0],right_wrist[0],right_shoulder[1],right_elbow[1],right_wrist[1])
            except:
                continue
            self.degree_thhold=20
            if ((left_wrist[1] < left_shoulder[1])and l_degree<self.degree_thhold) or ((right_wrist[1] < right_shoulder[1] )and r_degree<self.degree_thhold) :
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
                self.nearest_table(hand_location)

    def nearest_table(self,hand_location):
        nearest_dot = None
        current_time = time.time()
        for left_upper, right_lower, square_size, dot_name in self.dot_locations:
            tmp_upper=left_upper-self.max_in_range_table
            tmp_lower=right_lower+self.max_in_range_table
            left, upper = tmp_upper
            right, lower = tmp_lower
            # Check if hand_location is within the rectangle
            if left <= hand_location[0] <= right and upper <= hand_location[1] <= lower:
                nearest_dot = dot_name
                if nearest_dot is not None  and (nearest_dot != self.pre_locations or current_time - self.last_append>= 10):
                    self.connection.sentlocation(nearest_dot)
                    self.pre_locations=nearest_dot
                    self.last_append = current_time
            """ else:
                # Calculate the minimum distance from the hand_location to the edges of the rectangle
                distance_to_left = max(left - hand_location[0], 0)
                distance_to_right = max(hand_location[0] - right, 0)
                distance_to_upper = max(upper - hand_location[1], 0)
                distance_to_lower = max(hand_location[1] - lower, 0)

                # Find the minimum of these distances
                min_distance = min(distance_to_left, distance_to_right, distance_to_upper, distance_to_lower) """
    
    def label_zone(self,annotated_frame):
        for up, down, square_size, dot_name in self.dot_locations:
            cv2.rectangle(annotated_frame, (up[0], up[1]), (down[0],down[1]), (0, 255, 0), 2)
            cv2.putText(
                annotated_frame,
                dot_name,
                (int((up[0]+down[0])/2), int((up[1]+down[1])/2) ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.rectangle(annotated_frame, (up[0]-self.max_in_range_table, up[1]-self.max_in_range_table), (down[0]+self.max_in_range_table, down[1]+self.max_in_range_table), (0, 0, 255), 2)
            cv2.putText(
                annotated_frame,
                dot_name,
                (int((up[0]+down[0])/2), int((up[1]+down[1])/2) ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )


    def find_degree(self,xA,xB,x4,yA,yB,y4):
        ABx = xB - xA
        ABy = yB - yA
        BCx = x4 - xB
        BCy = y4 - yB
        dot_product = ABx * BCx + ABy * BCy
        magnitude_AB = math.sqrt(ABx**2 + ABy**2)
        magnitude_BC = math.sqrt(BCx**2 + BCy**2)
        cos_theta = dot_product / (magnitude_AB * magnitude_BC)
        angle_degrees = math.degrees(math.acos(cos_theta))
        return angle_degrees
        
        
    def start(self):
        
        while self.cap.isOpened():
            success, frame = self.cap.read()
            cv2.namedWindow(self.window_name)
            cv2.namedWindow("keypoint")
            cv2.setMouseCallback(self.window_name, self.on_mouse_click)
            if success:
                result_pose = self.model_pose(frame)
                annotated_frame = frame.copy()
                self.label_person(result_pose,annotated_frame)
                self.label_zone(annotated_frame)
                self.connection.get_queue_data()
                print(f"Table Location = {self.dot_locations}")
                cv2.imshow(self.window_name, annotated_frame)
                cv2.imshow("keypoint",result_pose[0].plot())
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.cap.release()
                    cv2.destroyAllWindows()
                    self.connection.disconnect()
                    break
            else:
                break

            
     
if __name__ == '__main__':
    test = temi_hand_dectecter(ip=config.SERVER_SOCKET_IPV4,port=config.SERVER_SOCKET_PORT,cam=0)
    test.start()