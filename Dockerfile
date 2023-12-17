FROM roboflow/roboflow-inference-server-gpu

RUN pip install firebase_admin

COPY . .

CMD [ "python", "rtspCV.py" ] 