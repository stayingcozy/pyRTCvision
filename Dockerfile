#FROM python:3.10

## Update required libraries for inference
#RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

## Install python libraries
#RUN pip install inference-gpu
#RUN pip install firebase_admin

#COPY . .

#CMD [ "python", "rtspCV.py" ] 


## jetson nano
FROM roboflow/inference-server:jetson

WORKDIR /app

# Update the package lists
# Update the package lists
RUN apt-get update && apt-get --fix-broken install -y && apt-get install -y python3.8 python3-pip

# Install or upgrade pip
RUN python3.8 -m pip install --upgrade pip

# Install firebase_admin
RUN python3.8 -m pip install firebase_admin
