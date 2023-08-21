import socketio
sio = socketio.Client()
class setup_connection:
    def __init__(self,  ip, port):
        self.ip = ip
        self.port= port
        self.temi_stat = "idle"
    


    @sio.on('connect')
    def on_connect():
        print('Connected to server')


    


    @sio.on('disconnect')
    def on_disconnect():
        print('Disconnected from server')
        


    def connect(self):
        sio.connect('http://'+self.ip+':'+self.port+'')

    def disconnect(self):    
        sio.disconnect()

    def sentlocation(self,location):
        sio.emit('send_location', location)
        
    @sio.on('response')#for change temi stat
    def on_response(self,data):
        self.temi_stat=data
        print('Server response:', data)