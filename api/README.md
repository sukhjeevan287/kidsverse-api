# Kidsverse Django Backend API

A complete Django REST Framework backend implementation built from the **Kidsverse Database Schema** (`kidsverse_db_schema.pdf`) and **API Specification** (`kidsverse_api_docs.pdf`).

## Features & Highlights

- **Database Backend**: PostgreSQL (target version 14+) utilizing UUID primary keys, JSONB columns, foreign key constraints, and cascade policies.
- **Environment Configuration**: Strictly managed via `.env` with support for PostgreSQL credentials (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`), Django `SECRET_KEY`, and `JWT_SECRET`.
- **JWT Authentication**: Secure Bearer Token authentication (`Authorization: Bearer <token>`) for Parent accounts.
- **Middleware Authorization**: Automatic ownership verification ensuring parents can only access their own student resources (`/api/v1/students/{studentId}/...`).
- **Standardized Error Envelope**: Consistent API response formatting for non-2xx statuses:
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR | FORBIDDEN | NOT_FOUND",
      "message": "Human readable error details",
      "details": {}
    }
  }
  ```
- **Server-Side XP & Streak Math**: Automatic server-side gamification updates upon completing missions, tests, and challenge battles.
- **Data Seeding**: Included `seed_data` management command to pre-populate catalog items (Subjects, Topics, Tiers, Missions, Tests, Avatar Customizations, Interests, Goals, Challenges, Opponents).

---

## Environment Setup (`.env`)

The project reads environment variables from the `.env` file in the project root:

```ini
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=*

# PostgreSQL Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=kidsverse_db
DB_USER=postgres
DB_PASSWORD=change-me
DB_HOST=127.0.0.1
DB_PORT=5432

# Authentication
JWT_SECRET=change-me
```

---

## Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Apply Migrations

Ensure PostgreSQL is running and the database specified in `.env` exists:

```bash
python manage.py migrate
```

### 3. Seed Initial Catalog Data

Populate initial subjects, topics, missions, avatar items, goals, and interests:

```bash
python manage.py seed_data
```

### 4. Run Automated Unit Tests

```bash
python manage.py test
```

### 5. Start Development Server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/api/v1/`.

---

## API Endpoints Overview

| Category | Endpoint | Method | Description |
|---|---|---|---|
| **Auth** | `/api/v1/auth/parent/signup` | `POST` | Create new Parent account & return JWT |
| **Auth** | `/api/v1/auth/parent/login` | `POST` | Authenticate Parent & return JWT |
| **Auth** | `/api/v1/auth/parent/logout` | `POST` | Invalidate session |
| **Parent** | `/api/v1/parent/me` | `GET` | Get authenticated parent profile |
| **Parent** | `/api/v1/parent/students` | `GET` | List children under parent |
| **Parent** | `/api/v1/parent/overview` | `GET` | Parent dashboard overview across children |
| **Students** | `/api/v1/students` | `POST` | Create child (step 1 of onboarding) |
| **Students** | `/api/v1/students/{studentId}/grade-board` | `PATCH` | Set child's grade and educational board |
| **Avatar** | `/api/v1/avatar/characters` | `GET` | List base explorer characters |
| **Avatar** | `/api/v1/avatar/items` | `GET` | List outfit/hair/accessory customization items |
| **Avatar** | `/api/v1/students/{studentId}/avatar` | `PUT` | Save equipped avatar look |
| **Interests** | `/api/v1/interests` | `GET` | Catalog of curiosity topics |
| **Interests** | `/api/v1/students/{studentId}/interests` | `PUT` | Update student's selected interests |
| **Goals** | `/api/v1/goals` | `GET` | Catalog of learning goals |
| **Goals** | `/api/v1/students/{studentId}/goals` | `PUT` | Update student's selected goals |
| **Onboarding**| `/api/v1/students/{studentId}/onboarding/steps/{stepKey}/complete` | `POST` | Mark specific onboarding step completed |
| **Onboarding**| `/api/v1/students/{studentId}/onboarding/status` | `GET` | Onboarding progress status |
| **Onboarding**| `/api/v1/students/{studentId}/nova/greet` | `POST` | Finish onboarding & greet AI companion Nova |
| **Home** | `/api/v1/students/{studentId}/home` | `GET` | Single call to hydrate Home screen |
| **Learn** | `/api/v1/students/{studentId}/subjects` | `GET` | Subjects list with progress & lock state |
| **Learn** | `/api/v1/subjects/{subjectId}/topics` | `GET` | Topics for a subject (by grade) |
| **Learn** | `/api/v1/students/{studentId}/topics/{topicId}` | `GET` | Full topic detail with tiers & node chain |
| **Learn** | `/api/v1/missions/{missionId}` | `GET` | Mission content payload |
| **Learn** | `/api/v1/students/{studentId}/missions/{missionId}/start` | `POST` | Start a mission |
| **Learn** | `/api/v1/students/{studentId}/missions/{missionId}/complete` | `POST` | Complete mission & award XP |
| **Journey** | `/api/v1/students/{studentId}/journey` | `GET` | Journey map worlds & companion activities |
| **Journey** | `/api/v1/students/{studentId}/companion-activities/{activityId}/complete` | `POST` | Log completion of companion activity |
| **Test** | `/api/v1/topics/{topicId}/tests` | `GET` | Tests for a topic |
| **Test** | `/api/v1/tests/{testId}` | `GET` | Test intro & metadata |
| **Test** | `/api/v1/students/{studentId}/tests/{testId}/attempts` | `POST` | Start test attempt |
| **Test** | `/api/v1/tests/attempts/{attemptId}/questions/{order}` | `GET` | Get single test question |
| **Test** | `/api/v1/tests/attempts/{attemptId}/answers` | `POST` | Submit answer for question |
| **Test** | `/api/v1/tests/attempts/{attemptId}/complete` | `POST` | Complete test attempt |
| **Test** | `/api/v1/tests/attempts/{attemptId}/result` | `GET` | Detailed test score & recommendations |
| **Challenge**| `/api/v1/challenges` | `GET` | List available challenges |
| **Challenge**| `/api/v1/challenges/{challengeId}/opponents` | `GET` | List AI opponents for challenge |
| **Challenge**| `/api/v1/challenges/{challengeId}/preview` | `GET` | Preview challenge match |
| **Challenge**| `/api/v1/students/{studentId}/challenge-battles` | `POST` | Start challenge battle |
| **Challenge**| `/api/v1/challenge-battles/{battleId}/complete` | `POST` | Complete battle & award XP |
| **Challenge**| `/api/v1/challenge-battles/{battleId}/result` | `GET` | Fetch battle result |
| **Profile** | `/api/v1/students/{studentId}/profile` | `GET` | Student profile overview |
| **Profile** | `/api/v1/students/{studentId}/profile/our-journey` | `GET` | Overall journey progress summary |
| **Profile** | `/api/v1/students/{studentId}/profile/cards` | `GET` | Earned badges & achievement cards |
