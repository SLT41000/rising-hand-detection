import socketio
import config

class temiCam:
    cam_id = 0

    def __init__(self, ip=None, port=5000):

        self.sio = socketio.Client()

        self.setup_events()
        self.connect(ip, str(port))

    def setup_events(self):

        @self.sio.on('receiver_goto_dest')
        def on_receiver_goto_dest(data):
            print('Receiver destination:', data)
            print(f"Go to {data}")
            self.sio.emit("on_ready","ready")

        @self.sio.on('disconnect')
        def on_disconnect():
            print('Disconnected from server')



    def connect(self, ip, port):
        self.sio.connect(f'http://{ip}:{port}')
        print("connect\n")
        self.sio.emit("on_ready","ready")


if __name__ == '__main__':
    custom_server = temiCam(ip=config.SERVER_SOCKET_IPV4,port=config.SERVER_SOCKET_PORT)
