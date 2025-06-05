# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements_simple.txt .
RUN pip install --no-cache-dir -r requirements_simple.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 8003 available to the world outside this container
EXPOSE 8003

# Run main.py when the container launches
# The command should point to main:app since main.py is in the root directory
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]
