FROM python:3.11-slim

WORKDIR /app

# Install Flask
RUN pip install --no-cache-dir flask

# Copy application
COPY internal_app.py .

# Expose port
EXPOSE 8080

# Run the internal service
CMD ["python", "internal_app.py"]
