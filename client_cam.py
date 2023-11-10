import socketio
import config

class ClientCam:
    cam_id = 0

    def __init__(self, connection=True, ip=None, port=5000):
        self.cam_id = ClientCam.cam_id
        ClientCam.cam_id += 1
        self.table_data = []
        self.connection = connection
        self.sio = socketio.Client()

        self.setup_events()
        self.connect(ip, str(port))

    def setup_events(self):
        @self.sio.on('connect')
        def on_connect():
            print('Connected to server')

        @self.sio.on('response')
        def on_response(data):
            print('Server response:', data)

        @self.sio.on('receiver_goto_dest')
        def on_receiver_goto_dest(data):
            print('Receiver destination:', data)

        @self.sio.on('disconnect')
        def on_disconnect():
            print('Disconnected from server')

        @self.sio.on('event_update_table')
        def update_table():
            self.get_table_data()

        @self.sio.on('update_table')
        def update_table(data):
            if data is not None:
                self.table_data = data

        @self.sio.on('update_data')
        def update_data(data):
            print(data)

    def connect(self, ip, port):
        if not self.connection:
            return "Connection is set to false"
        self.sio.connect(f'http://{ip}:{port}')

    def push_table_data(self, up_left, down_right, square_size):
        self.sio.emit("append_table", (up_left, down_right, square_size, self.cam_id))

    def disconnect(self):
        if not self.connection:
            return "Connection is set to false"
        self.sio.emit("cam_disconnect", self.cam_id)
        self.sio.disconnect()

    def append_queue(self, queue_name):
        if queue_name == "HOMEBASE":
            self.sio.emit('home_base')
            return
        self.sio.emit("append_queue", queue_name)

    def del_table(self, xy):
        self.sio.emit("del_table", (xy, self.cam_id))

    def get_table_data(self):
        self.sio.emit("get_table", self.cam_id)

    def get_data(self):
        self.sio.emit("get_data")


if __name__ == '__main__':
    custom_server = ClientCam(ip=config.SERVER_SOCKET_IPV4, port=config.SERVER_SOCKET_PORT)
