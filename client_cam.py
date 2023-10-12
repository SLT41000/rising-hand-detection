import socketio
import config
class client_cam:
    def __init__(self,connection=True,ip=None,port=5000) -> None:
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

        @self.sio.on('disconnect')
        def on_disconnect():
            print('Disconnected from server')
        
        @self.sio.on("rec_queue")
        def queue_data(data):
            print(data)
            
            

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
        self.sio.emit('push_queue',location)
    
    def get_queue_data(self):
        self.sio.emit('get_data_queue')
        
        
        
            

            
        

if __name__ == '__main__':
    custom_server = client_cam(ip=config.SERVER_SOCKET_IPV4,port=str(config.SERVER_SOCKET_PORT))

                