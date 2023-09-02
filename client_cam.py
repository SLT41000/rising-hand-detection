import socketio
import eventlet
sio = socketio.Client()

temi_stat = "IDLE"
def connect(ip,port):
    
    sio.connect('http://'+ip+':'+port+'')

def disconnect():    
    sio.disconnect()

def sentlocation(location):
    global temi_stat
    location=int(location)
    temi_stat="BUSY"
    sio.emit('send_location', location)
    
    
        

        
        
        
def change_temi_state():
    global temi_stat
    if(temi_stat=="BUSY"):
        temi_stat="IDLE"
    else:
        temi_stat="BUSY"
    
                
@sio.on('connect')
def on_connect():
    print('Connected to server')


@sio.on('response')
def on_response(data):
    print('Server response:', data)
    

@sio.on('get_location')
def get_location():
    change_temi_state()
    print('Temi ready')
        


@sio.on('disconnect')
def on_disconnect():
    print('Disconnected from server')
            