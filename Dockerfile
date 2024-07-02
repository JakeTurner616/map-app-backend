# Use a lightweight Python image as a base
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and database
COPY backend.py .
COPY pixels.db .

# Expose the port the app will run on
EXPOSE 50617

# Install gunicorn
RUN pip install --no-cache-dir gunicorn

# Run Gunicorn when the container starts on port 50617
CMD ["gunicorn", "-b", "0.0.0.0:50617", "backend:app", "--log-level", "debug", "--log-file", "-"]

