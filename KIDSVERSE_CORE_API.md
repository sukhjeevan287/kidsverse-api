# Kidsverse Core & App API Documentation

Comprehensive REST API reference for the **Kidsverse** mobile and web applications (Parent Accounts, Student Onboarding, Avatar Customization, Learning Missions, Journey Progression, Testing System, Challenge Battles, and Gamification).

Base URL: `http://localhost:8000/api/v1`

---

## 1. Authentication & Security Architecture

### Bearer Token Authentication
Endpoints marked as **Requires Auth** require an HTTP `Authorization` header containing the JWT token received from Parent login or signup:
```http
Authorization: Bearer <jwt_parent_token>
```

### Student Ownership Middleware
Endpoints with path pattern `/api/v1/students/{studentId}/...` automatically enforce authorization via [`StudentOwnershipMiddleware`](file:///C:/Users/admin/Desktop/kidsverse/api/middleware.py). The middleware verifies that the student UUID belongs directly to the authenticated parent. Unauthorized access attempts yield:
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Authenticated parent does not own this student",
    "details": {}
  }
}
```

### Gamification & Automatic Streak Engine
Completing missions, tests, and challenge battles automatically updates the student's server-side statistics (`total_xp`, `day_streak`, `level`). Level math is calculated as:
$$\text{level} = 1 + \left\lfloor \frac{\text{total\_xp}}{1000} \right\rfloor$$

---

## 2. API Endpoints Summary

| Category | Endpoint | Method | Auth | Description |
|---|---|---|---|---|
| **Auth** | `/auth/parent/signup` | `POST` | Public | Create new Parent account & obtain JWT |
| **Auth** | `/auth/parent/login` | `POST` | Public | Authenticate Parent & obtain JWT |
| **Auth** | `/auth/parent/logout` | `POST` | Bearer | End session |
| **Parent** | `/parent/me` | `GET` | Bearer | Get current parent profile |
| **Parent** | `/parent/students` | `GET` | Bearer | List children under current parent |
| **Parent** | `/parent/overview` | `GET` | Bearer | Dashboard metrics across all children |
| **Onboarding** | `/students` | `POST` | Bearer | Create a new child profile (Step 1) |
| **Onboarding** | `/students/{studentId}/grade-board` | `PATCH` | Bearer | Set child's grade and board (Step 2) |
| **Avatar** | `/avatar/characters` | `GET` | Public | Catalog of avatar character archetypes |
| **Avatar** | `/avatar/items` | `GET` | Public | Catalog of avatar items (outfit, hair, acc) |
| **Avatar** | `/students/{studentId}/avatar` | `PUT` | Bearer | Save child's customized avatar (Step 3) |
| **Interests** | `/interests` | `GET` | Public | Catalog of student interests |
| **Interests** | `/students/{studentId}/interests` | `PUT` | Bearer | Save child's selected interests (Step 4) |
| **Goals** | `/goals` | `GET` | Public | Catalog of learning goals |
| **Goals** | `/students/{studentId}/goals` | `PUT` | Bearer | Save child's selected goals (Step 5) |
| **Onboarding** | `/students/{studentId}/onboarding/steps/{stepKey}/complete` | `POST` | Bearer | Complete specific onboarding step |
| **Onboarding** | `/students/{studentId}/onboarding/status` | `GET` | Bearer | Check progress & next onboarding step |
| **Nova** | `/students/{studentId}/nova/greet` | `POST` | Bearer | Trigger Nova AI greeting & complete onboarding |
| **Home** | `/students/{studentId}/home` | `GET` | Bearer | Personalized home screen feed |
| **Learn** | `/students/{studentId}/subjects` | `GET` | Bearer | Available subjects & unlocked status |
| **Learn** | `/subjects/{subjectId}/topics` | `GET` | Public | List topics under subject |
| **Learn** | `/students/{studentId}/topics/{topicId}` | `GET` | Bearer | Topic detail with syllabus tiers & mission nodes |
| **Missions** | `/missions/{missionId}` | `GET` | Public | Fetch mission lesson content |
| **Missions** | `/students/{studentId}/missions/{missionId}/start` | `POST` | Bearer | Start mission timer & progress tracking |
| **Missions** | `/students/{studentId}/missions/{missionId}/complete` | `POST` | Bearer | Complete mission, award stars & XP |
| **Journey** | `/students/{studentId}/journey` | `GET` | Bearer | 2D World Map coordinates & companion activities |
| **Journey** | `/students/{studentId}/companion-activities/{activityId}/complete` | `POST` | Bearer | Complete companion mini-activity |
| **Tests** | `/topics/{topicId}/tests` | `GET` | Public | List diagnostic practice tests for topic |
| **Tests** | `/tests/{testId}` | `GET` | Public | Test metadata & question count |
| **Tests** | `/students/{studentId}/tests/{testId}/attempts` | `POST` | Bearer | Start test attempt & fetch first question |
| **Tests** | `/tests/attempts/{attemptId}/questions/{order}` | `GET` | Public | Fetch test question by sequence order |
| **Tests** | `/tests/attempts/{attemptId}/answers` | `POST` | Public | Submit answer for current test question |
| **Tests** | `/tests/attempts/{attemptId}/complete` | `POST` | Public | Grade test attempt, calculate score & XP |
| **Tests** | `/tests/attempts/{attemptId}/result` | `GET` | Public | Detailed score report & learning recommendations |
| **Challenges** | `/challenges` | `GET` | Public | List boss challenges |
| **Challenges** | `/challenges/{challengeId}/opponents` | `GET` | Public | List opponents for a challenge |
| **Challenges** | `/challenges/{challengeId}/preview` | `GET` | Public | Preview rules, opponent & rewards |
| **Battles** | `/students/{studentId}/challenge-battles` | `POST` | Bearer | Start 1v1 battle match against opponent |
| **Battles** | `/challenge-battles/{battleId}/complete` | `POST` | Public | Submit battle score and calculate win/loss |
| **Battles** | `/challenge-battles/{battleId}/result` | `GET` | Public | Fetch final battle summary & XP |
| **Profile** | `/students/{studentId}/profile` | `GET` | Bearer | Student stats, streak, avatar & level |
| **Profile** | `/students/{studentId}/profile/our-journey` | `GET` | Bearer | Long-term milestone & syllabus progress |
| **Profile** | `/students/{studentId}/profile/cards` | `GET` | Bearer | Collectible badges & cards earned |

---

## 3. Detailed Endpoint Reference

### 3.1. Auth & Parent Accounts

#### 3.1.1. Parent Signup
Create a new parent account and receive a JWT token.

- **Method**: `POST`
- **URL**: `/api/v1/auth/parent/signup`
- **Auth**: Public
- **Request Body**:
```json
{
  "email": "sarah.parent@example.com",
  "password": "SecretPassword123!",
  "full_name": "Sarah Connor",
  "phone": "+1-555-0199"
}
```
- **Response (`201 Created`)**:
```json
{
  "parent": {
    "id": "e4b2d184-a82f-4889-8d19-583bcf3d0a1b",
    "email": "sarah.parent@example.com",
    "full_name": "Sarah Connor",
    "phone": "+1-555-0199",
    "created_at": "2026-09-26T10:00:00Z",
    "last_login_at": null
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

#### 3.1.2. Parent Login
Authenticate with email and password.

- **Method**: `POST`
- **URL**: `/api/v1/auth/parent/login`
- **Auth**: Public
- **Request Body**:
```json
{
  "email": "sarah.parent@example.com",
  "password": "SecretPassword123!"
}
```
- **Response (`200 OK`)**:
```json
{
  "parent": {
    "id": "e4b2d184-a82f-4889-8d19-583bcf3d0a1b",
    "email": "sarah.parent@example.com",
    "full_name": "Sarah Connor",
    "phone": "+1-555-0199",
    "created_at": "2026-09-26T10:00:00Z",
    "last_login_at": "2026-09-26T10:05:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

#### 3.1.3. Parent Logout
End the authenticated session.

- **Method**: `POST`
- **URL**: `/api/v1/auth/parent/logout`
- **Auth**: `Bearer <token>`
- **Response (`204 No Content`)**

---

#### 3.1.4. Parent Me
Retrieve the authenticated parent profile.

- **Method**: `GET`
- **URL**: `/api/v1/parent/me`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "id": "e4b2d184-a82f-4889-8d19-583bcf3d0a1b",
  "email": "sarah.parent@example.com",
  "full_name": "Sarah Connor",
  "phone": "+1-555-0199",
  "created_at": "2026-09-26T10:00:00Z",
  "last_login_at": "2026-09-26T10:05:00Z"
}
```

---

#### 3.1.5. Parent Students
List all children linked to the parent.

- **Method**: `GET`
- **URL**: `/api/v1/parent/students`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "students": [
    {
      "id": "7fa8e1b2-c012-45e3-9876-543210fedcba",
      "name": "Leo Connor",
      "grade": "Grade 4",
      "board": "CBSE",
      "avatar": {
        "character_id": "3b29c9f0-21a4-4a25-a129-379f8812c3de",
        "thumbnail_url": "https://assets.kidsverse.app/avatars/explorer_boy.png"
      },
      "onboarding_completed": true
    }
  ]
}
```

---

#### 3.1.6. Parent Overview
Summary dashboard showing stats, streak, subject progress, and recent test scores across all children.

- **Method**: `GET`
- **URL**: `/api/v1/parent/overview`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "students": [
    {
      "student_id": "7fa8e1b2-c012-45e3-9876-543210fedcba",
      "name": "Leo Connor",
      "day_streak": 5,
      "total_xp": 1250,
      "subjects": [
        {
          "subject": "Mathematics",
          "progress_percent": 65
        },
        {
          "subject": "Science",
          "progress_percent": 40
        }
      ],
      "recent_test_score": 92.5
    }
  ]
}
```

---

### 3.2. Students & Onboarding

#### 3.2.1. Create Student
Creates a new child account under the authenticated parent (Step 1 of onboarding).

- **Method**: `POST`
- **URL**: `/api/v1/students`
- **Auth**: `Bearer <token>`
- **Request Body**:
```json
{
  "name": "Leo"
}
```
- **Response (`201 Created`)**:
```json
{
  "id": "7fa8e1b2-c012-45e3-9876-543210fedcba",
  "parent_id": "e4b2d184-a82f-4889-8d19-583bcf3d0a1b",
  "name": "Leo",
  "onboarding_completed_at": null,
  "created_at": "2026-09-26T10:10:00Z"
}
```

---

#### 3.2.2. Update Grade & Board
Selects the educational grade and curriculum board (Step 2 of onboarding).

- **Method**: `PATCH`
- **URL**: `/api/v1/students/{studentId}/grade-board`
- **Auth**: `Bearer <token>`
- **Request Body**:
```json
{
  "grade": "Grade 4",
  "board": "CBSE"
}
```
- **Response (`200 OK`)**:
```json
{
  "id": "7fa8e1b2-c012-45e3-9876-543210fedcba",
  "name": "Leo",
  "grade": "Grade 4",
  "board": "CBSE",
  "created_at": "2026-09-26T10:10:00Z"
}
```

---

#### 3.2.3. Avatar Characters Catalog
List base avatar characters available for selection.

- **Method**: `GET`
- **URL**: `/api/v1/avatar/characters`
- **Auth**: Public
- **Response (`200 OK`)**:
```json
{
  "characters": [
    {
      "id": "3b29c9f0-21a4-4a25-a129-379f8812c3de",
      "slug": "explorer-boy",
      "name": "Explorer Boy",
      "base_image_url": "https://assets.kidsverse.app/avatars/explorer_boy.png"
    },
    {
      "id": "4c30d0a1-32b5-5b36-b230-480a9923d4ef",
      "slug": "cosmic-girl",
      "name": "Cosmic Girl",
      "base_image_url": "https://assets.kidsverse.app/avatars/cosmic_girl.png"
    }
  ]
}
```

---

#### 3.2.4. Avatar Items Catalog
List customizable avatar items with optional category filtering (`outfit`, `hair`, `accessory`).

- **Method**: `GET`
- **URL**: `/api/v1/avatar/items?category=outfit`
- **Auth**: Public
- **Query Parameters**:
  - `category` (optional): `outfit`, `hair`, `accessory`
- **Response (`200 OK`)**:
```json
{
  "items": [
    {
      "id": "11111111-2222-3333-4444-555555555555",
      "name": "Space Cadet Suit",
      "slug": "space-suit",
      "category": "outfit",
      "thumbnail_url": "https://assets.kidsverse.app/items/space_suit.png"
    }
  ]
}
```

---

#### 3.2.5. Save Student Avatar
Save the child's customized avatar configuration (Step 3 of onboarding).

- **Method**: `PUT`
- **URL**: `/api/v1/students/{studentId}/avatar`
- **Auth**: `Bearer <token>`
- **Request Body**:
```json
{
  "character_id": "3b29c9f0-21a4-4a25-a129-379f8812c3de",
  "outfit_item_id": "11111111-2222-3333-4444-555555555555",
  "hair_item_id": null,
  "accessory_item_id": null
}
```
- **Response (`200 OK`)**:
```json
{
  "character_id": "3b29c9f0-21a4-4a25-a129-379f8812c3de",
  "outfit_item_id": "11111111-2222-3333-4444-555555555555",
  "hair_item_id": null,
  "accessory_item_id": null,
  "updated_at": "2026-09-26T10:15:00Z"
}
```

---

#### 3.2.6. Interests Catalog
Fetch available interests (e.g., Space, Animals, Robots, Sports, Art).

- **Method**: `GET`
- **URL**: `/api/v1/interests`
- **Auth**: Public
- **Response (`200 OK`)**:
```json
{
  "interests": [
    {
      "id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
      "key": "space",
      "name": "Space & Astronomy",
      "icon_asset": "https://assets.kidsverse.app/icons/space.png",
      "order_index": 1
    },
    {
      "id": "2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
      "key": "animals",
      "name": "Animals & Nature",
      "icon_asset": "https://assets.kidsverse.app/icons/animals.png",
      "order_index": 2
    }
  ]
}
```

---

#### 3.2.7. Set Student Interests
Save the child's selected interest preferences (Step 4 of onboarding).

- **Method**: `PUT`
- **URL**: `/api/v1/students/{studentId}/interests`
- **Auth**: `Bearer <token>`
- **Request Body**:
```json
{
  "interest_ids": [
    "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d"
  ]
}
```
- **Response (`200 OK`)**:
```json
{
  "selected_count": 1,
  "interest_ids": [
    "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d"
  ]
}
```

---

#### 3.2.8. Goals Catalog
Fetch available child learning goals (e.g. Master school topics, Daily learning habit).

- **Method**: `GET`
- **URL**: `/api/v1/goals`
- **Auth**: Public
- **Response (`200 OK`)**:
```json
{
  "goals": [
    {
      "id": "99999999-8888-7777-6666-555555555555",
      "key": "master_school_topics",
      "name": "Master School Syllabus",
      "description": "Score 90%+ in school exams and tests",
      "order_index": 1
    }
  ]
}
```

---

#### 3.2.9. Set Student Goals
Save selected learning goals for the child (Step 5 of onboarding).

- **Method**: `PUT`
- **URL**: `/api/v1/students/{studentId}/goals`
- **Auth**: `Bearer <token>`
- **Request Body**:
```json
{
  "goal_ids": [
    "99999999-8888-7777-6666-555555555555"
  ]
}
```
- **Response (`200 OK`)**:
```json
{
  "goal_ids": [
    "99999999-8888-7777-6666-555555555555"
  ]
}
```

---

#### 3.2.10. Complete Onboarding Step
Records completion of an individual onboarding step (`child`, `grade_board`, `avatar`, `interests`, `goals`, `lobby`, `nova`).

- **Method**: `POST`
- **URL**: `/api/v1/students/{studentId}/onboarding/steps/{stepKey}/complete`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "step_key": "lobby",
  "completed_at": "2026-09-26T10:18:00Z"
}
```

---

#### 3.2.11. Onboarding Status
Queries completed steps, the next step in line, and whether onboarding is 100% complete.

- **Method**: `GET`
- **URL**: `/api/v1/students/{studentId}/onboarding/status`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "completed_steps": ["child", "grade_board", "avatar", "interests", "goals", "lobby"],
  "next_step": "nova",
  "is_complete": false
}
```

