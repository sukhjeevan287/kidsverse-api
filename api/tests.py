from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from api.models import (
    Parent, Student, Interest, Goal, AvatarCharacter, AvatarCategory,
    AvatarItem, Subject, Topic, TopicTier, Mission, Test, TestQuestion,
    Challenge, ChallengeOpponent, StudentStat
)
from api.jwt_utils import generate_jwt_token


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
