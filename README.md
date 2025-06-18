# Expiry Notification System

A desktop-based inventory management system that notifies small business owners of products nearing expiry. Built with Python, PyQt5, and SQLite, this tool provides a simple GUI to manage and monitor product inventory.

---

## 📦 Features

- Add, search, and delete product entries
- Tracks product expiry dates
- Desktop notification alerts (now powered by `plyer` for cross-platform support)
- Simple and intuitive PyQt5 interface
- SQLite-powered data persistence

---

## 🚀 Run via Docker

```bash
docker pull techceo/expiry-notifier:latest
```

---
On Windows (VcXsrv required):
```bash
$env:DISPLAY="host.docker.internal:0.0"
docker run -it --rm -e DISPLAY=$env:DISPLAY techceo/expiry-notifier
```

On Linux:
```bash
xhost +local:docker
docker run -it --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix techceo/expiry-notifier
```

---
🐙 GitHub Repository
🔗 https://github.com/TechCeo/Expiry-Notification-System

🐳 Docker Hub Repository
🔗 https://hub.docker.com/r/techceo/expiry-notifier

---
🛠 Tech Stack
- Python 3.11

- PyQt5

- SQLite

- Plyer (replaced win10toast for cross-platform notifications)

- Docker
---
👤 Author
- Yusuf Adamu (TechCeo)
  
---
