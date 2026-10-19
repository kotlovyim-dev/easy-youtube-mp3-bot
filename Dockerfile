FROM python:3.11-slim

WORKDIR /app

# YouTube needs a JavaScript runtime (Node 22+) to solve its player challenges for yt-dlp
COPY --from=node:22.22.0-slim@sha256:dd9d21971ec4395903fa6143c2b9267d048ae01ca6d3ea96f16cb30df6187d94 /usr/local/bin/node /usr/local/bin/node

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
