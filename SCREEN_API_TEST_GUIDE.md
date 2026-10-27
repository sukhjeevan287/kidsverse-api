# Kidsverse Screen API Test Guide

This guide covers every API referenced by `Kidsverse_All_Screens_API_62.pdf`. The API base URL is `http://127.0.0.1:8000/api/v1`.

## Before Testing

Run the migration and seed the local catalog:

```powershell
py -3 manage.py migrate
py -3 manage.py seed_data
py -3 manage.py runserver
```

Set these PowerShell variables. Replace generated values as you progress through the flow.

```powershell
$API = 'http://127.0.0.1:8000/api/v1'
$AUTH = 'Bearer <TOKEN>'
$PARENT_ID = '<PARENT_ID>'
$STUDENT_ID = '<STUDENT_ID>'
$SUBJECT_ID = '<SUBJECT_ID>'
$TOPIC_ID = '<TOPIC_ID>'
$MISSION_ID = '<MISSION_ID>'
$PACKAGE_ID = '<PACKAGE_ID>'
$TEST_ID = '<TEST_ID>'
$ATTEMPT_ID = '<ATTEMPT_ID>'
$CHALLENGE_ID = '<CHALLENGE_ID>'
$OPPONENT_ID = '<OPPONENT_ID>'
$BATTLE_ID = '<BATTLE_ID>'
```

All endpoints except signup, login, forgot-password, and catalog/content routes require:

```powershell
-Headers @{ Authorization = $AUTH }
```

## Screen Coverage

| Screens | Screen name(s) | API route | Status |
|---|---|---|---|
| 01 | Landing | No API | No API required |
| 02 | Parent Login | `POST /auth/parent/login` | Ready |
| 03 | Forgot Password | `POST /auth/parent/forgot-password` | Ready; delivery provider still needs configuration |
| 04 | Create Account | `POST /auth/parent/signup` | Ready |
| 05 | Create Child | `POST /students` | Ready |
| 06–07 | Parent verification and OTP | `POST /parent/verification/start`, `POST /parent/verification/verify` | Ready |
| 08 | Learning Setup | `PATCH /students/{studentId}/grade-board` | Ready; assigns the matching curriculum |
| 09 | Avatar | `PUT /students/{studentId}/avatar` | Ready |
| 10–11 | Interests and Goals | `PUT /students/{studentId}/interests`, `PUT /students/{studentId}/goals` | Ready |
| 12 | Meet Nova | Existing onboarding routes | Ready |
| 13 | Welcome | `GET /students/{studentId}/learning-path` | Ready |
| 14 | Home | `GET /students/{studentId}/home` | Ready |
| 15 | Settings Panel | `GET/PATCH /students/{studentId}/settings` | Ready |
| 16 | Nova Chat | `GET/POST /students/{studentId}/nova/messages` | Ready |
| 17 | Learn Hub | `GET /students/{studentId}/subjects` | Ready |
| 18–20, 47–48 | Journey and companion screens | `GET /students/{studentId}/journey?subject={slug}` | Ready |
| 21–25 | Subject topic screens | `GET /students/{studentId}/topics/{topicId}` | Ready |
| 26 | Lesson Discover | `GET /missions/{missionId}` | Ready |
| 27–36 | Learning package screens | `GET /learning-packages/{packageId}` | Ready |
| 37–39 | Mission start, completion, review | Mission start/complete/review routes | Ready |
| 40–46 | Test, result, review, extra learning | Test and recommendation routes | Ready |
| 49–54 | Challenge and leaderboard | Challenge and leaderboard routes | Ready |
| 55–57 | Profile, journey, break passes | Profile and break-pass routes | Ready |
| 58–62 | Parent gate, switching, overview, evidence, plan | Parent routes | Ready |

## Onboarding and Authentication

### Create account — Screen 04

`parent_pin` is optional, but provide it to test Screen 58.

```powershell
Invoke-RestMethod -Method Post -Uri "$API/auth/parent/signup" -ContentType 'application/json' -Body '{
  "email":"parent@example.com", "password":"Password123", "full_name":"Priya Shah", "phone":"9999999999", "parent_pin":"1234"
}'
```

Save the returned `token` in `$AUTH` and `parent.id` in `$PARENT_ID`.

### Login — Screen 02

```powershell
Invoke-RestMethod -Method Post -Uri "$API/auth/parent/login" -ContentType 'application/json' -Body '{"email":"parent@example.com","password":"Password123"}'
```

### Forgot password — Screen 03

```powershell
Invoke-RestMethod -Method Post -Uri "$API/auth/parent/forgot-password" -ContentType 'application/json' -Body '{"email":"parent@example.com"}'
```

This safely records a request. It deliberately does not expose whether the email exists. Configure an email/SMS provider before treating password reset as production-ready.

