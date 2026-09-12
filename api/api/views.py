import datetime
from api.utils import hash_password, verify_password
from api.jwt_utils import generate_jwt_token
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from api.models import (
    Parent, Student, Interest, StudentInterest, Goal, StudentGoal,
    OnboardingStep, Subject, SubjectGradeAvailability, StudentSubjectUnlock,
    Topic, TopicJourneyMeta, StudentTopicProgress, CompanionActivity,
    StudentCompanionActivityLog, TopicTier, Mission, MissionProgress,
    Test, TestQuestion, TestAttempt, TestAttemptAnswer, ExtraLearningRecommendation,
    Challenge, ChallengeOpponent, ChallengeBattle, JourneyMilestone,
    StudentJourneyProgress, StudentCard, NovaInteraction, AvatarCharacter,
    AvatarCategory, AvatarItem, StudentAvatar, StudentAvatarUnlock, StudentStat,
    MissionRecommendation
)
from api.serializers import (
    ParentSerializer, ParentSignupSerializer, ParentLoginSerializer,
    StudentSerializer, GradeBoardSerializer, InterestSerializer, GoalSerializer,
    AvatarCharacterSerializer, AvatarItemSerializer, SaveAvatarSerializer,
    SetInterestsSerializer, SetGoalsSerializer, SubjectSerializer, TopicSerializer,
    MissionSerializer, TestSerializer, TestQuestionSerializer, ChallengeSerializer,
    ChallengeOpponentSerializer, StudentCardSerializer
)