---

#### 3.2.12. Nova Greet & Finish Onboarding
Triggers Nova AI companion greeting and marks `onboarding_completed_at`.

- **Method**: `POST`
- **URL**: `/api/v1/students/{studentId}/nova/greet`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "message": "Hey Leo! I'm Nova, your AI learning companion!",
  "onboarding_completed_at": "2026-09-26T10:20:00Z"
}
```

---

### 3.3. Home Screen

#### 3.3.1. Student Home
Returns personalized student feed: streak, level, XP, smart recommended mission, and subject cards.

- **Method**: `GET`
- **URL**: `/api/v1/students/{studentId}/home`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "greeting": "Ready for today's adventure, Leo?",
  "stats": {
    "day_streak": 5,
    "total_xp": 1250,
    "level": 2
  },
  "recommended_mission": {
    "mission_id": "727a3c31-1ee7-4560-bfdf-793ca0a831e5",
    "title": "Equivalent Fractions",
    "subject": "Mathematics",
    "topic": "Fractions",
    "duration_minutes": 8,
    "reason": "Continue your journey in Fractions!",
    "xp_reward": 30,
    "progress_percent": 0
  },
  "subjects": [
    {
      "id": "78794c48-fb9e-4e6f-a89c-851912442cf2",
      "name": "Mathematics",
      "slug": "mathematics",
      "icon_asset": "https://assets.kidsverse.app/subjects/math.png",
      "is_unlocked": true,
      "topics_count": 8
    }
  ]
}
```