### Create child — Screen 05

```powershell
Invoke-RestMethod -Method Post -Uri "$API/students" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body '{"name":"Aarav"}'
```

Save `id` as `$STUDENT_ID`.

### Start and verify parent OTP — Screens 06–07

```powershell
$verification = Invoke-RestMethod -Method Post -Uri "$API/parent/verification/start" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body "{
  \"full_name\":\"Priya Shah\", \"relationship\":\"Mother\", \"phone\":\"9999999999\", \"student_id\":\"$STUDENT_ID\"
}"

Invoke-RestMethod -Method Post -Uri "$API/parent/verification/verify" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body "{
  \"challenge_id\":\"$($verification.challenge_id)\", \"code\":\"$($verification.development_code)\"
}"
```

`development_code` is only returned with `DEBUG=True`; connect an SMS provider for production delivery.

### Set grade and board — Screen 08

```powershell
Invoke-RestMethod -Method Patch -Uri "$API/students/$STUDENT_ID/grade-board" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body '{"grade":"4","board":"CBSE"}'
```

This resolves or creates the `CBSE + 4` curriculum and stores it on the student. Student-facing subjects, topics, home, and journey data are limited to this curriculum.

### Avatar catalogs and save — Screen 09

```powershell
Invoke-RestMethod -Uri "$API/avatar/characters"
Invoke-RestMethod -Uri "$API/avatar/items?category=outfit"
Invoke-RestMethod -Method Put -Uri "$API/students/$STUDENT_ID/avatar" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body '{
  "character_id":"<CHARACTER_ID>", "outfit_item_id":"<OUTFIT_ITEM_ID>", "hair_item_id":null, "accessory_item_id":null
}'
```

### Interests and goals — Screens 10–11

```powershell
Invoke-RestMethod -Uri "$API/interests"
Invoke-RestMethod -Method Put -Uri "$API/students/$STUDENT_ID/interests" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body '{"interest_ids":["<INTEREST_ID>"]}'
Invoke-RestMethod -Uri "$API/goals"
Invoke-RestMethod -Method Put -Uri "$API/students/$STUDENT_ID/goals" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body '{"goal_ids":["<GOAL_ID>"]}'
```

### Meet Nova — Screen 12

```powershell
Invoke-RestMethod -Method Post -Uri "$API/students/$STUDENT_ID/onboarding/steps/lobby/complete" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Method Post -Uri "$API/students/$STUDENT_ID/nova/greet" -Headers @{Authorization=$AUTH}
```

## Learning Screens

### Welcome learning path — Screen 13

```powershell
Invoke-RestMethod -Uri "$API/students/$STUDENT_ID/learning-path" -Headers @{Authorization=$AUTH}
```

### Home and settings — Screens 14–15

```powershell
Invoke-RestMethod -Uri "$API/students/$STUDENT_ID/home" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Uri "$API/students/$STUDENT_ID/settings" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Method Patch -Uri "$API/students/$STUDENT_ID/settings" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body '{"settings":{"music_enabled":false,"sound_effects":true}}'
```

### Nova chat — Screen 16

```powershell
Invoke-RestMethod -Uri "$API/students/$STUDENT_ID/nova/messages" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Method Post -Uri "$API/students/$STUDENT_ID/nova/messages" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body "{\"message\":\"Help me understand this\",\"topic_id\":\"$TOPIC_ID\"}"
```

The current implementation persists the message and a deterministic response. Connect an AI provider before production use.

### Subjects, journey, and topics — Screens 17–25, 47–48

```powershell
Invoke-RestMethod -Uri "$API/students/$STUDENT_ID/subjects" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Uri "$API/students/$STUDENT_ID/journey?subject=maths" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Uri "$API/students/$STUDENT_ID/journey?subject=literacy" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Uri "$API/students/$STUDENT_ID/topics/$TOPIC_ID" -Headers @{Authorization=$AUTH}
```

The general subject-topic catalog route remains available for authoring/catalog use:

```powershell
Invoke-RestMethod -Uri "$API/subjects/$SUBJECT_ID/topics?grade=4"
```

### Mission and package learning — Screens 26–39

```powershell
Invoke-RestMethod -Uri "$API/missions/$MISSION_ID"
Invoke-RestMethod -Uri "$API/learning-packages/$PACKAGE_ID" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Method Post -Uri "$API/students/$STUDENT_ID/missions/$MISSION_ID/start" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body '{}'
Invoke-RestMethod -Method Post -Uri "$API/students/$STUDENT_ID/missions/$MISSION_ID/complete" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body '{"score":100,"time_spent_seconds":300}'
Invoke-RestMethod -Uri "$API/students/$STUDENT_ID/missions/$MISSION_ID/review" -Headers @{Authorization=$AUTH}
```

