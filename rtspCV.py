import cv2
import inference
import supervision as sv

import matplotlib.pyplot as plt
from PIL import ImageDraw

# Local
from Analytics import Analytics

annotator = sv.BoxAnnotator()
debug = False   # if false delete every image after prediction/upload

def process(predictions, image):

    ## Analytics import function ##
    results = ay.analytics(predictions)
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


## Firebase listen for new rtsp links to process
uid = "RJ0pPZEpmqPdiwMNBsuErIKU8zI3" # hardcode uid
source = "rtsp://user0:pass0@192.168.86.34:8554/mystream"
model = "microsoft-coco/9"
# api an environmental var

uploadInterval = 30 # 180  
ay = Analytics(model, uid, uploadInterval)
# firebase = Firebase(uid)


## Inference import local function ##
# in - rtsp link, model, api key
# on prediction - output class of bbox coordinates
inference.Stream(
    source=source,
    model=model,
    output_channel_order="BGR",
    use_main_thread=True,
    on_prediction=process,
    api_key="api_key"
)

