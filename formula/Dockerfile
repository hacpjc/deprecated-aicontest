# Use an official Python runtime as a parent image
FROM ubuntu:18.04
 
# Set the working directory to /app
WORKDIR /app
 
# Install the python package we need
RUN apt update
RUN apt install -y python-pip
RUN export DEBIAN_FRONTEND=noninteractive; apt install -y tzdata
RUN apt install -y python-opencv
#RUN pip install --trusted-host pypi.python.org websocket-client==0.7.0 uptime logging flask-socketio  eventlet opencv-python pillow numpy pandas
RUN pip install --trusted-host pypi.python.org numpy eventlet flask-socketio pillow opencv-python pandas 

 
# Copy the current directory contents into the container at /app
ADD . /app
 
# Run sample_bot.py when the container launches, you should replace it with your program
# The parameters of the program should be "[player_name] [player_number] [token] [connect_url]"
ENTRYPOINT ["python", "hacformula.py"]