def update_student_xp_streak(student, xp_gained):
    stats, _ = StudentStat.objects.get_or_create(student=student)
    stats.total_xp += xp_gained
    today = timezone.now().date()
    if stats.last_active_date is None:
        stats.day_streak = 1
    elif stats.last_active_date == today - datetime.timedelta(days=1):
        stats.day_streak += 1
    elif stats.last_active_date < today - datetime.timedelta(days=1):
        stats.day_streak = 1
    stats.last_active_date = today
    # Level formula: level = 1 + (total_xp // 1000)
    stats.level = 1 + (stats.total_xp // 1000)
    stats.save()
    return stats


# --- AUTH & PARENT ACCOUNTS ---

class ParentSignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ParentSignupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        if Parent.objects.filter(email=email).exists():
            return Response({"detail": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        parent = Parent.objects.create(
            email=email,
            password_hash=hash_password(serializer.validated_data['password']),
            full_name=serializer.validated_data.get('full_name', ''),
            phone=serializer.validated_data.get('phone', '')
        )
        token = generate_jwt_token(parent.id)
        return Response({
            "parent": ParentSerializer(parent).data,
            "token": token
        }, status=status.HTTP_201_CREATED)


class ParentLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ParentLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            parent = Parent.objects.get(email=email)
        except Parent.DoesNotExist:
            return Response({"detail": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        if not verify_password(password, parent.password_hash):
            return Response({"detail": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        parent.last_login_at = timezone.now()
        parent.save()

        token = generate_jwt_token(parent.id)
        return Response({
            "parent": ParentSerializer(parent).data,
            "token": token
        }, status=status.HTTP_200_OK)


class ParentLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class ParentMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(ParentSerializer(request.parent).data)


class ParentStudentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        students = Student.objects.filter(parent=request.parent, is_active=True)
        res = []
        for s in students:
            data = {
                "id": str(s.id),
                "name": s.name,
                "grade": s.grade,
                "board": s.board,
                "avatar": s.avatar.character.base_image_url if hasattr(s, 'avatar') and s.avatar else None,
                "onboarding_completed": s.onboarding_completed_at is not None
            }
            if hasattr(s, 'avatar') and s.avatar:
                data["avatar"] = {
                    "character_id": str(s.avatar.character.id),
                    "thumbnail_url": s.avatar.character.base_image_url
                }
            res.append(data)
        return Response({"students": res})


class ParentOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        students = Student.objects.filter(parent=request.parent, is_active=True)
        res = []
        for s in students:
            stats = StudentStat.objects.filter(student=s).first()
            recent_attempt = TestAttempt.objects.filter(student=s, status='completed').order_by('-completed_at').first()
            
            subjects_list = []
            for subj in Subject.objects.filter(is_active=True):
                topics = Topic.objects.filter(subject=subj)
                if topics.exists():
                    comp = StudentTopicProgress.objects.filter(student=s, topic__in=topics, status='completed').count()
                    pct = int((comp / topics.count()) * 100)
                else:
                    pct = 0
                subjects_list.append({
                    "subject": subj.name,
                    "progress_percent": pct
                })

            res.append({
                "student_id": str(s.id),
                "name": s.name,
                "day_streak": stats.day_streak if stats else 0,
                "total_xp": stats.total_xp if stats else 0,
                "subjects": subjects_list,
                "recent_test_score": float(recent_attempt.score) if recent_attempt and recent_attempt.score else 0
            })
        return Response({"students": res})


# --- STUDENTS & ONBOARDING ---

class CreateStudentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get('name')
        if not name:
            return Response({"detail": "name is required"}, status=status.HTTP_400_BAD_REQUEST)

        student = Student.objects.create(
            parent=request.parent,
            name=name
        )
        StudentStat.objects.create(student=student)
        OnboardingStep.objects.create(student=student, step_key='child')

        return Response({
            "id": str(student.id),
            "parent_id": str(student.parent.id),
            "name": student.name,
            "onboarding_completed_at": None,
            "created_at": student.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)


class UpdateGradeBoardView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, studentId):
        student = Student.objects.get(id=studentId)
        serializer = GradeBoardSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        student.grade = serializer.validated_data['grade']
        student.board = serializer.validated_data['board']
        student.save()

        OnboardingStep.objects.get_or_create(student=student, step_key='grade_board')
        return Response(StudentSerializer(student).data)


class AvatarCharactersView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        chars = AvatarCharacter.objects.filter(is_active=True).order_index() if hasattr(AvatarCharacter.objects, 'order_index') else AvatarCharacter.objects.filter(is_active=True).order_by('order_index')
        return Response({"characters": AvatarCharacterSerializer(chars, many=True).data})


class AvatarItemsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cat_key = request.query_params.get('category')
        items = AvatarItem.objects.filter(is_active=True)
        if cat_key:
            items = items.filter(category__key=cat_key)
        return Response({"items": AvatarItemSerializer(items, many=True).data})


class SaveStudentAvatarView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, studentId):
        student = Student.objects.get(id=studentId)
        serializer = SaveAvatarSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        character = AvatarCharacter.objects.get(id=serializer.validated_data['character_id'])
        outfit = AvatarItem.objects.filter(id=serializer.validated_data.get('outfit_item_id')).first()
        hair = AvatarItem.objects.filter(id=serializer.validated_data.get('hair_item_id')).first()
        acc = AvatarItem.objects.filter(id=serializer.validated_data.get('accessory_item_id')).first()

        avatar, _ = StudentAvatar.objects.update_or_create(
            student=student,
            defaults={
                'character': character,
                'outfit_item': outfit,
                'hair_item': hair,
                'accessory_item': acc,
            }
        )
        OnboardingStep.objects.get_or_create(student=student, step_key='avatar')

        return Response({
            "character_id": str(character.id),
            "outfit_item_id": str(outfit.id) if outfit else None,
            "hair_item_id": str(hair.id) if hair else None,
            "accessory_item_id": str(acc.id) if acc else None,
            "updated_at": avatar.updated_at.isoformat()
        })


class InterestsCatalogView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        interests = Interest.objects.filter(is_active=True).order_by('order_index')
        return Response({"interests": InterestSerializer(interests, many=True).data})


class StudentInterestsView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, studentId):
        student = Student.objects.get(id=studentId)
        serializer = SetInterestsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ids = serializer.validated_data['interest_ids']
        StudentInterest.objects.filter(student=student).delete()
        new_objs = [StudentInterest(student=student, interest_id=i_id) for i_id in ids]
        StudentInterest.objects.bulk_create(new_objs)

        OnboardingStep.objects.get_or_create(student=student, step_key='interests')

        return Response({
            "selected_count": len(ids),
            "interest_ids": [str(i) for i in ids]
        })


class GoalsCatalogView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        goals = Goal.objects.filter(is_active=True).order_by('order_index')
        return Response({"goals": GoalSerializer(goals, many=True).data})


class StudentGoalsView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, studentId):
        student = Student.objects.get(id=studentId)
        serializer = SetGoalsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ids = serializer.validated_data['goal_ids']
        StudentGoal.objects.filter(student=student).delete()
        new_objs = [StudentGoal(student=student, goal_id=g_id) for g_id in ids]
        StudentGoal.objects.bulk_create(new_objs)

        OnboardingStep.objects.get_or_create(student=student, step_key='goals')

        return Response({
            "goal_ids": [str(g) for g in ids]
        })


class CompleteOnboardingStepView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, studentId, stepKey):
        student = Student.objects.get(id=studentId)
        step, _ = OnboardingStep.objects.get_or_create(student=student, step_key=stepKey)
        return Response({
            "step_key": stepKey,
            "completed_at": step.completed_at.isoformat()
        })


class OnboardingStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId):
        student = Student.objects.get(id=studentId)
        steps = list(OnboardingStep.objects.filter(student=student).values_list('step_key', flat=True))
        all_steps = ['child', 'grade_board', 'avatar', 'interests', 'goals', 'lobby', 'nova']
        
        next_step = None
        for s in all_steps:
            if s not in steps:
                next_step = s
                break

        return Response({
            "completed_steps": steps,
            "next_step": next_step,
            "is_complete": student.onboarding_completed_at is not None
        })


class NovaGreetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, studentId):
        student = Student.objects.get(id=studentId)
        student.onboarding_completed_at = timezone.now()
        student.save()

        OnboardingStep.objects.get_or_create(student=student, step_key='nova')

        NovaInteraction.objects.create(
            student=student,
            message="Greeting",
            response=f"Hey {student.name}! I'm Nova..."
        )

        return Response({
            "message": f"Hey {student.name}! I'm Nova, your AI learning companion!",
            "onboarding_completed_at": student.onboarding_completed_at.isoformat()
        })


# --- HOME ---

class StudentHomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId):
        student = Student.objects.get(id=studentId)
        stats, _ = StudentStat.objects.get_or_create(student=student)

        # Recommended mission
        rec = MissionRecommendation.objects.filter(student=student, is_active=True).first()
        rec_data = None
        if rec and rec.mission:
            rec_data = {
                "mission_id": str(rec.mission.id),
                "title": rec.mission.name,
                "subject": rec.mission.topic.subject.name,
                "topic": rec.mission.topic.name,
                "duration_minutes": 8,
                "reason": rec.reason_text or "Recommended based on your learning path",
                "xp_reward": rec.mission.xp_reward,
                "progress_percent": 0
            }
        else:
            first_mission = Mission.objects.first()
            if first_mission:
                rec_data = {
                    "mission_id": str(first_mission.id),
                    "title": first_mission.name,
                    "subject": first_mission.topic.subject.name,
                    "topic": first_mission.topic.name,
                    "duration_minutes": 8,
                    "reason": "Start your journey with this mission!",
                    "xp_reward": first_mission.xp_reward,
                    "progress_percent": 0
                }

        subjects = Subject.objects.filter(is_active=True).order_by('order_index')
        subj_serializer = SubjectSerializer(subjects, many=True, context={'student': student})

        return Response({
            "greeting": f"Ready for today's adventure, {student.name}?",
            "stats": {
                "day_streak": stats.day_streak,
                "total_xp": stats.total_xp,
                "level": stats.level
            },
            "recommended_mission": rec_data,
            "subjects": subj_serializer.data
        })


