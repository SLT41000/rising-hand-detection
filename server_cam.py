import eventlet
import socketio

import cofig
class CustomSocketIOServer:
    def __init__(self):
        self.sio = socketio.Server()
        self.app = socketio.WSGIApp(self.sio, static_files={
            '/': {'content_type': 'text/html', 'filename': 'index.html'}
        })
        self.location = None
        self.cur_location=None
        self.setup_events()

    def setup_events(self):
        @self.sio.event
        def move_to(sid):
           
            self.sio.emit("receiver_goto_dest", self.cur_location)

        @self.sio.event
        def receiver_moving_status(sid, data):
            print(data)
            if data == "complete":
                self.cur_location=None
                self.sio.emit("sender_location")
                self.sio.emit("on_complete")

        @self.sio.event
        def location_from_cam(sid, location):
            
            self.cur_location = location
            print(self.cur_location)
            self.sio.emit("receiver_goto_des", self.cur_location)
            
            
        
        @self.sio.event
        def connect(sid, environ):
            print('connect ', sid)
            self.sio.emit("sender_location")

        @self.sio.event
        def response(sid, data):
            print('message ', data)

        @self.sio.event
        def disconnect(sid):
            print('disconnect ', sid)

        @self.sio.event
        def receiver_location(sid, data):
            self.location = data
            
    def start_server(self, host, port):
        eventlet.wsgi.server(eventlet.listen((host, port)), self.app)

if __name__ == '__main__':
    custom_server = CustomSocketIOServer()
    custom_server.start_server(cofig.SERVER_SOCKET_IPV4, 5000)