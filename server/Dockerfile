# Use an official Python runtime as a base image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /server

# Install required libraries
RUN pip install Flask
RUN pip install flask-pymongo
RUN pip install flask-cors
RUN pip install requests

# Copy the current directory contents into the container at /server
COPY . /server

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "app.py"]