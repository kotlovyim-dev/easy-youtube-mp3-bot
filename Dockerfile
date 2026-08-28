FROM python:3.11-slim

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-fetch static ffmpeg & ffprobe binaries during image build
RUN python3 -c "import static_ffmpeg; static_ffmpeg.add_paths()"

# Copy bot source
COPY . .

# Create downloads directory
RUN mkdir -p /app/downloads

CMD ["python", "main.py"]
