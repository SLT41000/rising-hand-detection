import eventlet
import socketio 
import numpy as np
import threading
import config
from eventlet import wsgi
import time
class CustomSocketIOServer:
    def __init__(self,ip,port):
        self.sio = socketio.Server()
        self.app = socketio.WSGIApp(self.sio, static_files={
            '/': {'content_type': 'text/html', 'filename': 'index.html'}
        })
        self.status = "IDLE"
        self.queue=[]
        self.table = [] 
        self.last_append=0
        self.idle_time=0
        self.location = None
        self.cur_location="homebase"
        self.cout=0
        self.setup_events()
        self.server=threading.Thread(target=self.start_server, args=(ip, port))
        self.server.start()

    def setup_events(self):
        #temi_event
        @self.sio.event
        def move_to(sid):
            if(self.cur_location==None):
               return
            self.sio.emit("receiver_goto_dest", self.cur_location)
    
        @self.sio.event
        def receiver_moving_status(sid, data):
            print(data)
            if data == "complete":
                self.sio.emit("sender_location")

        
        
        #cam_event
        #del for del right chick on client
        @self.sio.event
        def del_table(sid,xy,input_cam_id):
            nearest_index = None
            for index, (left_upper, right_lower, square_size, cam_id) in  enumerate(self.table):
                if(cam_id==input_cam_id):
                    left, upper = left_upper
                    right, lower = right_lower
                    if left <= xy[0] <= right and upper <= xy[1] <= lower:
                        nearest_index = index
            if nearest_index is not None:
                self.table.pop(nearest_index)
            self.sio.emit("event_update_table")

        #for insert queue
        @self.sio.event
        def append_queue(sid,table_name : str):
            current_time = time.time()
            if(table_name not in self.queue and (self.cur_location!=table_name or current_time - self.last_append>= 10)):
                self.last_append=current_time
                self.cur_location=table_name
                self.queue.append(table_name)
            self.pop_queue()
        
        #for insert table
        @self.sio.event
        def append_table(sid,up_left, down_right, square_size,name):
            if(up_left, down_right, square_size,name!=None):
                self.table.append((up_left, down_right, square_size,name))
            self.sio.emit("event_update_table")
        
        #for get table list to send to client
        @self.sio.event
        def get_table(sid,input_cam_id:int)->list:
            tmp_list=[]
            for i,(left_upper, right_lower, square_size, cam_id) in enumerate(self.table):
                if(input_cam_id==cam_id):
                    tmp_list.append((left_upper, right_lower, square_size,str(i+1)))
            self.sio.emit("update_table",tmp_list)
        
        #for del table on disconnect camera
        @self.sio.event
        def cam_disconnect(sid,input_cam_id:int)->list:
            tmp_list=[]
            for i,(left_upper, right_lower, square_size, cam_id) in enumerate(self.table):
                if(input_cam_id!=cam_id):
                    tmp_list.append(self.table[i])
            self.table=tmp_list
                
        #use for tami to update server that tami is ready
        @self.sio.event
        def on_ready(sid, data):
            print(data)
            if data == "ready":
                self.status="IDLE"
                self.pop_queue()
        
        
        
        @self.sio.event
        def connect(sid, environ):
            print('connect ', sid)
            

        @self.sio.event
        def response(sid, data):
            if(data=="on_ready"):
                self.sio.emit("on_ready")
                

        @self.sio.event
        def disconnect(sid):
            print('disconnect ', sid)

        @self.sio.event
        def receiver_location(sid, data):
            self.location = data
        
        #get std data want to show on client
        @self.sio.event
        def get_data(sid):
            txt=f"Table Queue = {self.queue}\n{self.status}\nTable Location = {self.table}"
            self.sio.emit("update_data",txt)
                        
    def stop_server(self):
        self.server.join(timeout=1)
        
        
    def home_base(self):
        self.cur_location="homebase"
        print("Go Home Base")
        #self.status="BUSY"
        self.sio.emit("receiver_goto_dest","home base")
    
    #for send queue to temi
    def pop_queue(self):
        if(len(self.queue)!=0 and self.status=="IDLE"):
            location=self.queue.pop(0)
            self.cur_location=location
            print(f"send location {location}")
            self.status="BUSY"
            self.sio.emit("receiver_goto_dest", location)
        elif(len(self.queue)==0 and self.status=="IDLE" and self.cur_location!="homebase"):
            self.home_base()
            
            
    def start_server(self, host, port):
        eventlet.wsgi.server(eventlet.listen((host, port)), self.app)

        
        



if __name__ == '__main__':
    custom_server = CustomSocketIOServer(config.SERVER_SOCKET_IPV4, 5000) 
    
    
    

    
    
