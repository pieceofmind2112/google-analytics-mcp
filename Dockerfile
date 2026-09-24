FROM python:3.10-slim

WORKDIR /app

# Copy your repository files into the container
COPY . .

# Install the server package
RUN pip install --no-cache-dir .

# Expose the port Cloud Run will route traffic to
EXPOSE 8080

# Command to run your modified HTTP-enabled MCP server
# (Adjust this command to match your specific HTTP implementation)
CMD ["python", "-m", "analytics_mcp", "--transport", "http", "--port", "8080"]
