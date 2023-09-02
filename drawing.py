import cv2

# Global variables to store coordinates
zone_coords = []
drawing = False

def draw_rectangle(event, x, y, flags, param):
    global zone_coords, drawing

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        zone_coords = [(x, y)]

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        zone_coords.append((x, y))
        cv2.rectangle(frame, zone_coords[0], zone_coords[1], (0, 255, 0), 2)
        

# Capture video from webcam (change 0 to your camera index if necessary)
cap = cv2.VideoCapture(0)

cv2.namedWindow('Frame')
cv2.setMouseCallback('Frame', draw_rectangle)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    if not drawing and len(zone_coords) == 2:
        # Extract the zone from the frame
        
        zone_frame = frame[zone_coords[0][1]:zone_coords[1][1], zone_coords[0][0]:zone_coords[1][0]]
        print(len(zone_frame))
        cv2.imshow('Zone', zone_frame)

    print(frame)

    if cv2.waitKey(30) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
