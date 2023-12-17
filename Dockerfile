FROM roboflow/roboflow-inference-server-gpu

WORKDIR /pyRTCvision

RUN pip install firebase_admin

COPY . .

RUN python rtspCV.py