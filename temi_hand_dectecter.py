from ultralytics import YOLO
import cv2
import numpy as np
import config
import time
from client_cam import ClientCam
import math

class temi_hand_dectecter:
    def __init__(self,  cam=0, ip:str="",port:str="",connection:bool=True,range:int=0)->None:
        self.model_pose = YOLO('yolov8n-pose.pt')  # for detect pose
        self.cap = cv2.VideoCapture(cam)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.connection=ClientCam(ip=ip,port=str(port),connection=connection)
        self.drawing = False
        self.start_x, self.start_y = -1, -1
        self.end_x, self.end_y = -1, -1
        self.pre_locations=None
        self.last_append=0
        self.last_update=0
        self.window_name="hand detector"
        self.max_in_range_table=range
    
    
    def on_mouse_click(self, event, x, y, flags, param):
        #handle del dot_location on right chick
        if event == cv2.EVENT_RBUTTONDOWN :
            self.right_c_event([x,y])
            return
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
                if(self.end_x<self.start_x and self.start_y > self.end_y):
                    up_left =[self.end_x,self.end_y]
                    down_right = [self.start_x,self.start_y]
                elif(self.end_x<self.start_x and self.start_y <self.end_y):
                    up_left = [self.end_x, self.start_y]
                    down_right = [self.start_x, self.end_y]
                elif(self.start_y>self.end_y and self.end_x>self.start_x):
                    up_left =[self.start_x,self.end_y]
                    down_right = [self.end_x,self.start_y]
                else:#up_left on a left top rectangle down_right is on the right down
                    up_left =[self.start_x,self.start_y]
                    down_right = [self.end_x,self.end_y]
                self.connection.push_table_data(up_left, down_right, square_size)
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
                hand_location = person_center
                self.nearest_table(hand_location)
                
    def right_c_event(self,xy):
        self.connection.del_table(xy)
    
    def distant_of_2dot(self, xy: np,index:list):
        nearest_dot = None
        min_distance = float('inf')  # Initialize minimum distance to a very large value
        for left_upper, right_lower, square_size, dot_name in self.connection.table_data:
            tmp_upper = left_upper - self.max_in_range_table
            tmp_lower = right_lower + self.max_in_range_table
            left, upper = tmp_upper
            right, lower = tmp_lower

            # Calculate the center of the current dot's location
            dot_center = [(left + right) / 2, (upper + lower) / 2]

            # Calculate the distance between the hand location and the center of the dot
            distance = np.linalg.norm(xy - dot_center)
                # Check if the current dot is closer than the previously found nearest dot
            if distance < min_distance:
                min_distance = distance
                nearest_dot = dot_name
        return nearest_dot
    
    def nearest_table(self,hand_location ):
        nearest_dot = None
        current_time = time.time()
        for i,(left_upper, right_lower, square_size,name) in enumerate(self.connection.table_data):
            tmp_upper=left_upper
            tmp_lower=right_lower
            left, upper = tmp_upper
            right, lower = tmp_lower 
            # Check if hand_location is within the rectangle
            if left <= hand_location[0] <= right and upper <= hand_location[1] <= lower:
                nearest_dot = name
        if nearest_dot is not None  and (nearest_dot != self.pre_locations or current_time - self.last_append>= 10):
            self.connection.append_queue(nearest_dot)
            self.last_append = current_time
        elif nearest_dot ==None:
            self.connection.append_queue("HOMEBASE")
    
    def label_zone(self,annotated_frame):
        for i,(up, down, square_size,name) in enumerate(self.connection.table_data):
            cv2.rectangle(annotated_frame, (up[0], up[1]), (down[0],down[1]), (0, 255, 0), 2)
            cv2.putText(
                annotated_frame,
                name,
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
                name,
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
        
    def print_data(self):
        current_time = time.time()
        if(current_time-self.last_update>1):
            self.connection.get_data()
            self.last_update=current_time

    def start(self):
        cv2.namedWindow(self.window_name)
        cv2.namedWindow("keypoint")
        cv2.setMouseCallback(self.window_name, self.on_mouse_click)
        while self.cap.isOpened():
            success, frame = self.cap.read()
            if success:
                result_pose = self.model_pose(frame, verbose=False)
                annotated_frame = frame.copy()
                self.print_data()
                self.label_person(result_pose, annotated_frame)
                self.label_zone(annotated_frame)
                cv2.imshow(self.window_name, annotated_frame)
                cv2.imshow("keypoint", result_pose[0].plot())
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                break

        self.cap.release()
        cv2.destroyAllWindows()
        self.connection.disconnect()

            
     
if __name__ == '__main__':
    test = temi_hand_dectecter(ip=config.SERVER_SOCKET_IPV4,port=config.SERVER_SOCKET_PORT,cam=0,connection=True)
    test.start()