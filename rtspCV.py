import cv2
import inference
import supervision as sv

# Local
from Firebase import Firebase
from Analytics import Analytics

# init const
annotator = sv.BoxAnnotator()
debug = False  
model = "microsoft-coco/9"
uploadInterval = 30 # 180  
# export ROBOFLOW_API_KEY=your_key_here

# debug
# uid = "RJ0pPZEpmqPdiwMNBsuErIKU8zI3" # hardcode uid
# source = "rtsp://user0:pass0@192.168.86.34:8554/mystream"


def process(predictions, image):

    # Calculate movement analytics
    results = ay.analytics(predictions)

    # If debug, print and viz out
    if debug:

        # Watch web app chart
        classes = {item["class_id"]: item["class"] for item in predictions["predictions"]}

        detections = sv.Detections.from_roboflow(predictions)

        print(predictions)

        image = annotator.annotate(
            scene=image, detections=detections, labels=[classes[i] for i in detections.class_id]
        )

        cv2.imshow("Prediction", image)
        cv2.waitKey(1)


# Firebase listen for new rtsp links to process
firebase = Firebase()
source, uid = firebase.streamingListen()

# init anayltics class instance
ay = Analytics(model, uid, firebase, uploadInterval)

# Intake RTSP stream and predict
inference.Stream(
    source=source,
    model=model,
    output_channel_order="BGR",
    use_main_thread=True,
    on_prediction=process,
    api_key="api_key"
)

