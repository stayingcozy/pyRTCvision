FROM python:3.10

# Update required libraries for inference
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# Install python libraries
RUN pip install inference-gpu
RUN pip install firebase_admin

COPY . .

CMD [ "python", "rtspCV.py" ] 


# ## jetson nano
# FROM python:3.10 as pythonSet
# WORKDIR /app
# RUN pip install firebase_admin
# COPY . .

# FROM roboflow/inference-server:jetson
# COPY --from=pythonSet ./app .
# CMD [ "python", "rtspCV.py" ] 