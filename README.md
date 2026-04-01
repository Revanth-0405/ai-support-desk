# AI Support Desk API

A fully featured, production-ready AI Support Desk backend. This system implements an end-to-end enterprise ticketing platform featuring Role-Based Access Control (RBAC), real-time WebSocket chat, scalable NoSQL history, and Google Gemini AI integrations.

---

## Architecture Diagram

```text
+-------------------+       +-----------------------+       +-------------------------+
|                   |       |                       |       | PostgreSQL (Relational) |
|   Client / UI     | <---> |   Flask REST API      | <---> | - Users & Roles         |
| (Postman/Browser) | REST  |   (Auth, CRUD, AI)    |       | - Tickets & KB Articles |
|                   |       |                       |       +-------------------------+
+---------+---------+       +-----------+-----------+
          |                             |                   +-------------------------+
          | WebSockets                  | SDK/API           | AWS DynamoDB (NoSQL)    |
          v                             v                   | - Chat Messages         |
+-------------------+       +-----------------------+ <---> | - User Presence         |
| Flask-SocketIO    |       | Google Gemini 2.0     |       | - AI Usage Logs         |
| (Real-Time Comm.) |       | (Categorise, Suggest, |       +-------------------------+
|                   |       |  Summarise)           |
+-------------------+       +-----------------------+
```

---

## Tech Stack

* **Core Framework:** Python 3.12, Flask, Flask-RESTful
* **Authentication:** Flask-JWT-Extended (RBAC)
* **Relational Database:** PostgreSQL (Flask-SQLAlchemy & Alembic)
* **NoSQL Database:** AWS DynamoDB (boto3)
* **Real-Time Engine:** Flask-SocketIO
* **AI Engine:** Google Gemini API (gemini-2.0-flash)
* **Observability:** JSON Logging, request_id tracing
* **Testing:** Pytest, unittest.mock, SocketIO Test Client

---

## Local Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/Revanth-0405/ai-support-desk.git
cd ai-support-desk
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize database

```bash
flask db upgrade
```

### 5. Run the server

```bash
python run.py
```

---

## Environment Variables

Create a `.env` file in root:

| Variable              | Required | Description                  |
| --------------------- | -------- | ---------------------------- |
| FLASK_APP             | Yes      | run.py                       |
| FLASK_ENV             | Yes      | development / production     |
| DATABASE_URL          | Yes      | PostgreSQL connection string |
| JWT_SECRET_KEY        | Yes      | JWT secret                   |
| GEMINI_API_KEY        | Yes      | Google AI key                |
| AWS_ACCESS_KEY_ID     | Yes      | Dummy for local              |
| AWS_SECRET_ACCESS_KEY | Yes      | Dummy for local              |
| AWS_DEFAULT_REGION    | Yes      | e.g., us-east-1              |

---

## AI Features Overview

* **Auto-Categorisation:** Assigns category & priority using AI
* **Suggested Responses:** Generates responses using chat + KB
* **Conversation Summary:** Summarises ticket on resolution

---

## E2E Testing Guide (cURL)

### 1. Register users

```bash
curl -X POST http://localhost:5000/api/auth/register \
-H "Content-Type: application/json" \
-d '{"username":"cust1","email":"c@test.com","password":"password123"}'

curl -X POST http://localhost:5000/api/auth/register \
-H "Content-Type: application/json" \
-d '{"username":"agent1","email":"a@test.com","password":"password123"}'
```

### 2. Login

```bash
curl -X POST http://localhost:5000/api/auth/login \
-H "Content-Type: application/json" \
-d '{"email":"c@test.com","password":"password123"}'
```

### 3. Create ticket

```bash
curl -X POST http://localhost:5000/api/tickets \
-H "Authorization: Bearer <CUST_TOKEN>" \
-H "Content-Type: application/json" \
-d '{"subject":"Login error","description":"I get a 500 error"}'
```

### 4. Assign ticket

```bash
curl -X PUT http://localhost:5000/api/tickets/<TICKET_ID>/assign \
-H "Authorization: Bearer <AGENT_TOKEN>"
```

### 5. AI suggestion

```bash
curl -X POST http://localhost:5000/api/ai/suggest/<TICKET_ID> \
-H "Authorization: Bearer <AGENT_TOKEN>"
```

### 6. Resolve ticket

```bash
curl -X PUT http://localhost:5000/api/tickets/<TICKET_ID>/resolve \
-H "Authorization: Bearer <AGENT_TOKEN>"
```

---

## WebSocket Chat Guide

* Connect: `ws://localhost:5000/?token=<JWT>`
* Join: `join_room` → `{ "ticket_id": "<ID>" }`
* Send: `send_message` → `{ "ticket_id": "<ID>", "content": "Hello" }`
* Listen: `new_message`, `user_typing`, `user_left`

---

## Automated Tests

Run:

```bash
pytest -v
```

### Coverage:

* RBAC validation
* CRUD operations
* AI mocking
* WebSocket events
* DynamoDB interactions
* Transaction rollbacks
