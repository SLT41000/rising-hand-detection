import eventlet
import socketio 
import threading
import config
from eventlet import wsgi

class CustomSocketIOServer:
    def __init__(self,ip,port):
        self.sio = socketio.Server()
        self.app = socketio.WSGIApp(self.sio, static_files={
            '/': {'content_type': 'text/html', 'filename': 'index.html'}
        })
        self.location = None
        self.cur_location=None
        self.temi_status="IDLE"
        self.queue=[]
        self.setup_events()
        self.server=threading.Thread(target=self.start_server, args=(ip, port))
        self.server.start()

    def setup_events(self):
        #basic event
        @self.sio.event
        def connect(sid, environ):
            print('connect ', sid)
            self.sio.emit("response","hello")
            

        @self.sio.event
        def response(sid, data):
            print('message ', data)

        @self.sio.event
        def disconnect(sid):
            print('disconnect ', sid)

        
        
        #event for client_cam
        @self.sio.event
        def push_queue(sid,table_name : str):
            if(table_name not in self.queue):
                self.queue.append(table_name)
            self.pop_queue()
        
        @self.sio.event
        def location_from_cam(sid, location):
            print(f"send location {location}")
            self.cur_location = location
            self.sio.emit("receiver_goto_dest", location)
            
        @self.sio.event
        def get_data_queue(sid):
            self.sio.emit("rec_queue",f"Table Queue = {self.queue}\n{self.temi_status}")
        
        #event for temi-app
        @self.sio.event
        def move_to(sid):
            if(self.cur_location==None):
               return
            self.sio.emit("receiver_goto_dest", self.cur_location)
        
        @self.sio.event
        def receiver_moving_status(sid, data):
            print(data)
            if data == "complete":
                self.cur_location=None
                self.temi_status="IDLE"
                self.sio.emit("sender_location")
                self.pop_queue()

        @self.sio.event
        def receiver_location(sid, data):
            self.location = data
        
        
                        
    def stop_server(self):
        self.server.join(timeout=1)
        
    
    def pop_queue(self):
        if(len(self.queue)!=0 and self.temi_status=="IDLE"):
            location=self.queue.pop(0)
            print(f"send location {location}")
            self.cur_location = location
            self.temi_status="BUSY"
            self.sio.emit("receiver_goto_dest", location)

            
    def start_server(self, host, port):
        eventlet.wsgi.server(eventlet.listen((host, port)), self.app)

        
        



if __name__ == '__main__':
    custom_server = CustomSocketIOServer(config.SERVER_SOCKET_IPV4, 5000)
    
    
    

    
    
