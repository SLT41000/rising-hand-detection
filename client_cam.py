import socketio

class client_cam:
    def __init__(self,connection=True,ip=None,port=5000) -> None:
        self.status = "IDLE"
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
            

        @self.sio.on('complete')
        def on_complete():
            self.change_status()
            print('Temi ready')
                


        @self.sio.on('disconnect')
        def on_disconnect():
            print('Disconnected from server')
            

    def connect(self,ip,port):
        if(self.connection==False):
            return "connection set false"
        self.sio.connect('http://'+ip+':'+port+'')
        

    def disconnect(self):   
        if(self.connection==False):
            return "connection set false"
        self.sio.disconnect()

    def sentlocation(self,location):
        if(self.connection==False):
            return "connection set false"
       
        if(location != None):
            self.status="BUSY"
            self.sio.emit('location_from_cam',location)
        
        
            

            
            
            
    def change_status(self):
        
        if(self.status=="BUSY"):
            self.status="IDLE"
        else:
            self.status="BUSY"
        

    
                