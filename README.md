<p align="center">
    <img src="assets/pyRTCvision logo.png" width=300 height=300>
</p>


# pyRTCvision
WebRTC stream with Firebase SDP exchange and Python Computer Vision. pyRTCvison works with firepub, firemtx-server to apply Machine Learning / Computer Vision to live stream.

## Install 
1. pip install inference-gpu
2. pip install firebase_admin
3. (if needed) pip install torch or torchvision

## Model and Analytics
Detects dog, cats, person per frame/image basis. Calculates a rolling average of detections for an approximation of activity of each during video stream. Machine learning algorithms from roboflow.

Microsoft coco model is used for predicton.

## Usage

Dockerfile there to create image to upload and run from your favorite cloud service provider’s VM. Recommend checkout out firepub and firemtx-server.