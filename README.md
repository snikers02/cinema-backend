# 🎬 Cinema Collaborative Streaming Server (Backend)

Welcome to the backend streaming platform for real-time collaborative movie and video watching! This project is built on **Django, Django Channels (WebSockets), and Redis** using a strict and scalable **Microkernel Architecture**.

The system enables users to create virtual rooms, stream local media files or YouTube video links, chat in real-time, trigger animated reactions, and flexibly share playback controllers ("remotes").

---

## 🏗️ Microkernel Architecture

The entire codebase is structured into an isolated **Kernel Core** and dynamic modular **Plugins**. The core is fully autonomous and does not contain any hard dependencies or direct imports of plugin functionality. Decoupled communication and data propagation are handled entirely by event-driven **Django Signals**.

```mermaid
graph TD
    %% Core Kernel
    subgraph Kernel [System Kernel]
        RoomsApp[apps.rooms <br> Rooms Management]
        UsersApp[apps.users <br> User Management]
        WS[RoomConsumer <br> WebSockets / ASGI]
    end

    %% Event Bus
    Signals{Django Signals}

    %% Modular Plugins
    subgraph Plugins [Modular Plugins]
        PluginSync[plugins.sync <br> 🎮 Sync & Remotes]
        PluginMovies[plugins.movies <br> 🎬 Movies & YouTube]
        PluginChat[plugins.chat <br> 💬 Room Chat & History]
        PluginReactions[plugins.reactions <br> 🔥 Live Reactions]
        PluginSocial[plugins.social <br> 👥 Profiles & Socials]
        PluginActivity[plugins.activity <br> 📈 Activity Logger]
        PluginAchievements[plugins.achievements <br> 🏆 Gamification]
    end

    %% Flow connections
    RoomsApp -->|room_created_signal| Signals
    WS -->|socket_message_signal| Signals

    Signals -.--> PluginMovies
    Signals -.--> PluginSync
    Signals -.--> PluginChat
    Signals -.--> PluginReactions
    Signals -.--> PluginActivity
    Signals -.--> PluginAchievements
```

### 1. The Kernel Core
*   **`apps.users`**: Manages custom user profiles (`CustomUser`), JWT/Session authentication, and registration processes.
*   **`apps.rooms`**: Handles rooms lifecycle, unique invite code generation, and member management.
    *   **WebSocket Transport (`RoomConsumer`)**: The ASGI gateway for real-time traffic. It is only responsible for low-level connection handshakes, WebSocket frame FIFO dispatching, and broadcast grouping. It contains zero business logic related to chats or playback states; instead, it dispatches incoming frames as a generic `socket_message_signal` to the event bus.

### 2. Modular Plugins
*   **`plugins.movies` (Media & Video Integration)**:
    *   Manages the movies repository (supporting local file uploads like `.mp4`/`.webm` and raw **YouTube** URLs).
    *   Intercepts `room_created_signal` to instantiate and link corresponding movie models to the rooms.
*   **`plugins.sync` (Synchronized Playback & Shared Control "Remotes")**:
    *   Saves real-time playback coordinates and toggle values (`current_time` & `is_playing`) in `RoomPlaybackState`.
    *   Enforces access levels using `RoomPlaybackRules` (general settings) and `RoomAuthorizedController` (individual remote grants).
    *   Filters and drops incoming WebSocket commands (`play`, `pause`, `seek`) sent by participants without explicit remote rights.
*   **`plugins.chat` (Room Chats)**:
    *   Listens to `socket_message_signal` to filter `chat.message` events, validate textual frames, and commit them to the database history.
*   **`plugins.reactions` (Animated Flying Emojis)**:
    *   Allows participants to send live reactions (`reaction.send`) that animate across the screen of all connected peers.
*   **`plugins.social` (Social Framework)**:
    *   Handles friend requests, followings, online lists, and peer interactions.
*   **`plugins.activity` (Activity Log)**:
    *   Logs critical user interactions to format individual activity streams.
*   **`plugins.achievements` (Gamification Engine)**:
    *   Automatically unlocks milestones and achievements (e.g., *"First Watch Party"*, *"Social Butterfly"*) based on activity signals.

---

## 🛠️ Technology Stack

*   **Runtime Environment**: Python 3.11+
*   **Web Framework**: Django 4.2+ (Django REST Framework for APIs)
*   **Concurreny & WebSockets**: Django Channels 4, ASGI (Uvicorn/Daphne)
*   **Cache & Channel Layers**: Redis 7
*   **Database Engine**: PostgreSQL 15 / MySQL 8
*   **Containerization**: Docker, Docker Compose

---

## 🚀 Quick Setup (Docker deployment)

The backend environment is prepared for containerized deployments with automatic orchestration between Django, DB engines, and Redis services.

### 1. Setup Environment Configuration (`.env`)
Create a `.env` file in the root directory of the backend project (adjacent to `docker-compose.yml`):
```bash
cp .env.example .env
```
Populate database credentials, Django Secret Key, and Redis endpoints inside the `.env` file.

### 2. Spin Up Containers
Launch the stack in detached or foreground mode:
```bash
docker-compose up --build
```
This boots and orchestrates:
*   `web`: The Django ASGI web server listening on port `8000`.
*   `db`: The DB server listening on port `5432` / `5435`.
*   `redis`: The cache and message broker listening on port `6379`.

### 3. Run Database Migrations
Apply schemas and model structures to the database inside the active web container:
```bash
docker-compose exec web python manage.py migrate
```

### 4. Create Admin Account (Superuser)
To access the built-in Django Admin Panel (`/admin/`):
```bash
docker-compose exec web python manage.py createsuperuser
```

---

## 🎮 Safe Playback & Boundary Protections

To avoid playback freezes and out-of-sync frames (especially when switching between long and short streams), the system includes several safety layers:
1.  **State Reset on Content Change**: Each time a movie is linked or switched in a room (`attach_video_to_room` signal handler), its playback cursor is reset to `0.0` and `is_playing` defaults to `False`.
2.  **Boundary Protection (Overrun Capping)**: If a room contains an old stale timestamp that exceeds the duration of a newly loaded video, the frontend automatically detects this mismatch, seeks back to `0.0`, and notifies the backend to update the DB.
3.  **Safe Anchor Reference (first-tick protection)**: The timer that tracks user-triggered manual seeks initializes its cache variable (`lastTime`) at `-1`. This prevents sending initial false seeks to the WebSocket during the first mounting cycle of a room.

---

## 🔒 Extension and Development Rules

When writing new features or integrating tools, respect the system architecture constraints:
1.  **Strictly zero imports from `plugins` inside the `core`**. The Kernel Core must remain fully unaware of anything inside the `plugins` folder.
2.  Subscribe to Kernel events (e.g., room creation, socket message arrival) using Django signal handlers (`@receiver`) declared within the plugin directories.
3.  Always construct and apply schema changes through the active Docker container (`docker-compose exec web python manage.py migrate`).
