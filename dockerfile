# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir matplotlib flask

# Make port 3030 available to the world outside this container
EXPOSE 3030

# Run the application when the container launches
CMD ["python", "mixed_json_arcadia_plotly_multiple_edit_text"]