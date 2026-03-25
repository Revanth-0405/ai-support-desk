# Real-Time AI-Powered Support Desk

## 1. Project Overview

This is the backend system for a SaaS customer support platform. The system is built using a layered architecture with a clear separation between REST endpoints, service logic, and data access.

Currently in **Phase 1**, this system supports:

* Role-Based Access Control (RBAC) for Customers, Agents, and Admins.
* Full CRUD operations for Support Tickets, including auto-generated ticket numbers.
* A searchable Knowledge Base (KB) with soft-delete capabilities.

---

## 2. Architecture Diagram (Phase 1)

```text
+-------------------+       +--------------------+
| Flask REST API    |       | PostgreSQL         |
| (Tickets, KB,     | ----> | (Users, Tickets,   |
| Users, Auth)      |       | KB Articles)       |
+-------------------+       +--------------------+

(Note: DynamoDB and Flask-SocketIO will be integrated in Phase 2)
```

---

## 3. Tech Stack

* **Language:** Python 3.10+
* **Framework:** Flask (Blueprints, App Factory)
* **Database:** PostgreSQL (via Docker)
* **ORM:** Flask-SQLAlchemy & Flask-Migrate
* **Authentication:** Flask-JWT-Extended

---

## 4. Local Setup Instructions

### Prerequisites

* Python 3.10+ installed
* Docker and Docker Compose installed

### Step-by-Step Setup

#### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ai-support-desk.git
cd ai-support-desk
```

#### 2. Start the databases using Docker

```bash
docker-compose up -d
```

#### 3. Set up the virtual environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

#### 4. Install dependencies

```bash
pip install -r requirements.txt
```

#### 5. Configure Environment Variables

Copy the example file and update it if necessary:

```bash
cp .env.example .env
```

#### 6. Run Database Migrations

```bash
flask db init
flask db migrate -m "initial_schema"
flask db upgrade
```

#### 7. Run the Application

```bash
python run.py
```

---

## 5. Environment Variables

| Variable       | Description                  | Example                                              |
| -------------- | ---------------------------- | ---------------------------------------------------- |
| FLASK_APP      | Entry point for Flask        | run.py                                               |
| FLASK_ENV      | Environment mode             | development                                          |
| SECRET_KEY     | Flask secret key             | your_secret_key                                      |
| DATABASE_URL   | PostgreSQL connection string | postgresql://user:password@localhost:5432/support_db |
| JWT_SECRET_KEY | Secret key for JWT auth      | your_jwt_secret_key                                  |

---

## 6. API Documentation (Phase 1 Endpoints)

### Authentication

* `POST /api/auth/register` → Register a new user
* `POST /api/auth/login` → Login and receive a JWT

---

### Tickets

| Method | Endpoint                  | Description                          | Auth Required |
| ------ | ------------------------- | ------------------------------------ | ------------- |
| POST   | /api/tickets              | Create a support ticket              | Customer+     |
| GET    | /api/tickets              | List tickets (paginated, filterable) | Yes           |
| GET    | /api/tickets/<id>         | Get ticket details                   | Yes           |
| PUT    | /api/tickets/<id>         | Update ticket (status, priority)     | Agent+        |
| PUT    | /api/tickets/<id>/assign  | Assign agent to ticket               | Agent+        |
| PUT    | /api/tickets/<id>/resolve | Resolve and close ticket             | Agent+        |

---

### Knowledge Base (KB)

| Method | Endpoint     | Description            | Auth Required |
| ------ | ------------ | ---------------------- | ------------- |
| GET    | /api/kb      | List KB articles       | No            |
| GET    | /api/kb/<id> | Get article details    | No            |
| POST   | /api/kb      | Create KB article      | Agent+        |
| PUT    | /api/kb/<id> | Update KB article      | Agent+        |
| DELETE | /api/kb/<id> | Soft-delete KB article | Admin         |

---

## 8. Phase 2: Real-Time & Presence API (WebSocket)

### New REST Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET`  | `/api/tickets/<id>/messages` | Get chat history for a ticket (REST fallback) | Yes (Customer scoped) |
| `GET`  | `/api/presence/agents` | List all agents with current presence status | Agent/Admin |

### WebSocket Connection (URL: `ws://localhost:5000`)
**Authentication:** A valid JWT token MUST be passed during the connection handshake.
* **Query String:** `?token=<YOUR_JWT>`
* **Payload:** `{ "token": "<YOUR_JWT>" }`
Unauthenticated connections will be immediately rejected.

### Client-to-Server Events (Emit)
| Event Name | Payload | Description |
|------------|---------|-------------|
| `join_room` | `{ "ticket_id": "<uuid>" }` | Joins a ticket's chat room. Returns `message_history` array. |
| `send_message`| `{ "ticket_id": "<uuid>", "content": "Hello!" }` | Sends a message to the room. Stored in DynamoDB. |
| `leave_room`| `{ "ticket_id": "<uuid>" }` | Leaves the chat room. |
| `typing` | `{ "ticket_id": "<uuid>" }` | Broadcasts typing status to others in the room. |

### Server-to-Client Events (Listen)
| Event Name | Payload | Description |
|------------|---------|-------------|
| `message_history` | `[ { message_obj }, ... ]` | Array of last 50 messages, received upon joining a room. |
| `new_message` | `{ message_obj }` | Real-time broadcast of a new chat message. |
| `user_typing` | `{ "user_id": "<uuid>", "ticket_id": "<uuid>" }` | Another user is typing. |
| `user_left` | `{ "user_id": "<uuid>", "ticket_id": "<uuid>" }` | A user left the chat room. |
| `presence_update` | `{ "user_id": "<uuid>", "status": "online/offline" }`| Global presence state changes. |
| `new_ticket_alert`| `{ ticket_obj }` | Alert to all agents when a new ticket is created. |
| `ticket_assigned` | `{ ticket_obj }` | Alert emitted specifically to the assigned agent. |
| `ticket_resolved` | `{ "ticket_id": "<uuid>" }` | Alert emitted to the room when the ticket is closed. |
| `error` | `{ "msg": "Error details" }` | Emitted when validation or auth fails. |