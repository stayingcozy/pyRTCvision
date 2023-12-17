from inference.core.interfaces.stream.inference_pipeline import InferencePipeline
from inference.core.interfaces.camera.entities import VideoFrame
from inference.core.interfaces.stream.sinks import render_boxes # debug

# Local
from Firebase import Firebase
from Analytics import Analytics

# init const
debug = False  
model = "microsoft-coco/9"
uploadInterval = 180 # 180, 30  
# export ROBOFLOW_API_KEY=your_key_here

# Firebase listen for new rtsp links to process
firebase = Firebase()

# init anayltics class instance
ay = Analytics(model, firebase, uploadInterval)

def on_prediction(predictions: dict, video_frame: VideoFrame) -> None:

    # Calculate movement analytics
    _ = ay.analytics(predictions)

while True:
    # Listen to streams in Firebase for status "streaming"
    source, uid = firebase.streamingListen()

    # Update streaming to processing
    firebase.updateStreamAsProcessing()

    if debug:
        pipeline = InferencePipeline.init(
            model_id=model,
            video_reference=source,
            on_prediction=render_boxes,
        )
        pipeline.start()
        pipeline.join()

    else:
        try:
            pipeline = InferencePipeline.init(
                model_id=model,
                video_reference=source,
                on_prediction=on_prediction,
            )
            pipeline.start()
            pipeline.join()
        except:
            firebase.updateStreamAsBroken()
            print("inference failed to process stream. Restarting") 