---

### 3.4. Learn, Topics & Missions

#### 3.4.1. Student Subjects
Fetch list of subjects with unlocked status for the specific student.

- **Method**: `GET`
- **URL**: `/api/v1/students/{studentId}/subjects`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "subjects": [
    {
      "id": "78794c48-fb9e-4e6f-a89c-851912442cf2",
      "name": "Mathematics",
      "slug": "mathematics",
      "is_unlocked": true
    },
    {
      "id": "898a5d59-0cf0-4f70-b90d-962a23553da3",
      "name": "Science",
      "slug": "science",
      "is_unlocked": true
    }
  ]
}
```

---

#### 3.4.2. Subject Topics
Fetch all curriculum topics for a subject, with optional grade filtering.

- **Method**: `GET`
- **URL**: `/api/v1/subjects/{subjectId}/topics?grade=Grade+4`
- **Auth**: Public
- **Query Parameters**:
  - `grade` (optional): e.g. `Grade 4`
- **Response (`200 OK`)**:
```json
{
  "topics": [
    {
      "id": "060d5b51-ce0b-4171-8ecb-99d63897f2ca",
      "name": "Fractions",
      "slug": "fractions",
      "grade_level": "Grade 4",
      "board": "CBSE",
      "description": "Understand fractions as parts of a whole",
      "order_index": 1,
      "status": "unlocked"
    }
  ]
}
```

---

#### 3.4.3. Student Topic Detail
Retrieves topic roadmap with syllabus tiers (School Syllabus, Advanced, Olympiad) and mission nodes with star ratings.

- **Method**: `GET`
- **URL**: `/api/v1/students/{studentId}/topics/{topicId}`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "id": "060d5b51-ce0b-4171-8ecb-99d63897f2ca",
  "name": "Fractions",
  "grade_level": "Grade 4",
  "subject": "Mathematics",
  "description": "Explore fuel tank partitioning and fractions in orbit",
  "tiers": [
    {
      "tier_key": "school_syllabus",
      "label": "School Syllabus",
      "status": "unlocked",
      "missions": ["Equivalent Fractions", "Adding Fractions"]
    }
  ],
  "nodes": [
    {
      "mission_id": "727a3c31-1ee7-4560-bfdf-793ca0a831e5",
      "order_index": 1,
      "name": "Equivalent Fractions",
      "status": "unlocked",
      "stars": 0
    }
  ]
}
```

