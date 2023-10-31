import socketio
import config
class client_cam:
    def __init__(self,connection=True,ip=None,port=5000) -> None:
        self.status = "BUSY"
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

        @self.sio.on('on_ready')
        def on_complete():
            self.status="IDLE"
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
        if(location=="HOMEBASE"):
            self.sio.emit('home_base')
        elif(location != None):
            self.status="BUSY"
            self.sio.emit('location_from_cam',location)
        
        
        
            

            
        

if __name__ == '__main__':
    custom_server = client_cam(ip=config.SERVER_SOCKET_IPV4,port=str(config.SERVER_SOCKET_PORT))

                