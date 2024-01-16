import cv2
import time
import os
import glob
import subprocess
import json

# Local
from Firebase import Firebase
from Analytics import Analytics

def delete_oldest_file_if_needed(output_folder, max_files):
    files = glob.glob(f"{output_folder}/*.jpg")
    if len(files) > max_files:
        oldest_file = min(files, key=os.path.getctime)
        os.remove(oldest_file)

def on_prediction(result):

    if result.stdout is not None:
        # Convert the JSON string to a Python dictionary
        results = json.loads(result.stdout)

        print("results: ", results)

        # Now you can pass `results` to your function
        ay.analytics(results)
    else:
        print("No output from subprocess command")

def process_frames(rtsp_stream_link, fps, output_folder):
    print("Processing frames on: ", rtsp_stream_link)
    cap = cv2.VideoCapture(rtsp_stream_link)
    frame_id = 0

    # Check if output folder exists, create it if it doesn't
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    while True:
        if frame_id == 1:
            cap.release() # release past cap
            cap = cv2.VideoCapture(rtsp_stream_link)
        elif frame_id > 1:
            # Read and discard several frames to clear the buffer
            for _ in range(10):
                cap.read()

        ret, frame = cap.read()
        if not ret:
            break

        # New file name
        new_file_name = f"{output_folder}/frame_{frame_id}.jpg"

        # Write frame to file
        cv2.imwrite(new_file_name, frame)

        # Check if we need to delete the oldest file
        delete_oldest_file_if_needed(output_folder, 2*fps)

        # Post newest file to inference server
        inference_post_cmd = f"base64 {new_file_name} | curl -d @- \"http://{inference_jetson_ip}:9001/{model}?api_key={ROBOFLOW_API_KEY}\""
        result = subprocess.run(inference_post_cmd, shell=True, check=True, capture_output=True, text=True)

        on_prediction(result)

        frame_id += 1

        # Sleep for a while to control the frame rate
        # time.sleep(1 / fps)

    cap.release()

if __name__ == "__main__":
    
    # roboflow inits
    model = "microsoft-coco/9"
    ROBOFLOW_API_KEY = "FwisbEr6bGeC7RAh5XXM"
    # other inits
    inference_jetson_ip = "localhost"
    fps = 4
    jpgPath = './frames'
    uploadInterval = 30 #180  

    # Firebase listen for new rtsp links to process
    firebase = Firebase(production=False)

    # init anayltics class instance
    ay = Analytics(model, firebase, uploadInterval)

    while True:
        # Listen to streams in Firebase for status "streaming"
        source, uid = firebase.streamingListen()

        # Update streaming to processing
        firebase.updateStreamAsProcessing()

        # If stream just started it needs time to boot
        time.sleep(2)

        process_frames(source, fps, jpgPath)