---

#### 3.4.4. Mission Detail
Returns mission lesson content (teaching method, explanation, image, hints, 3-step Learn Before Test flow, and CFU checks).

- **Method**: `GET`
- **URL**: `/api/v1/missions/{missionId}`
- **Auth**: Public
- **Response (`200 OK`)**:
```json
{
  "id": "727a3c31-1ee7-4560-bfdf-793ca0a831e5",
  "topic_id": "060d5b51-ce0b-4171-8ecb-99d63897f2ca",
  "tier_key": "school_syllabus",
  "name": "Equivalent Fractions",
  "xp_reward": 30,
  "content": {
    "type": "concept_package",
    "theme": "Space",
    "teaching_method": "Visual fuel tank partitioning in orbit",
    "explanation": "If an astronaut takes 2 out of 4 fuel pods (2/4), that is the exact same amount as half a fuel cell (1/2)!",
    "image_url": "https://assets.kidsverse.app/concepts/space_fractions.png",
    "hints": [
      "Divide both the top and bottom number by 2.",
      "Look at the visual fuel gauge."
    ],
    "nova_script": "Commander, look at the fuel reserves! Can you help calibrate them?",
    "learn_before_test": {
      "required": true,
      "order": ["understand", "example", "remember"],
      "starts_quiz_after": "remember",
      "steps": [
        {
          "step_key": "understand",
          "title": "Introduce the idea: Fractions represent parts of a whole",
          "teaching_text": "Imagine a fuel tank divided into 4 equal pods. Taking 2 pods fills up half the tank!",
          "key_idea": "Fractions with different numbers can describe the same amount.",
          "image_url": "https://assets.kidsverse.app/concepts/step1_understand_space_fractions.png",
          "image_prompt": "Astronaut comparing two fuel tanks side-by-side",
          "nova_script": "Notice how both tanks have the same amount of fuel?",
          "mini_question": {
            "question": "If you take 2 out of 4 equal pods, what fraction do you have?",
            "options": ["Half the tank", "The entire tank", "One quarter"],
            "answer": "Half the tank",
            "explanation": "2 out of 4 parts is half of the entire set."
          }
        },
        {
          "step_key": "example",
          "title": "Show it step by step: Multiplying top and bottom",
          "teaching_text": "Multiply top and bottom by 2: 1/2 x (2/2) = 2/4.",
          "key_idea": "Multiplying or dividing top and bottom by the same number keeps the value equal.",
          "image_url": "https://assets.kidsverse.app/concepts/step2_example_space_fractions.png",
          "image_prompt": "Holographic display showing 1/2 multiplying to form 2/4",
          "nova_script": "Multiplying top and bottom by 2 makes an equivalent fraction!",
          "mini_question": {
            "question": "What is 1/2 multiplied by 3/3?",
            "options": ["3/6", "2/6", "3/5"],
            "answer": "3/6",
            "explanation": "1*3 = 3 and 2*3 = 6, yielding 3/6."
          }
        },
        {
          "step_key": "remember",
          "title": "Make it memorable: The Golden Rule of Fractions",
          "teaching_text": "Whatever you do to the top, you MUST do to the bottom!",
          "key_idea": "Always treat numerator and denominator equally to keep fractions balanced.",
          "image_url": "https://assets.kidsverse.app/concepts/step3_remember_space_fractions.png",
          "image_prompt": "A balance scale floating in space",
          "nova_script": "Remember the Golden Rule and you will ace every quiz!",
          "mini_question": {
            "question": "What is the golden rule for keeping fractions equivalent?",
            "options": [
              "Do the same operation to both the top and bottom",
              "Only change the top number",
              "Always add 1 to the bottom"
            ],
            "answer": "Do the same operation to both the top and bottom",
            "explanation": "Applying the same factor to top and bottom keeps the ratio identical."
          }
        }
      ]
    },
    "check_for_understanding": [
      {
        "question": "Which fraction is equivalent to 1/2?",
        "options": ["2/4", "1/3", "3/5", "4/6"],
        "answer": "2/4",
        "difficulty": "Easy",
        "explanation": "2/4 simplifies to 1/2 when dividing both by 2."
      }
    ]
  }
}
```