## Test Arena

### List and start tests — Screens 40–42

```powershell
Invoke-RestMethod -Uri "$API/topics/$TOPIC_ID/tests"
$attempt = Invoke-RestMethod -Method Post -Uri "$API/students/$STUDENT_ID/tests/$TEST_ID/attempts" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body '{}'
$ATTEMPT_ID = $attempt.attempt_id
```

### Question, answer, result, and review — Screens 42–46

```powershell
$question = Invoke-RestMethod -Uri "$API/tests/attempts/$ATTEMPT_ID/questions/1"
Invoke-RestMethod -Method Post -Uri "$API/tests/attempts/$ATTEMPT_ID/answers" -ContentType 'application/json' -Body "{\"question_id\":\"$($question.id)\",\"selected_answer\":\"a\"}"
Invoke-RestMethod -Method Post -Uri "$API/tests/attempts/$ATTEMPT_ID/complete" -ContentType 'application/json' -Body '{}'
Invoke-RestMethod -Uri "$API/tests/attempts/$ATTEMPT_ID/result"
Invoke-RestMethod -Uri "$API/tests/attempts/$ATTEMPT_ID/review" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Uri "$API/students/$STUDENT_ID/extra-learning" -Headers @{Authorization=$AUTH}
```

## Challenge Screens

### Challenge catalog, battle, and leaderboard — Screens 49–54

```powershell
Invoke-RestMethod -Uri "$API/challenges"
Invoke-RestMethod -Uri "$API/challenges/$CHALLENGE_ID/opponents"
Invoke-RestMethod -Uri "$API/challenges/$CHALLENGE_ID/preview?opponent_id=$OPPONENT_ID"
$battle = Invoke-RestMethod -Method Post -Uri "$API/students/$STUDENT_ID/challenge-battles" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body "{\"challenge_id\":\"$CHALLENGE_ID\",\"opponent_id\":\"$OPPONENT_ID\"}"
$BATTLE_ID = $battle.battle_id
Invoke-RestMethod -Method Post -Uri "$API/challenge-battles/$BATTLE_ID/complete" -ContentType 'application/json' -Body '{"score":85}'
Invoke-RestMethod -Uri "$API/challenge-battles/$BATTLE_ID/result"
Invoke-RestMethod -Uri "$API/challenges/$CHALLENGE_ID/leaderboard?scope=global&student_id=$STUDENT_ID" -Headers @{Authorization=$AUTH}
```

The leaderboard currently derives XP from completed battle scores. `friends`, `India`, and `global` use the same dataset until social and geography data are introduced.

## Profile and Parent Screens

### Profile, journey, and break passes — Screens 55–57

```powershell
Invoke-RestMethod -Uri "$API/students/$STUDENT_ID/profile" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Uri "$API/students/$STUDENT_ID/profile/our-journey" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Uri "$API/students/$STUDENT_ID/break-passes" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Method Post -Uri "$API/students/$STUDENT_ID/break-passes" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body '{}'
```

### Parent PIN, student switch, overview, evidence, and plan — Screens 58–62

```powershell
Invoke-RestMethod -Method Post -Uri "$API/parent/pin/verify" -Headers @{Authorization=$AUTH} -ContentType 'application/json' -Body '{"pin":"1234"}'
Invoke-RestMethod -Uri "$API/parent/students" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Uri "$API/parent/overview" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Uri "$API/parent/evidence?student_id=$STUDENT_ID&topic_id=$TOPIC_ID" -Headers @{Authorization=$AUTH}
Invoke-RestMethod -Uri "$API/parent/plan?student_id=$STUDENT_ID&week=2026-09-28" -Headers @{Authorization=$AUTH}
```

## Curriculum and Content IDs

Student learning requires curriculum-backed topics. Use the content APIs to inspect the IDs needed above.

```powershell
Invoke-RestMethod -Uri "$API/curriculums?board=CBSE&grade=4"
Invoke-RestMethod -Uri "$API/curriculum/tree?board=CBSE&grade=4"
Invoke-RestMethod -Uri "$API/admin/content/packages?board=CBSE&grade=4"
Invoke-RestMethod -Uri "$API/admin/content/packages/$PACKAGE_ID"
```

Use `curriculum/tree` to obtain a topic ID and `admin/content/packages` to obtain a package ID. All learner APIs now reject topics outside the selected student's curriculum.

## Expected Limitations

- Password-reset requests and OTPs are persisted, but email/SMS delivery is intentionally marked `not_configured`/`development` until a provider is connected.
- Nova chat is persisted but uses a deterministic response until an AI service is connected.
- Leaderboard scopes share one global data set until friend and country data are modeled.
- Existing databases must run migration `0005`; it backfills curriculum links for existing topics and students where matching board/grade data exists.
