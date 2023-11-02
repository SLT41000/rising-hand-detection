import socketio
import config
import numpy as np
class client_cam:
    cam_id=0
    def __init__(self,connection=True,ip=None,port=5000) -> None:
        self.cam_id=client_cam.cam_id
        client_cam.cam_id+=1
        self.table_data=[]
        self.connection= connection
        self.sio = socketio.Client()
        self.app = socketio.WSGIApp(self.sio, static_files={
            '/': {'content_type': 'text/html', 'filename': 'index.html'}
        })
        
        self.setup_events()
        self.connect(ip,port)
    
    def setup_events(self):
        @self.sio.on('connect')
        def on_connect():
            print('Connected to server')


        @self.sio.on('response')
        def on_response(data):
            print('Server response:', data)
        
        @self.sio.on('receiver_goto_dest')
        def on_response(data):
            print('Server response:', data)


                
        @self.sio.on('disconnect')
        def on_disconnect():
            print('Disconnected from server')
            
        @self.sio.on('event_update_table')
        def update_table():
            self.get_table_data()
        
        @self.sio.on('update_table')
        def update_table(data):
            if(data!=None):
                self.table_data=data
                
        @self.sio.on('update_data')
        def update_data(data):
            print(data)

    def connect(self,ip,port):
        if(self.connection==False):
            return "connection set false"
        self.sio.connect('http://'+ip+':'+port+'')
    
    def push_table_data(self,up_left, down_right, square_size):
        self.sio.emit("append_table",(up_left, down_right, square_size, self.cam_id))

    def disconnect(self):   
        if(self.connection==False):
            return "connection set false"
        self.sio.emit("cam_disconnect",self.cam_id)
        self.sio.disconnect()
        
    def append_queue(self,queue_name:str):
        if(queue_name=="HOMEBASE"):
            self.sio.emit('home_base')
            return
        self.sio.emit("append_queue",queue_name)
        
    def del_table(self,xy):
        self.sio.emit("del_table",(xy,self.cam_id))


    def get_table_data(self)->list:
        self.sio.emit("get_table",self.cam_id)

    def get_data(self):
        self.sio.emit("get_data")
        
        
            

            
        

if __name__ == '__main__':
    custom_server = client_cam(ip=config.SERVER_SOCKET_IPV4,port=str(config.SERVER_SOCKET_PORT))

                