---

#### 3.4.5. Start Mission
Initializes a mission progress timer.

- **Method**: `POST`
- **URL**: `/api/v1/students/{studentId}/missions/{missionId}/start`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "status": "in_progress",
  "started_at": "2026-09-26T10:30:00Z"
}
```

---

#### 3.4.6. Complete Mission
Submits lesson score, calculates stars earned (1-3 stars), awards XP, updates streak, and returns the next mission in sequence.

- **Method**: `POST`
- **URL**: `/api/v1/students/{studentId}/missions/{missionId}/complete`
- **Auth**: `Bearer <token>`
- **Request Body**:
```json
{
  "score": 100.0
}
```
- **Response (`200 OK`)**:
```json
{
  "status": "completed",
  "stars": 3,
  "xp_awarded": 30,
  "completed_at": "2026-09-26T10:38:00Z",
  "next_mission_id": "838b4d42-2ff8-5671-cfef-804db1b942f6",
  "topic_progress_percent": 50
}
```

---

### 3.5. Journey & Companion Activities

#### 3.5.1. Student Journey World Map
Returns 2D map node coordinates for gamified world exploration (`map_x`, `map_y`) and companion activities.

- **Method**: `GET`
- **URL**: `/api/v1/students/{studentId}/journey?subject=mathematics`
- **Auth**: `Bearer <token>`
- **Query Parameters**:
  - `subject` (optional, default `literacy`): e.g. `mathematics`, `science`
- **Response (`200 OK`)**:
```json
{
  "subject": "Mathematics",
  "tagline": "Explore Mathematics with Nova!",
  "worlds": [
    {
      "topic_id": "060d5b51-ce0b-4171-8ecb-99d63897f2ca",
      "world_name": "Fraction Orbiters",
      "tagline": "Partition fuel cells in outer space",
      "status": "unlocked",
      "map_x": 45.5,
      "map_y": 72.0
    }
  ],
  "companion_activities": [
    {
      "id": "aa11bb22-cc33-dd44-ee55-ff6677889900",
      "name": "Nova's Star Collector Mini-game"
    }
  ]
}
```

---

#### 3.5.2. Complete Companion Activity
Logs completion of a companion mini-game or activity.

- **Method**: `POST`
- **URL**: `/api/v1/students/{studentId}/companion-activities/{activityId}/complete`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "completed_at": "2026-09-26T10:45:00Z"
}
```

