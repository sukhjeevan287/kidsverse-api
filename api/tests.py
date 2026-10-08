from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from api.models import (
    Parent, Student, Interest, Goal, AvatarCharacter, AvatarCategory,
    AvatarItem, Curriculum, Theme, Subject, Topic, TopicTier, Mission, Test, TestQuestion,
    Challenge, ChallengeQuestion, ChallengeOpponent, StudentStat, Concept,
    ConceptPackage, LearningContent, LearnBeforeTestStep, CheckForUnderstandingQuestion,
    ConceptTestQuestion, BattleQuestion
)
from api.jwt_utils import generate_jwt_token
from api.utils import hash_password


class KidsverseAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Seed minimal database objects
        self.interest = Interest.objects.create(key="space", name="Space")
        self.goal = Goal.objects.create(key="master_school_topics", name="Master school topics")
        
        self.character = AvatarCharacter.objects.create(slug="explorer-boy-1", name="Explorer Boy 1", base_image_url="http://example.com/char.png")
        self.category = AvatarCategory.objects.create(key="outfit", label="Outfit")
        self.avatar_item = AvatarItem.objects.create(category=self.category, slug="jacket", name="Jacket", thumbnail_url="http://example.com/item.png")

        self.subject = Subject.objects.create(name="Maths", slug="maths")
        self.topic = Topic.objects.create(subject=self.subject, grade_level="4", name="Fractions", slug="fractions")
        self.tier = TopicTier.objects.create(topic=self.topic, tier_key="school_syllabus", label="School Syllabus")
        self.mission = Mission.objects.create(topic=self.topic, tier=self.tier, name="Intro to Fractions", slug="intro-to-fractions", xp_reward=30)
        
        self.test_obj = Test.objects.create(topic=self.topic, name="Fractions Check", slug="fractions")
        self.question = TestQuestion.objects.create(test=self.test_obj, question_text="1/2 = ?", correct_answer="0.5", order_index=1)

        self.challenge = Challenge.objects.create(topic=self.topic, name="Fractions Duel", slug="fractions-duel")
        self.opponent = ChallengeOpponent.objects.create(challenge=self.challenge, name="Robo Rex", difficulty="medium")

    def test_full_application_flow(self):
        # 1. Signup Parent
        signup_res = self.client.post('/api/v1/auth/parent/signup', {
            "email": "parent1@example.com",
            "password": "Password123",
            "full_name": "Priya Shah"
        }, format='json')
        self.assertEqual(signup_res.status_code, 201)
        token = signup_res.data['token']
        parent_id = signup_res.data['parent']['id']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # 2. Login Parent
        login_res = self.client.post('/api/v1/auth/parent/login', {
            "email": "parent1@example.com",
            "password": "Password123"
        }, format='json')
        self.assertEqual(login_res.status_code, 200)

        # 3. Get Parent Me
        me_res = self.client.get('/api/v1/parent/me')
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.data['email'], "parent1@example.com")

        # 4. Create Student
        student_res = self.client.post('/api/v1/students', {"name": "Aarav"}, format='json')
        self.assertEqual(student_res.status_code, 201)
        student_id = student_res.data['id']

        # 5. Grade-board patch
        gb_res = self.client.patch(f'/api/v1/students/{student_id}/grade-board', {
            "grade": "4",
            "board": "CBSE"
        }, format='json')
        self.assertEqual(gb_res.status_code, 200)

        # 6. Save Avatar
        avatar_res = self.client.put(f'/api/v1/students/{student_id}/avatar', {
            "character_id": str(self.character.id),
            "outfit_item_id": str(self.avatar_item.id)
        }, format='json')
        self.assertEqual(avatar_res.status_code, 200)

        # 7. Set Interests & Goals
        int_res = self.client.put(f'/api/v1/students/{student_id}/interests', {
            "interest_ids": [str(self.interest.id)]
        }, format='json')
        self.assertEqual(int_res.status_code, 200)

        goal_res = self.client.put(f'/api/v1/students/{student_id}/goals', {
            "goal_ids": [str(self.goal.id)]
        }, format='json')
        self.assertEqual(goal_res.status_code, 200)

        # 8. Greet Nova
        greet_res = self.client.post(f'/api/v1/students/{student_id}/nova/greet')
        self.assertEqual(greet_res.status_code, 200)

        # 9. Get Home Hydration
        home_res = self.client.get(f'/api/v1/students/{student_id}/home')
        self.assertEqual(home_res.status_code, 200)
        self.assertIn("greeting", home_res.data)

        # 10. Complete Mission & Server XP calculation
        complete_m_res = self.client.post(f'/api/v1/students/{student_id}/missions/{self.mission.id}/complete', {
            "score": 100.0,
            "time_spent_seconds": 300
        }, format='json')
        self.assertEqual(complete_m_res.status_code, 200)
        self.assertEqual(complete_m_res.data['xp_awarded'], 30)

        stat = StudentStat.objects.get(student_id=student_id)
        self.assertEqual(stat.total_xp, 30)
        self.assertEqual(stat.day_streak, 1)

        # 11. Profile Check
        prof_res = self.client.get(f'/api/v1/students/{student_id}/profile')
        self.assertEqual(prof_res.status_code, 200)
        self.assertEqual(prof_res.data['total_xp'], 30)

    def test_student_ownership_forbidden(self):
        # Create Parent 1 & Student 1
        p1 = Parent.objects.create(email="p1@example.com", password_hash="hash")
        s1 = Student.objects.create(parent=p1, name="Student 1")

        # Create Parent 2
        p2 = Parent.objects.create(email="p2@example.com", password_hash="hash")
        token_p2 = generate_jwt_token(p2.id)

        # Parent 2 tries to access Student 1's profile -> should return 403 Forbidden
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_p2}')
        forbidden_res = self.client.get(f'/api/v1/students/{s1.id}/profile')
        self.assertEqual(forbidden_res.status_code, 403)
        self.assertEqual(forbidden_res.json()['error']['code'], "FORBIDDEN")

    def test_student_learning_path_is_scoped_to_curriculum(self):
        parent = Parent.objects.create(email="curriculum@example.com", password_hash="hash")
        token = generate_jwt_token(parent.id)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        cbse_grade_4 = Curriculum.objects.create(name="CBSE - Grade 4", code="cbse-grade-4", board="CBSE", grade="Grade 4")
        icse_grade_4 = Curriculum.objects.create(name="ICSE - Grade 4", code="icse-grade-4", board="ICSE", grade="Grade 4")
        maths = Subject.objects.create(name="Mathematics", slug="mathematics")
        maths.curricula.add(cbse_grade_4, icse_grade_4)
        cbse_topic = Topic.objects.create(subject=maths, curriculum=cbse_grade_4, board="CBSE", grade_level="Grade 4", name="CBSE Fractions", slug="cbse-fractions")
        icse_topic = Topic.objects.create(subject=maths, curriculum=icse_grade_4, board="ICSE", grade_level="Grade 4", name="ICSE Fractions", slug="icse-fractions")
        student = Student.objects.create(parent=parent, name="Aarav", grade="Grade 4", board="CBSE", curriculum=cbse_grade_4)

        subjects_res = self.client.get(f'/api/v1/students/{student.id}/subjects')
        self.assertEqual(subjects_res.status_code, 200)
        self.assertEqual(len(subjects_res.data['subjects']), 1)

        learning_path_res = self.client.get(f'/api/v1/students/{student.id}/learning-path')
        self.assertEqual(learning_path_res.status_code, 200)
        self.assertEqual(learning_path_res.data['subjects'][0]['topics'][0]['id'], str(cbse_topic.id))

        foreign_topic_res = self.client.get(f'/api/v1/students/{student.id}/topics/{icse_topic.id}')
        self.assertEqual(foreign_topic_res.status_code, 404)

    def test_settings_break_passes_and_parent_pin(self):
        parent = Parent.objects.create(email="screens@example.com", password_hash="hash", pin_hash=hash_password("1234"))
        student = Student.objects.create(parent=parent, name="Diya")
        token = generate_jwt_token(parent.id)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        settings_res = self.client.patch(f'/api/v1/students/{student.id}/settings', {"settings": {"music": False}}, format='json')
        self.assertEqual(settings_res.status_code, 200)
        self.assertEqual(settings_res.data['settings']['music'], False)

        break_res = self.client.post(f'/api/v1/students/{student.id}/break-passes')
        self.assertEqual(break_res.status_code, 200)
        self.assertEqual(break_res.data['available_count'], 2)

        pin_res = self.client.post('/api/v1/parent/pin/verify', {"pin": "1234"}, format='json')
        self.assertEqual(pin_res.status_code, 200)
        self.assertTrue(pin_res.data['verified'])

    def test_curriculum_content_feed_and_retrieval(self):
        # 1. Feed complete payload matching the portal
        payload = {
            "curriculum": {
                "grade": "Grade 4",
                "board": "CBSE",
                "subject": "Mathematics",
                "topic": "Fractions"
            },
            "concept": {
                "name": "Equivalent Fractions",
                "learning_objective": "Understand that fractions that look different can represent the same value."
            },
            "theme_interest": "Space",
            "content_type": "concept_package",
            "learning_content": {
                "teaching_method": "Visual fuel tank partitioning in orbit",
                "image_url": "https://assets.kidsverse.app/concepts/space_fractions.png",
                "image_prompt": "Astronaut dividing fuel canisters into 4 equal segments",
                "explanation": "If an astronaut takes 2 out of 4 fuel pods (2/4), that is the exact same amount as half a fuel cell (1/2)!",
                "hints": [
                    "Divide both the top and bottom number by 2.",
                    "Look at the visual fuel gauge.",
                    "Half of four is two."
                ],
                "nova_script": "Commander, look at the fuel reserves! Can you help calibrate them?",
                "nova_feedback": "Spectacular navigation! You've mastered equivalent fractions."
            },
            "learn_before_test": {
                "required": True,
                "order": ["understand", "example", "remember"],
                "starts_quiz_after": "remember",
                "steps": [
                    {
                        "step_key": "understand",
                        "title": "Introduce the idea: Fractions represent parts of a whole",
                        "teaching_text": "Imagine a fuel tank divided into 4 equal pods. Taking 2 pods out of 4 fills up half the tank!",
                        "key_idea": "Fractions with different numbers can describe the same amount.",
                        "image_url": "https://assets.kidsverse.app/concepts/step1_understand.png",
                        "image_prompt": "Astronaut looking at two fuel tanks, one divided into 2 and one into 4",
                        "nova_script": "Look closely Commander: 2 out of 4 is the exact same amount as 1 out of 2!",
                        "mini_question": {
                            "question": "If you take 2 out of 4 equal pods, what fraction do you have?",
                            "options": ["1/2", "1/4", "3/4"],
                            "answer": "1/2",
                            "explanation": "2/4 simplifies to 1/2."
                        }
                    },
                    {
                        "step_key": "example",
                        "title": "Show it step by step: Multiplying top and bottom",
                        "teaching_text": "Multiply numerator and denominator by 2: 1/2 x (2/2) = 2/4.",
                        "key_idea": "Multiplying or dividing top and bottom by the same number keeps the value equal.",
                        "image_url": "https://assets.kidsverse.app/concepts/step2_example.png",
                        "image_prompt": "Holographic math display showing multiplication of fraction",
                        "nova_script": "Multiplying both parts by 2 makes an equivalent fraction!",
                        "mini_question": {
                            "question": "What is 1/2 multiplied by 3/3?",
                            "options": ["3/6", "2/6", "3/5"],
                            "answer": "3/6",
                            "explanation": "1*3 = 3 and 2*3 = 6, yielding 3/6."
                        }
                    },
                    {
                        "step_key": "remember",
                        "title": "Make it memorable: The Golden Rule",
                        "teaching_text": "Whatever you do to the top, you must do to the bottom!",
                        "key_idea": "Always keep top and bottom balanced.",
                        "image_url": "https://assets.kidsverse.app/concepts/step3_remember.png",
                        "image_prompt": "Balance scale floating in zero gravity",
                        "nova_script": "Remember the Golden Rule and you'll always win the battle!",
                        "mini_question": {
                            "question": "What is the golden rule for equivalent fractions?",
                            "options": [
                                "Do the same to top and bottom",
                                "Only add to top",
                                "Multiply only bottom"
                            ],
                            "answer": "Do the same to top and bottom",
                            "explanation": "Applying the same factor to top and bottom maintains fraction value."
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
            ],
            "test_questions": {
                "one_time": False,
                "questions": [
                    {
                        "question": "If a space pod uses 3/6 of its fuel, what fraction has it used?",
                        "options": ["1/2", "1/3", "2/3", "3/4"],
                        "answer": "1/2",
                        "difficulty": "Medium",
                        "marks": 2,
                        "explanation": "3 divided by 3 is 1, and 6 divided by 3 is 2."
                    }
                ]
            },
            "battle_questions": [
                {
                    "question": "Quick battle: Is 4/8 equal to 1/2?",
                    "options": ["Yes", "No"],
                    "answer": "Yes",
                    "difficulty": "Hard",
                    "xp": 20,
                    "explanation": "Both numerator and denominator can be divided by 4."
                }
            ],
            "challenge": {
                "one_time": False,
                "questions": [
                    {
                        "question": "Boss challenge: Find the missing numerator: ?/10 = 1/2",
                        "options": ["5", "2", "4", "6"],
                        "answer": "5",
                        "difficulty": "Hard",
                        "xp": 35,
                        "explanation": "Half of 10 is 5.",
                        "nova_feedback": "Incredible! You defeated the challenge!"
                    }
                ]
            }
        }

        # Clear credentials for public/admin endpoint
        self.client.credentials()

        # Ingest content package
        feed_res = self.client.post('/api/v1/admin/content/feed', payload, format='json')
        self.assertEqual(feed_res.status_code, 201)
        data = feed_res.data['data']
        self.assertEqual(data['subject'], "Mathematics")
        self.assertEqual(data['board'], "CBSE")
        self.assertEqual(data['grade'], "Grade 4")
        self.assertEqual(data['concept'], "Equivalent Fractions")
        self.assertEqual(data['theme'], "Space")
        self.assertEqual(data['questions_saved']['total'], 4)
        self.assertEqual(data['learn_before_test_steps_saved'], 3)
        self.assertIn('curriculum_id', data)
        self.assertIn('theme_id', data)
        self.assertIn('learning_content_id', data)
        self.assertIn('mission_id', data)
        self.assertIn('test_id', data)
        self.assertIn('challenge_id', data)

        package_id = data['package_id']

        # Verify database records are properly segregated into dedicated relational tables
        self.assertTrue(Curriculum.objects.filter(board="CBSE", grade="Grade 4").exists())
        self.assertTrue(Theme.objects.filter(name="Space").exists())
        self.assertTrue(LearningContent.objects.filter(package_id=package_id).exists())
        self.assertEqual(LearnBeforeTestStep.objects.filter(package_id=package_id).count(), 3)
        self.assertEqual(
            list(LearnBeforeTestStep.objects.filter(package_id=package_id).order_by('order_index').values_list('step_key', flat=True)),
            ['understand', 'example', 'remember']
        )
        self.assertEqual(CheckForUnderstandingQuestion.objects.filter(package_id=package_id).count(), 1)
        self.assertEqual(ConceptTestQuestion.objects.filter(package_id=package_id).count(), 1)
        self.assertEqual(BattleQuestion.objects.filter(package_id=package_id).count(), 1)
        self.assertEqual(ChallengeQuestion.objects.filter(package_id=package_id).count(), 1)

        # Verify mission content received learn_before_test
        mission = Mission.objects.get(id=data['mission_id'])
        self.assertIn('learn_before_test', mission.content)
        self.assertEqual(len(mission.content['learn_before_test']['steps']), 3)

        # 2. Ingest a second package for the SAME concept but under a DIFFERENT theme ("Animals")
        payload_animals = dict(payload)
        payload_animals["theme_interest"] = "Animals"
        payload_animals["learning_content"] = {
            "teaching_method": "Jungle safari pizza division",
            "explanation": "Monkeys dividing fruit into equal shares",
            "hints": ["Each monkey gets an equal portion"],
            "nova_script": "Look at the animals sharing!",
            "nova_feedback": "Great animal care!"
        }
        feed_animals_res = self.client.post('/api/v1/admin/content/feed', payload_animals, format='json')
        self.assertEqual(feed_animals_res.status_code, 201)

        # Verify: Multiple themes for the same concept!
        concept_obj = Concept.objects.get(name="Equivalent Fractions")
        self.assertEqual(concept_obj.themes.count(), 2)
        theme_names = set(concept_obj.themes.values_list('name', flat=True))
        self.assertEqual(theme_names, {"Space", "Animals"})

        # 3. List Packages with filtering
        list_res = self.client.get('/api/v1/admin/content/packages?grade=Grade+4&board=CBSE&theme=Space')
        self.assertEqual(list_res.status_code, 200)
        self.assertGreaterEqual(list_res.data['count'], 1)
        self.assertEqual(list_res.data['packages'][0]['concept_name'], "Equivalent Fractions")
        self.assertEqual(list_res.data['packages'][0]['learn_steps_count'], 3)

        # 4. Get Package Detail (reconstructed from segregated tables)
        detail_res = self.client.get(f'/api/v1/admin/content/packages/{package_id}')
        self.assertEqual(detail_res.status_code, 200)
        pkg = detail_res.data
        self.assertEqual(pkg['curriculum']['grade'], "Grade 4")
        self.assertEqual(pkg['curriculum']['board'], "CBSE")
        self.assertEqual(pkg['concept']['name'], "Equivalent Fractions")
        self.assertEqual(len(pkg['learn_before_test']['steps']), 3)
        self.assertEqual(pkg['learn_before_test']['steps'][0]['step_key'], 'understand')
        self.assertEqual(pkg['learn_before_test']['steps'][1]['step_key'], 'example')
        self.assertEqual(pkg['learn_before_test']['steps'][2]['step_key'], 'remember')
        self.assertEqual(len(pkg['check_for_understanding']), 1)
        self.assertEqual(len(pkg['test_questions']['questions']), 1)
        self.assertEqual(len(pkg['battle_questions']), 1)
        self.assertEqual(len(pkg['challenge']['questions']), 1)
        self.assertEqual(pkg['learning_content']['hints'][0], "Divide both the top and bottom number by 2.")

        # 5. Curriculum Tree check
        tree_res = self.client.get('/api/v1/curriculum/tree?grade=Grade+4&board=CBSE')
        self.assertEqual(tree_res.status_code, 200)
        self.assertGreaterEqual(tree_res.data['count'], 1)
        found_topic = any(t['name'] == "Fractions" for t in tree_res.data['topics'])
        self.assertTrue(found_topic)

        # 6. Curriculum Management Endpoints
        curricula_res = self.client.get('/api/v1/curriculums')
        self.assertEqual(curricula_res.status_code, 200)
        self.assertGreaterEqual(curricula_res.data['count'], 1)

        curriculum_id = data['curriculum_id']
        curr_detail_res = self.client.get(f'/api/v1/curriculums/{curriculum_id}')
        self.assertEqual(curr_detail_res.status_code, 200)
        self.assertEqual(curr_detail_res.data['board'], 'CBSE')
        self.assertEqual(curr_detail_res.data['grade'], 'Grade 4')

        # Add subject to curriculum
        add_subj_res = self.client.post(f'/api/v1/curriculums/{curriculum_id}/subjects', {"name": "Science"}, format='json')
        self.assertEqual(add_subj_res.status_code, 201)

        # 7. Themes Endpoint
        themes_res = self.client.get('/api/v1/themes')
        self.assertEqual(themes_res.status_code, 200)
        self.assertGreaterEqual(themes_res.data['count'], 2)

        # Create new theme
        create_theme_res = self.client.post('/api/v1/themes', {"name": "Robots"}, format='json')
        self.assertEqual(create_theme_res.status_code, 201)
