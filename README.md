# Expiry Notification System

![Docker Pulls](https://img.shields.io/docker/pulls/techceo/expiry-notifier?style=flat-square)
![GitHub Repo stars](https://img.shields.io/github/stars/TechCeo/Expiry-Notification-System?style=flat-square)
![GitHub last commit](https://img.shields.io/github/last-commit/TechCeo/Expiry-Notification-System?style=flat-square)

A desktop-based inventory management system...

A desktop-based inventory management system that notifies small business owners of products nearing expiry. Built with Python, PyQt5, and SQLite, this tool provides a simple GUI to manage and monitor product inventory.

## Architecture

The application is organized as a modular monolith under `src/`:

- `domain/` contains typed product models and expiry business rules.
- `services/` coordinates inventory and notification use cases.
- `repositories/` owns product persistence operations.
- `infrastructure/` configures SQLite and migrates the legacy `students` table.
- `ui/` contains PyQt windows, dialogs, and the background expiry worker.

`Main.py` remains the compatibility entry point. On startup, existing records are copied
idempotently from the legacy table into the typed `products` schema; the original table
is retained as a safety measure.

Run locally with:

```bash
python Main.py
```

Run the automated tests with:

```bash
python -m unittest discover -v
```

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