# --- LEARN ---

class StudentSubjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId):
        student = Student.objects.get(id=studentId)
        subjects = Subject.objects.filter(is_active=True).order_by('order_index')
        serializer = SubjectSerializer(subjects, many=True, context={'student': student})
        return Response({"subjects": serializer.data})


class SubjectTopicsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, subjectId):
        grade = request.query_params.get('grade')
        topics = Topic.objects.filter(subject_id=subjectId)
        if grade:
            topics = topics.filter(grade_level=grade)
        topics = topics.order_by('order_index')
        
        student = getattr(request, 'student', None)
        serializer = TopicSerializer(topics, many=True, context={'student': student})
        return Response({"topics": serializer.data})


class StudentTopicDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId, topicId):
        student = Student.objects.get(id=studentId)
        topic = Topic.objects.get(id=topicId)

        tiers_list = []
        for tier in TopicTier.objects.filter(topic=topic).order_by('order_index'):
            missions_in_tier = Mission.objects.filter(topic=topic, tier=tier).order_by('order_index')
            m_names = list(missions_in_tier.values_list('name', flat=True))
            
            # Check tier status
            comp_count = MissionProgress.objects.filter(student=student, mission__in=missions_in_tier, status='completed').count()
            if comp_count == len(m_names) and len(m_names) > 0:
                t_status = 'completed'
            elif comp_count > 0:
                t_status = 'in_progress'
            else:
                t_status = 'unlocked' if tier.required_plan == 'free' else 'locked'

            tiers_list.append({
                "tier_key": tier.tier_key,
                "label": tier.label,
                "status": t_status,
                "missions": m_names
            })

        nodes_list = []
        all_missions = Mission.objects.filter(topic=topic).order_by('order_index')
        for m in all_missions:
            mp = MissionProgress.objects.filter(student=student, mission=m).first()
            nodes_list.append({
                "mission_id": str(m.id),
                "order_index": m.order_index,
                "name": m.name,
                "status": mp.status if mp else 'locked',
                "stars": mp.stars if mp else 0
            })

        return Response({
            "id": str(topic.id),
            "name": topic.name,
            "grade_level": topic.grade_level,
            "subject": topic.subject.name,
            "description": topic.description,
            "tiers": tiers_list,
            "nodes": nodes_list
        })


class MissionDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, missionId):
        mission = Mission.objects.get(id=missionId)
        return Response({
            "id": str(mission.id),
            "topic_id": str(mission.topic.id),
            "tier_key": mission.tier.tier_key,
            "name": mission.name,
            "xp_reward": mission.xp_reward,
            "content": mission.content or {"type": "interactive_lesson", "steps": []}
        })


class StartMissionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, studentId, missionId):
        student = Student.objects.get(id=studentId)
        mission = Mission.objects.get(id=missionId)

        prog, _ = MissionProgress.objects.get_or_create(student=student, mission=mission)
        prog.status = 'in_progress'
        if not prog.started_at:
            prog.started_at = timezone.now()
        prog.save()

        return Response({
            "status": "in_progress",
            "started_at": prog.started_at.isoformat()
        })


class CompleteMissionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, studentId, missionId):
        student = Student.objects.get(id=studentId)
        mission = Mission.objects.get(id=missionId)

        score = float(request.data.get('score', 100.0))
        stars = 3 if score >= 80 else (2 if score >= 50 else 1)

        prog, _ = MissionProgress.objects.get_or_create(student=student, mission=mission)
        prog.status = 'completed'
        prog.score = score
        prog.stars = stars
        prog.completed_at = timezone.now()
        prog.save()

        # Server-side XP update
        stats = update_student_xp_streak(student, mission.xp_reward)

        # Topic progress percentage
        topic_missions = Mission.objects.filter(topic=mission.topic)
        completed_count = MissionProgress.objects.filter(student=student, mission__in=topic_missions, status='completed').count()
        topic_pct = int((completed_count / topic_missions.count()) * 100) if topic_missions.exists() else 100

        # Next mission
        next_m = Mission.objects.filter(topic=mission.topic, order_index__gt=mission.order_index).order_by('order_index').first()

        return Response({
            "status": "completed",
            "stars": stars,
            "xp_awarded": mission.xp_reward,
            "completed_at": prog.completed_at.isoformat(),
            "next_mission_id": str(next_m.id) if next_m else None,
            "topic_progress_percent": topic_pct
        })


# --- JOURNEY ---

class StudentJourneyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId):
        student = Student.objects.get(id=studentId)
        subject_slug = request.query_params.get('subject', 'literacy')
        
        subject = Subject.objects.filter(slug__iexact=subject_slug).first()
        if not subject:
            subject = Subject.objects.first()

        worlds = []
        if subject:
            topics = Topic.objects.filter(subject=subject).order_by('order_index')
            for t in topics:
                tp = StudentTopicProgress.objects.filter(student=student, topic=t).first()
                meta = getattr(t, 'journey_meta', None)
                worlds.append({
                    "topic_id": str(t.id),
                    "world_name": meta.world_name if meta else t.name,
                    "tagline": meta.tagline if meta else t.description,
                    "status": tp.status if tp else 'locked',
                    "map_x": float(meta.map_x) if meta and meta.map_x else 10.0,
                    "map_y": float(meta.map_y) if meta and meta.map_y else 20.0
                })

        companion_acts = CompanionActivity.objects.filter(subject=subject) if subject else CompanionActivity.objects.all()
        acts_list = [{"id": str(a.id), "name": a.name} for a in companion_acts]

        return Response({
            "subject": subject.name if subject else "General",
            "tagline": f"Explore {subject.name} with Nova!",
            "worlds": worlds,
            "companion_activities": acts_list
        })


class CompleteCompanionActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, studentId, activityId):
        student = Student.objects.get(id=studentId)
        activity = CompanionActivity.objects.get(id=activityId)

        log = StudentCompanionActivityLog.objects.create(student=student, activity=activity)
        return Response({"completed_at": log.completed_at.isoformat()})


# --- TEST ---

class TopicTestsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, topicId):
        tests = Test.objects.filter(topic_id=topicId)
        return Response({"tests": TestSerializer(tests, many=True).data})


class TestDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, testId):
        test = Test.objects.get(id=testId)
        return Response(TestSerializer(test).data)


class StartTestAttemptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, studentId, testId):
        student = Student.objects.get(id=studentId)
        test = Test.objects.get(id=testId)

        attempt = TestAttempt.objects.create(student=student, test=test, status='in_progress')
        first_q = test.questions.order_by('order_index').first()

        first_q_data = None
        if first_q:
            first_q_data = {
                "id": str(first_q.id),
                "question_text": first_q.question_text,
                "question_type": first_q.question_type,
                "options": first_q.options,
                "order_index": first_q.order_index
            }

        return Response({
            "attempt_id": str(attempt.id),
            "status": attempt.status,
            "started_at": attempt.started_at.isoformat(),
            "first_question": first_q_data
        }, status=status.HTTP_201_CREATED)


class GetTestQuestionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, attemptId, order):
        attempt = TestAttempt.objects.get(id=attemptId)
        q = TestQuestion.objects.filter(test=attempt.test, order_index=order).first()
        if not q:
            return Response({"detail": "Question not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(TestQuestionSerializer(q).data)


class SubmitTestAnswerView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, attemptId):
        attempt = TestAttempt.objects.get(id=attemptId)
        q_id = request.data.get('question_id')
        selected = request.data.get('selected_answer')

        question = TestQuestion.objects.get(id=q_id)
        is_correct = (str(question.correct_answer).strip().lower() == str(selected).strip().lower())

        TestAttemptAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={'selected_answer': selected, 'is_correct': is_correct}
        )

        next_q = TestQuestion.objects.filter(test=attempt.test, order_index__gt=question.order_index).order_by('order_index').first()

        return Response({
            "is_correct": is_correct,
            "next_question_id": str(next_q.id) if next_q else None
        })


class CompleteTestAttemptView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, attemptId):
        attempt = TestAttempt.objects.get(id=attemptId)
        answers = TestAttemptAnswer.objects.filter(attempt=attempt)
        total_questions = attempt.test.questions.count()
        correct_count = answers.filter(is_correct=True).count()

        score = float((correct_count / total_questions) * 100) if total_questions > 0 else 0.0

        attempt.status = 'completed'
        attempt.score = score
        attempt.completed_at = timezone.now()
        attempt.save()

        # Update student stats server-side
        xp_awarded = int(score * 0.5)
        update_student_xp_streak(attempt.student, xp_awarded)

        # Recommendation if score < 80
        if score < 80:
            rec_mission = Mission.objects.filter(topic=attempt.test.topic).last()
            if rec_mission:
                ExtraLearningRecommendation.objects.get_or_create(
                    attempt=attempt,
                    mission=rec_mission,
                    reason="Targeted practice for missed test questions"
                )

        return Response({
            "status": "completed",
            "score": score,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "completed_at": attempt.completed_at.isoformat()
        })


class GetTestResultView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, attemptId):
        attempt = TestAttempt.objects.get(id=attemptId)
        answers = TestAttemptAnswer.objects.filter(attempt=attempt)
        total_questions = attempt.test.questions.count()
        correct_count = answers.filter(is_correct=True).count()

        recs = ExtraLearningRecommendation.objects.filter(attempt=attempt)
        recs_list = [{
            "mission_id": str(r.mission.id),
            "name": r.mission.name,
            "reason": r.reason
        } for r in recs]

        return Response({
            "score": float(attempt.score) if attempt.score else 0.0,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "xp_awarded": int((attempt.score or 0) * 0.5),
            "extra_learning": recs_list
        })


