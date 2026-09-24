FROM python:3.10-slim

WORKDIR /app

# Copy your repository files into the container
COPY . .

# Install the server package and the HTTP web frameworks
RUN pip install --no-cache-dir . uvicorn starlette

# Expose the port Cloud Run will route traffic to
EXPOSE 8080

# Command to run the new HTTP wrapper
CMD ["python", "app.py"]
