import cv2
import numpy as np
from ultralytics import YOLO
import requests
import datetime
import time
from twilio.rest import Client
import threading

# Load the YOLO model
model = YOLO("best3.pt")

# Define the dictionary mapping class IDs to labels
d = {
    0: "bearing_defect",
    1: "coolant_hose_defect",
    2: "headlight_defect",
    3: "radiator_cap_defect",
    4: "spark_plug_defect"
}

def process_camera(max_retry=3, retry_delay=5):
    # Retry opening the camera for a maximum of 'max_retry' times
    for attempt in range(1, max_retry + 1):
        print(f"Attempting to open camera. Attempt {attempt}/{max_retry}")
        cap = cv2.VideoCapture(0)  # 0 for default camera, adjust if necessary

        if not cap.isOpened():
            print("Error opening camera")
            if attempt < max_retry:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retry attempts reached. Exiting.")
                exit(1)
        else:
            break

    # Continue processing once the camera is successfully opened
    # Define video writer settings
    fourcc = cv2.VideoWriter_fourcc(*"XVID")  # Video codec (XVID is a common choice)
    fps = 20  # Frames per second
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    output_filename = "output.avi"
    out = cv2.VideoWriter(output_filename, fourcc, fps, (frame_width, frame_height))

    # Create a window to display the camera feed
    cv2.namedWindow("Camera Feed", cv2.WINDOW_NORMAL)

    while True:
        # Capture a frame
        ret, frame = cap.read()

        # Break if frame is not captured
        if not ret:
            break

        # Perform prediction on the frame
        results = model(frame)[0]

        # Draw bounding boxes and labels for each detection
        for box in results:
            # Get individual coordinates
            x1, y1, x2, y2 = box.boxes.xyxy[0].cpu().numpy()

            # Get class label and confidence score
            class_id = box.boxes.cls[0].cpu().numpy().item()
            label = d[class_id]  # Map ID to label
            conf = box.boxes.conf[0].cpu().numpy().item()

            # Send Telegram notification for each detection asynchronously
            threading.Thread(target=send_telegram_message, args=(label,)).start()
            # send_sms_message(label)

            # Draw bounding box
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

            # Add label with optional confidence score
            text = f"{label}: {conf:.2f}"  # Format confidence score

            # Calculate label placement (adjust as needed)
            offset = 5  # Adjust offset based on text size and box size
            text_width, text_height = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
            x_text = int(x1 + offset)
            y_text = int(y1 + offset + text_height)

            cv2.putText(frame, text, (x_text, y_text), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Write the frame to the video file
        out.write(frame)

        # Display the frame without resizing
        cv2.imshow("Camera Feed", frame)

        # Wait for a key press (adjust the delay as needed)
        key = cv2.waitKey(1) & 0xFF

        # If 'q' is pressed, break the loop
        if key == ord('q'):
            break

    # Release resources
    cap.release()
    out.release()
    cv2.destroyAllWindows()

def send_telegram_message(message):
    # Telegram bot token and chat IDs
    BOT_TOKEN = "6577924249:AAEe1GBlG7T3WPljsnoOGRGXa1-951NlPbY"
    CHAT_IDS = ["1868149513", "581456276", "5690080759"]  
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Send the message to each chat ID
    for chat_id in CHAT_IDS:
        bot_message = f"The Class which is Defect is : {message} \nTimestamp: {timestamp}"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={chat_id}&text={bot_message}"
        response = requests.get(url)

# Twilio credentials
account_sid = 'ACc66b95d86c2632cb50786511b56e1d77'
auth_token = '8ea8204c98233e7457208b14c1670e79'
from_number = '+12562977674'

def send_sms_message(label):
    # Twilio client
    client = Client(account_sid, auth_token)

    # Construct the message
    message_body = f"Detected object: {label}\nConfidence:"

    # Send SMS
    message = client.messages.create(
        body=message_body,
        from_=from_number,
        to='+917397501899'
    )
    print(f"SMS sent: {message.sid}")

# Process the camera feed with a specified output filename
process_camera()