# --- CHALLENGE ---

class ListChallengesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        challenges = Challenge.objects.all()
        return Response({"challenges": ChallengeSerializer(challenges, many=True).data})


class ChallengeOpponentsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, challengeId):
        opponents = ChallengeOpponent.objects.filter(challenge_id=challengeId)
        return Response({"opponents": ChallengeOpponentSerializer(opponents, many=True).data})


class PreviewChallengeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, challengeId):
        challenge = Challenge.objects.get(id=challengeId)
        opponent_id = request.query_params.get('opponent_id')
        opponent = ChallengeOpponent.objects.filter(id=opponent_id).first() if opponent_id else challenge.opponents.first()

        return Response({
            "challenge": challenge.name,
            "opponent": {
                "name": opponent.name if opponent else "Robo Rex",
                "difficulty": opponent.difficulty if opponent else "medium"
            },
            "rules": "First to 5 correct answers wins.",
            "xp_reward": 50
        })


class StartChallengeBattleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, studentId):
        student = Student.objects.get(id=studentId)
        challenge_id = request.data.get('challenge_id')
        opponent_id = request.data.get('opponent_id')

        challenge = Challenge.objects.get(id=challenge_id)
        opponent = ChallengeOpponent.objects.get(id=opponent_id)

        battle = ChallengeBattle.objects.create(
            student=student,
            challenge=challenge,
            opponent=opponent,
            status='in_progress',
            started_at=timezone.now()
        )

        return Response({
            "battle_id": str(battle.id),
            "status": battle.status,
            "started_at": battle.started_at.isoformat()
        }, status=status.HTTP_201_CREATED)


class CompleteChallengeBattleView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, battleId):
        battle = ChallengeBattle.objects.get(id=battleId)
        score = float(request.data.get('score', 85.0))
        result = 'win' if score >= 50 else 'loss'

        battle.status = 'completed'
        battle.score = score
        battle.result = result
        battle.completed_at = timezone.now()
        battle.save()

        xp_awarded = 50 if result == 'win' else 10
        update_student_xp_streak(battle.student, xp_awarded)

        return Response({
            "status": "completed",
            "result": result,
            "score": score,
            "xp_awarded": xp_awarded,
            "completed_at": battle.completed_at.isoformat()
        })


class ChallengeBattleResultView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, battleId):
        battle = ChallengeBattle.objects.get(id=battleId)
        xp_awarded = 50 if battle.result == 'win' else 10
        return Response({
            "status": battle.status,
            "result": battle.result,
            "score": float(battle.score) if battle.score else 0.0,
            "xp_awarded": xp_awarded,
            "completed_at": battle.completed_at.isoformat() if battle.completed_at else None
        })


# --- PROFILE ---

class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId):
        student = Student.objects.get(id=studentId)
        stats, _ = StudentStat.objects.get_or_create(student=student)
        avatar_url = student.avatar.character.base_image_url if hasattr(student, 'avatar') and student.avatar else None

        return Response({
            "name": student.name,
            "level": stats.level,
            "total_xp": stats.total_xp,
            "day_streak": stats.day_streak,
            "avatar_thumbnail_url": avatar_url,
            "grade": student.grade,
            "board": student.board
        })


class StudentOurJourneyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId):
        student = Student.objects.get(id=studentId)

        subjects_prog = []
        for s in Subject.objects.filter(is_active=True):
            topics = Topic.objects.filter(subject=s)
            if topics.exists():
                comp = StudentTopicProgress.objects.filter(student=student, topic__in=topics, status='completed').count()
                pct = int((comp / topics.count()) * 100)
            else:
                pct = 0
            subjects_prog.append({
                "subject": s.name,
                "progress_percent": pct
            })

        total_m = JourneyMilestone.objects.count()
        comp_m = StudentJourneyProgress.objects.filter(student=student, status='completed').count()

        return Response({
            "subjects_progress": subjects_prog,
            "milestones_completed": comp_m,
            "total_milestones": total_m
        })


class StudentCardsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId):
        student = Student.objects.get(id=studentId)
        cards = StudentCard.objects.filter(student=student).order_by('-earned_at')
        return Response({"cards": StudentCardSerializer(cards, many=True).data})
