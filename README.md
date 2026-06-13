# Kelem Backend

<div align="center">
  <img src="./public/logo.svg" alt="Ethio-Global Academy Teacher Portal" width="180" height="180">
  <br><br>
  <h1>Kelem Backend</h1>
  <p><em>Academic management platform API for organizations, schools, branches, teachers, students, parents, and school operations.</em></p>
  <!-- <p>
    <strong>Course:</strong> Software Engineering Final Year Project<br>
    <strong>Institution:</strong> Addis Ababa Science and Technology University
  </p>
  <br>
  <p>
    <strong>Collaborators:</strong><br>
    <a href="https://github.com/fitiha">fitiha</a> ·
    <a href="https://github.com/NahomTesM">NahomTesM</a> ·
    <a href="https://github.com/oddegen">oddegen</a> ·
    <a href="https://github.com/RobelD420">RobelD420</a> ·
    <a href="https://github.com/Tonetor777">Tonetor777</a>
  </p> -->
</div>

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Core Features](#core-features)
3. [Technology Stack](#technology-stack)
4. [System Architecture](#system-architecture)
5. [Project Structure](#project-structure)
6. [Getting Started](#getting-started)
7. [Environment Configuration](#environment-configuration)
8. [Common Commands](#common-commands)
9. [API Surface](#api-surface)
10. [Background Services](#background-services)
11. [Testing And Quality](#testing-and-quality)
12. [Deployment Notes](#deployment-notes)

---

## Project Overview

Kelem Backend is a Django and Django REST Framework backend for a school management platform. It supports multi-tenant academic operations across organizations, schools, and branches, with role-aware workflows for organization owners, branch admins, teachers, and parents.

The system is designed to power clients with authenticated REST APIs, real-time messaging, invitation-based onboarding, academic year management, attendance tracking, assessments, announcements, media uploads, and analytics.

### Purpose

To provide a centralized backend that manages the operational data and business rules of a modern academic platform, including school setup, user onboarding, classroom workflows, parent communication, and reporting.

---

## Core Features

| Domain | Description |
|---|---|
| **Authentication & Identity** | Custom user model with role-based access for organization owners, branch admins, teachers, and parents. Supports JWT authentication, approval-link exchange, and parent OTP login. |
| **Organization Hierarchy** | APIs for organizations, schools, and branches with ownership-aware access control. |
| **Academic Management** | Manage academic years, grades, sections, subjects, and grade-subject mappings. |
| **Teacher Management** | Teacher profiles, qualifications, subject assignments, homeroom assignments, invitation flows, and schedule-related data access. |
| **Student & Parent Management** | Student records, parent profiles, parent-student links, invitation flows, search/filter support, and self-service parent access patterns. |
| **Attendance** | Attendance records, attendance reasons, summary endpoints, and branch/class scoped attendance workflows. |
| **Assessments** | Assessment creation, result tracking, and academic performance workflows. |
| **Announcements** | Publish and manage school or branch announcements through dedicated API endpoints. |
| **Messaging** | Real-time chat threads over WebSockets for parent-teacher communication. |
| **Bulk Import** | CSV/Excel import workflows for teacher and student-related data with asynchronous job tracking and downloadable templates. |
| **Media Uploads** | Multipart upload and media handling backed by S3-compatible object storage. |
| **API Documentation** | OpenAPI schema generation with Swagger UI for frontend and integration teams. |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend Framework | Django 6 |
| API Framework | Django REST Framework |
| Authentication | Djoser, Simple JWT, Django Allauth |
| Real-Time | Django Channels, Redis |
| Task Queue | Celery, django-celery-beat |
| Database | PostgreSQL |
| Cache / Broker | Redis |
| Object Storage | MinIO in local and S3-compatible storage in production |
| API Schema | drf-spectacular |
| Environment Management | `uv`, `django-environ` |
| Testing | Pytest, factory-boy, coverage |
| Linting / Formatting | Ruff, djLint |
| Type Checking | mypy with Django and DRF plugins |
| Container Runtime | Docker Compose |

---

## System Architecture

### Application Layout

The backend follows a modular Django layout:

- `config/` contains settings, URL routing, ASGI/WSGI entrypoints, Celery setup, and websocket wiring.
- `apps/` contains the main business domains such as accounts, academics, teachers, students, attendance, assessments, messaging, and organizations.
- `core/` contains shared models, templates, static assets, import helpers, and project-level utilities.

### Runtime Flow

1. **HTTP API**: Django REST Framework serves authenticated REST endpoints under `/api/`.
2. **Authentication**: Djoser and JWT endpoints handle token issuance, refresh, verification, parent OTP login, and organization approval link exchange.
3. **Async Jobs**: Celery handles background work such as bulk imports and scheduled academic-year tasks.
4. **Realtime Messaging**: Django Channels exposes WebSocket chat endpoints for live thread updates.
5. **Storage**: Media and import files are stored through the configured media backend, with MinIO available for local S3-compatible development.

### Access Model

The API is scoped by role and ownership:

- **Organization owners** manage organization-wide resources.
- **Branch admins** manage branch-level operations.
- **Teachers** access their own teaching data and classroom workflows.
- **Parents** authenticate through invitation and OTP-based flows for student-linked access.

---

## Project Structure

```text
.
├── apps/
│   ├── accounts/           # Custom user model, auth flows, JWT, email and OTP logic
│   ├── organizations/      # Organization management
│   ├── schools/            # School entities
│   ├── branches/           # Branches and branch-admin workflows
│   ├── academics/          # Academic years, grades, sections, subjects
│   ├── teachers/           # Teacher profiles, qualifications, assignments
│   ├── students/           # Students, parents, parent links, invitations
│   ├── attendance/         # Attendance records, reasons, summaries
│   ├── analytics/          # Intervention and analytics-related APIs
│   ├── assessments/        # Assessments and results
│   ├── announcements/      # Announcement management
│   └── messaging/          # Chat threads and websocket messaging
├── config/                 # Settings, URLs, ASGI/WSGI, Celery, websocket config
├── core/                   # Shared models, templates, static files, import helpers
├── compose/                # Docker build definitions
├── docs/                   # Sphinx documentation
├── locale/                 # Translation files
├── public/                 # Public project assets
├── tests/                  # Project-level test support
├── docker-compose.local.yml
├── justfile
├── pyproject.toml
└── uv.lock
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- `uv`
- GNU `make` or `just` for convenience commands

### Local Setup

```bash
# Clone the repository
git clone <your-repository-url>
cd Backend

# Build the local images
just build

# Start the local stack
just up
```

The default local services include:

- Django API on `http://localhost:8000`
- Swagger docs on `http://localhost:8000/api/docs/`
- Adminer on `http://localhost:8080`
- Mailpit on `http://localhost:8025`
- Flower on `http://localhost:5555`

### Superuser Creation

```bash
docker compose -f docker-compose.local.yml run --rm django uv run python manage.py createsuperuser
```

---

## Environment Configuration

Local Docker services read environment values from:

- `.envs/.local/.django`
- `.envs/.local/.postgres`

Production services use the corresponding files under `.envs/.production/`.

### Important Settings

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `DJANGO_DEBUG` | Enables debug mode in local development |
| `FRONTEND_DOMAIN` | Used when generating activation and password-reset links |
| `DJANGO_EMAIL_BACKEND` | Email backend configuration |
| `S3_ACCESS_KEY_ID` | Object storage access key |
| `S3_SECRET_ACCESS_KEY` | Object storage secret |
| `S3_BUCKET` | Upload bucket name |
| `S3_REGION` | Object storage region |
| `S3_INTERNAL_ENDPOINT` | Internal S3-compatible endpoint |
| `S3_PUBLIC_ENDPOINT` | Public-facing object storage endpoint |
| `SMS_BACKEND` | SMS provider backend for OTP and invitation messages |
| `TELERIVET_API_KEY` | Telerivet API key when using the Telerivet SMS backend |
| `TELERIVET_PROJECT_ID` | Telerivet project identifier |
| `TELERIVET_TIMEOUT_SECONDS` | SMS request timeout |

---

## Common Commands

### Container Lifecycle

```bash
just build
just up
just logs
just down
```

### Django Management Commands

```bash
just manage migrate
just manage createsuperuser
just manage shell
```

### Documentation

```bash
docker compose -f docker-compose.docs.yml up
```

### Local Quality Checks

```bash
source .venv/bin/activate && ruff check .
docker compose -f docker-compose.local.yml run --rm django uv run mypy core
docker compose -f docker-compose.local.yml run --rm django pytest
```

---

## API Surface

### Base URLs

| Endpoint | Purpose |
|---|---|
| `/api/` | Main REST API |
| `/api/schema/` | OpenAPI schema |
| `/api/docs/` | Swagger UI |
| `/auth/` | Djoser and JWT authentication endpoints |

### Authentication Endpoints

| Endpoint | Purpose |
|---|---|
| `/auth/jwt/create/` | Obtain JWT access and refresh tokens |
| `/auth/jwt/refresh/` | Refresh an access token |
| `/auth/jwt/verify/` | Verify a token |
| `/auth/organization-approval/exchange/` | Exchange organization approval magic link for auth |
| `/auth/otp/request/` | Request parent login OTP |
| `/auth/otp/verify/` | Verify parent login OTP |

### Major API Resources

| Resource | Description |
|---|---|
| `/api/users/` | User and profile-facing account data |
| `/api/organizations/` | Organization management |
| `/api/schools/` | School management |
| `/api/branches/` | Branch management |
| `/api/branch-admins/` | Branch admin CRUD and invitation flow |
| `/api/academic-years/` | Academic year management |
| `/api/grades/` | Grades |
| `/api/sections/` | Sections |
| `/api/subjects/` | Subjects |
| `/api/grade-subjects/` | Grade-subject mappings |
| `/api/students/` | Student CRUD, search, and filtered access |
| `/api/parents/` | Parent profiles and invitation flow |
| `/api/parent-links/` | Parent-student relationships |
| `/api/teachers/` | Teacher CRUD, qualifications, assignments, and bulk import |
| `/api/homeroom-assignments/` | Homeroom assignment management |
| `/api/attendance/` | Attendance records |
| `/api/attendance-reasons/` | Attendance reason management |
| `/api/attendance-summaries/` | Attendance summaries and reporting |
| `/api/assessments/` | Assessments |
| `/api/assessment-results/` | Assessment results |
| `/api/announcements/` | Announcements |
| `/api/chat-threads/` | Messaging threads |
| `/api/media/` | Media upload endpoints |

### Real-Time Endpoint

```text
ws/chat/threads/<thread_id>/
```

This WebSocket endpoint is used for live chat thread updates.

---

## Background Services

### Celery

The project uses Celery for background processing, including bulk import execution and scheduled jobs.

Local service containers:

- `celeryworker`
- `celerybeat`
- `flower`

### Mailpit

Mailpit is available in local development for inspecting outbound email messages:

```text
http://127.0.0.1:8025
```

### MinIO

The local Docker stack includes MinIO and a bucket bootstrap container for S3-compatible media workflows.

---

## Testing And Quality

The main quality gates for this repository are:

- **Pytest** for automated tests
- **Ruff** for linting and formatting checks
- **mypy** for type checking
- **djLint** for Django template formatting

### Recommended Verification Commands

```bash
docker compose -f docker-compose.local.yml run --rm django pytest
docker compose -f docker-compose.local.yml run --rm django pytest apps/students/tests/
docker compose -f docker-compose.local.yml run --rm django uv run mypy core
source .venv/bin/activate && ruff check .
```

### Coverage

```bash
uv run coverage run -m pytest
uv run coverage html
```

---

## Deployment Notes

Production uses the Django production settings module and expects object storage to be configured for multipart media upload flows.

Set the following in `.envs/.production/.django`:

- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`
- `S3_BUCKET`
- `S3_REGION`
- `S3_INTERNAL_ENDPOINT`
- `S3_PUBLIC_ENDPOINT`

Also ensure the relevant DNS and reverse-proxy configuration is in place for the backend API and public upload endpoints.