---

### 3.6. Diagnostic & Practice Tests

#### 3.6.1. Topic Tests
List all tests linked to a topic.

- **Method**: `GET`
- **URL**: `/api/v1/topics/{topicId}/tests`
- **Auth**: Public
- **Response (`200 OK`)**:
```json
{
  "tests": [
    {
      "id": "80f12c34-9ab3-45cd-ef12-3456789abcde",
      "name": "Equivalent Fractions Test",
      "intro_text": "Practice test for Equivalent Fractions",
      "questions_count": 5
    }
  ]
}
```

---

#### 3.6.2. Test Detail
Get test overview metadata.

- **Method**: `GET`
- **URL**: `/api/v1/tests/{testId}`
- **Auth**: Public
- **Response (`200 OK`)**:
```json
{
  "id": "80f12c34-9ab3-45cd-ef12-3456789abcde",
  "name": "Equivalent Fractions Test",
  "intro_text": "Practice test for Equivalent Fractions",
  "questions_count": 5
}
```

---

#### 3.6.3. Start Test Attempt
Creates an active test attempt session and returns the first question immediately.

- **Method**: `POST`
- **URL**: `/api/v1/students/{studentId}/tests/{testId}/attempts`
- **Auth**: `Bearer <token>`
- **Response (`201 Created`)**:
```json
{
  "attempt_id": "67890abc-1234-5678-90ab-cdef12345678",
  "status": "in_progress",
  "started_at": "2026-09-26T10:50:00Z",
  "first_question": {
    "id": "55555555-6666-7777-8888-999999999999",
    "question_text": "If a space pod uses 3/6 of its fuel, what fraction has it used?",
    "question_type": "mcq",
    "options": ["1/2", "1/3", "2/3", "3/4"],
    "order_index": 1
  }
}
```

