FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Create the grouping directory for storing results
RUN mkdir -p /grouping && chmod 777 /grouping

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port 20425
EXPOSE 20425

# Set environment variable to indicate Docker environment
ENV DOCKER_ENV=true

# Run the application
CMD ["python", "app.py"]