FROM python:3.11-slim

# Install system dependencies for PyQt5 and GUI apps
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    libnss3 \
    libasound2 \
    libglib2.0-0 \
    libxkbcommon-x11-0 \
    libxcb1 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libsm6 \
    libxext6 \
    qtbase5-dev \
    qtbase5-dev-tools \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*





ENV QT_X11_NO_MITSHM=1

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "Main.py"]