---

#### 3.6.4. Get Test Question by Order
Fetches question $N$ of an active test attempt.

- **Method**: `GET`
- **URL**: `/api/v1/tests/attempts/{attemptId}/questions/{order}`
- **Auth**: Public
- **Response (`200 OK`)**:
```json
{
  "id": "66666666-7777-8888-9999-000000000000",
  "question_text": "Which fraction is equivalent to 2/8?",
  "question_type": "mcq",
  "options": ["1/4", "1/2", "3/8"],
  "points": 1,
  "order_index": 2
}
```

---

#### 3.6.5. Submit Test Answer
Submits the child's answer for evaluation, records correctness, and returns the next question ID.

- **Method**: `POST`
- **URL**: `/api/v1/tests/attempts/{attemptId}/answers`
- **Auth**: Public
- **Request Body**:
```json
{
  "question_id": "55555555-6666-7777-8888-999999999999",
  "selected_answer": "1/2"
}
```
- **Response (`200 OK`)**:
```json
{
  "is_correct": true,
  "next_question_id": "66666666-7777-8888-9999-000000000000"
}
```

---

#### 3.6.6. Complete Test Attempt
Finishes the attempt, grades total score, awards XP ($0.5 \times \text{score}$), and automatically creates targeted remediation recommendations if score $< 80\%$.

- **Method**: `POST`
- **URL**: `/api/v1/tests/attempts/{attemptId}/complete`
- **Auth**: Public
- **Response (`200 OK`)**:
```json
{
  "status": "completed",
  "score": 100.0,
  "correct_count": 5,
  "total_questions": 5,
  "completed_at": "2026-09-26T10:55:00Z"
}
```

---

#### 3.6.7. Test Result & Targeted Recommendations
Fetches full score breakdown and extra learning recommendations.

- **Method**: `GET`
- **URL**: `/api/v1/tests/attempts/{attemptId}/result`
- **Auth**: Public
- **Response (`200 OK`)**:
```json
{
  "score": 100.0,
  "correct_count": 5,
  "total_questions": 5,
  "xp_awarded": 50,
  "extra_learning": []
}
```

---

### 3.7. Challenges & 1v1 Battles

#### 3.7.1. List Challenges
List all active boss challenges.

- **Method**: `GET`
- **URL**: `/api/v1/challenges`
- **Auth**: Public
- **Response (`200 OK`)**:
```json
{
  "challenges": [
    {
      "id": "90e23d45-0bc4-56de-f012-456789abcdef",
      "slug": "fractions-equivalent-fractions-challenge",
      "name": "Equivalent Fractions Challenge",
      "description": "Boss challenge battle for Equivalent Fractions",
      "is_one_time": false
    }
  ]
}
```

---

#### 3.7.2. Challenge Opponents
List AI/opponent bots available for a challenge.

- **Method**: `GET`
- **URL**: `/api/v1/challenges/{challengeId}/opponents`
- **Auth**: Public
- **Response (`200 OK`)**:
```json
{
  "opponents": [
    {
      "id": "44444444-5555-6666-7777-888888888888",
      "name": "Robo Rex",
      "avatar_id": "robot-1",
      "difficulty": "medium"
    },
    {
      "id": "55555555-6666-7777-8888-999999999999",
      "name": "Cyber Titan",
      "avatar_id": "robot-2",
      "difficulty": "hard"
    }
  ]
}
```

---

#### 3.7.3. Preview Challenge
Preview battle arena rules, rewards, and opponent details.

- **Method**: `GET`
- **URL**: `/api/v1/challenges/{challengeId}/preview?opponent_id=44444444-5555-6666-7777-888888888888`
- **Auth**: Public
- **Response (`200 OK`)**:
```json
{
  "challenge": "Equivalent Fractions Challenge",
  "opponent": {
    "name": "Robo Rex",
    "difficulty": "medium"
  },
  "rules": "First to 5 correct answers wins.",
  "xp_reward": 50
}
```

---

#### 3.7.4. Start Challenge Battle
Begins a 1v1 battle match between student and selected opponent.

