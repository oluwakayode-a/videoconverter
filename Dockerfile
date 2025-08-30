# Use Ubuntu as base image with Python
FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    ffmpeg \
    xvfb \
    x11-utils \
    libx11-dev \
    libxext-dev \
    libxrender-dev \
    libxtst6 \
    libxi6 \
    libglib2.0-0 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    libcairo-gobject2 \
    libpango-1.0-0 \
    libatk1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual display for GUI
ENV DISPLAY=:99

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY utils.py .

# Create directories for input/output
RUN mkdir -p /app/input /app/output

# Create startup script
RUN echo '#!/bin/bash\n\
# Start virtual display\n\
Xvfb :99 -screen 0 1024x768