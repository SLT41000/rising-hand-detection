import cv2

USER = "admin"
PASS = "888888"
IP = "ipv4"
PORT = "10554"
STREAM_PATH = "av0_0"


rtsp = f"rtsp://{USER}:{PASS}@{IP}:{PORT}/tcp/{STREAM_PATH}"
http=f"http://{IP}:{PORT}/videostream.cgi?user={USER}&pwd={PASS}"
cap = cv2.VideoCapture(http)

# Check if the capture was successfully opened
buffer = []
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("No more frames.")
        break

    buffer.append(frame)

    # Keep only the last N frames in the buffer (adjust N as needed)
    buffer = buffer[-10:]

    # Display the oldest frame from the buffer
    cv2.imshow('Output', buffer[0])

    k = cv2.waitKey(10) & 0xFF
    if k == 27:
        break