- **Method**: `POST`
- **URL**: `/api/v1/students/{studentId}/challenge-battles`
- **Auth**: `Bearer <token>`
- **Request Body**:
```json
{
  "challenge_id": "90e23d45-0bc4-56de-f012-456789abcdef",
  "opponent_id": "44444444-5555-6666-7777-888888888888"
}
```
- **Response (`201 Created`)**:
```json
{
  "battle_id": "33333333-4444-5555-6666-777777777777",
  "status": "in_progress",
  "started_at": "2026-09-26T11:00:00Z"
}
```

---

#### 3.7.5. Complete Challenge Battle
Submits final battle score ($\ge 50$ points = win, $< 50$ = loss), awards XP (50 XP for Win, 10 XP for Loss), and updates streak.

- **Method**: `POST`
- **URL**: `/api/v1/challenge-battles/{battleId}/complete`
- **Auth**: Public
- **Request Body**:
```json
{
  "score": 90.0
}
```
- **Response (`200 OK`)**:
```json
{
  "status": "completed",
  "result": "win",
  "score": 90.0,
  "xp_awarded": 50,
  "completed_at": "2026-09-26T11:04:00Z"
}
```

---

#### 3.7.6. Challenge Battle Result
Returns the completed battle result summary.

- **Method**: `GET`
- **URL**: `/api/v1/challenge-battles/{battleId}/result`
- **Auth**: Public
- **Response (`200 OK`)**:
```json
{
  "status": "completed",
  "result": "win",
  "score": 90.0,
  "xp_awarded": 50,
  "completed_at": "2026-09-26T11:04:00Z"
}
```

---

### 3.8. Profile, Our Journey & Collectible Cards

#### 3.8.1. Student Profile
Fetch child gamification card, streak, XP, grade, board, and avatar preview.

- **Method**: `GET`
- **URL**: `/api/v1/students/{studentId}/profile`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "name": "Leo",
  "level": 2,
  "total_xp": 1330,
  "day_streak": 5,
  "avatar_thumbnail_url": "https://assets.kidsverse.app/avatars/explorer_boy.png",
  "grade": "Grade 4",
  "board": "CBSE"
}
```

---

#### 3.8.2. Student Our Journey
Tracks overall syllabus completion progress across all subjects and milestone achievements.

- **Method**: `GET`
- **URL**: `/api/v1/students/{studentId}/profile/our-journey`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "subjects_progress": [
    {
      "subject": "Mathematics",
      "progress_percent": 65
    },
    {
      "subject": "Science",
      "progress_percent": 40
    }
  ],
  "milestones_completed": 3,
  "total_milestones": 12
}
```

---

#### 3.8.3. Student Collectible Cards
Retrieves trading cards and achievement badges earned by the child.

- **Method**: `GET`
- **URL**: `/api/v1/students/{studentId}/profile/cards`
- **Auth**: `Bearer <token>`
- **Response (`200 OK`)**:
```json
{
  "cards": [
    {
      "id": "card-1111-2222-3333-4444-555555555555",
      "card_name": "Fraction Master",
      "description": "Awarded for completing all Fraction syllabus missions with 3 stars",
      "image_url": "https://assets.kidsverse.app/cards/fraction_master.png",
      "rarity": "rare",
      "earned_at": "2026-09-26T10:40:00Z"
    }
  ]
}
```

---

## 4. End-to-End Workflow Examples via cURL

### 1. Parent Signup & Onboarding
```bash
# 1. Signup parent
curl -X POST "http://localhost:8000/api/v1/auth/parent/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"sarah@example.com","password":"Password123!","full_name":"Sarah"}'

# 2. Create child profile using returned token
curl -X POST "http://localhost:8000/api/v1/students" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Leo"}'

# 3. Set grade and board
curl -X PATCH "http://localhost:8000/api/v1/students/<STUDENT_ID>/grade-board" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"grade":"Grade 4","board":"CBSE"}'
```

### 2. Playing a Learning Mission
```bash
# Start mission
curl -X POST "http://localhost:8000/api/v1/students/<STUDENT_ID>/missions/<MISSION_ID>/start" \
  -H "Authorization: Bearer <TOKEN>"

# Complete mission (awards XP & Stars)
curl -X POST "http://localhost:8000/api/v1/students/<STUDENT_ID>/missions/<MISSION_ID>/complete" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"score": 100.0}'
```

### 3. Taking a Practice Test
```bash
# Start attempt
curl -X POST "http://localhost:8000/api/v1/students/<STUDENT_ID>/tests/<TEST_ID>/attempts" \
  -H "Authorization: Bearer <TOKEN>"

# Submit question answer
curl -X POST "http://localhost:8000/api/v1/tests/attempts/<ATTEMPT_ID>/answers" \
  -H "Content-Type: application/json" \
  -d '{"question_id":"<QUESTION_ID>","selected_answer":"1/2"}'

# Finish test attempt
curl -X POST "http://localhost:8000/api/v1/tests/attempts/<ATTEMPT_ID>/complete"
```
