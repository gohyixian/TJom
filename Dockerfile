# Use a lightweight official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all project files into the container
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose the port the app runs on
EXPOSE 5000

# Start the Flask app using server.py with __main__ block
# CMD ["python", "server.py"]
CMD ["/bin/bash"]
