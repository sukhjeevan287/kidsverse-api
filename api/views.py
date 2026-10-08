import datetime
import secrets
from django.db.models import Count, Sum, Q
from api.utils import hash_password, verify_password
from api.jwt_utils import generate_jwt_token
from django.utils import timezone
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.utils.text import slugify

from api.models import (
    Parent, Student, Interest, StudentInterest, Goal, StudentGoal,
    OnboardingStep, PasswordResetRequest, ParentVerificationChallenge, Curriculum, Theme, Subject, SubjectGradeAvailability, StudentSubjectUnlock,
    Topic, TopicJourneyMeta, StudentTopicProgress, CompanionActivity,
    StudentCompanionActivityLog, TopicTier, Mission, MissionProgress,
    Test, TestQuestion, TestAttempt, TestAttemptAnswer, ExtraLearningRecommendation,
    Challenge, ChallengeQuestion, ChallengeOpponent, ChallengeBattle, JourneyMilestone,
    StudentJourneyProgress, StudentCard, NovaInteraction, AvatarCharacter,
    AvatarCategory, AvatarItem, StudentAvatar, StudentAvatarUnlock, StudentStat,
    MissionRecommendation, StudentSettings, StudentBreakPass, Concept, ConceptPackage, LearningContent, LearnBeforeTestStep,
    CheckForUnderstandingQuestion, ConceptTestQuestion, BattleQuestion, ConceptQuestion, LearningEvent
)
from api.serializers import (
    ParentSerializer, ParentSignupSerializer, ParentLoginSerializer,
    StudentSerializer, GradeBoardSerializer, InterestSerializer, GoalSerializer,
    AvatarCharacterSerializer, AvatarItemSerializer, SaveAvatarSerializer,
    SetInterestsSerializer, SetGoalsSerializer, SubjectSerializer, TopicSerializer,
    MissionSerializer, TestSerializer, TestQuestionSerializer, ChallengeSerializer,
    ChallengeOpponentSerializer, StudentCardSerializer, CurriculumSerializer,
    ThemeSerializer, LearningContentSerializer, LearnBeforeTestStepSerializer,
    CheckForUnderstandingQuestionSerializer, ConceptTestQuestionSerializer,
    BattleQuestionSerializer, ChallengeQuestionSerializer,
    ConceptSerializer, ConceptPackageListSerializer, ConceptQuestionSerializer
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


def get_student_curriculum(student):
    if student.curriculum_id:
        return student.curriculum
    if not (student.board and student.grade):
        return None
    curr = Curriculum.objects.filter(
        board__iexact=student.board,
        grade__iexact=student.grade,
        is_active=True,
    ).first()
    if not curr:
        alt_grade = f"Grade {student.grade}" if not student.grade.lower().startswith("grade") else student.grade.replace("Grade", "").replace("grade", "").strip()
        curr = Curriculum.objects.filter(
            board__iexact=student.board,
            grade__iexact=alt_grade,
            is_active=True,
        ).first()
    return curr


def get_student_topics(student):
    curriculum = get_student_curriculum(student)
    if not curriculum:
        return Topic.objects.none()
    alt_grade = f"Grade {curriculum.grade}" if not curriculum.grade.lower().startswith("grade") else curriculum.grade.replace("Grade", "").replace("grade", "").strip()
    return Topic.objects.filter(
        Q(curriculum=curriculum) |
        Q(curriculum__board__iexact=curriculum.board, curriculum__grade__in=[curriculum.grade, alt_grade])
    ).distinct()


def serialize_topic_progress(student, topic):
    progress = StudentTopicProgress.objects.filter(student=student, topic=topic).first()
    return {
        'id': str(topic.id),
        'name': topic.name,
        'slug': topic.slug,
        'subject': topic.subject.name,
        'status': progress.status if progress else 'locked',
        'order_index': topic.order_index,
    }


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
            pin_hash=hash_password(serializer.validated_data['parent_pin']) if serializer.validated_data.get('parent_pin') else None,
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


class ParentForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({'email': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        parent = Parent.objects.filter(email__iexact=email).first()
        if parent:
            PasswordResetRequest.objects.create(
                parent=parent,
                expires_at=timezone.now() + datetime.timedelta(hours=1),
            )

        return Response({
            'message': 'If this email is registered, password reset instructions will be sent.',
            'delivery': 'not_configured',
        })


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
            student_topics = get_student_topics(s)
            for subj in Subject.objects.filter(topics__in=student_topics, is_active=True).distinct():
                topics = student_topics.filter(subject=subj)
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


class ParentVerificationStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        required_fields = ('full_name', 'relationship', 'phone', 'student_id')
        missing = [field for field in required_fields if not request.data.get(field)]
        if missing:
            return Response({'error': f"Missing required fields: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)

        student = Student.objects.filter(id=request.data['student_id'], parent=request.parent).first()
        if not student:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        code = f'{secrets.randbelow(1000000):06d}'
        challenge = ParentVerificationChallenge.objects.create(
            parent=request.parent,
            student=student,
            full_name=request.data['full_name'].strip(),
            relationship=request.data['relationship'].strip(),
            phone=request.data['phone'].strip(),
            code_hash=hash_password(code),
            expires_at=timezone.now() + datetime.timedelta(minutes=10),
        )
        response = {
            'challenge_id': str(challenge.id),
            'expires_at': challenge.expires_at.isoformat(),
            'delivery': 'development',
        }
        if settings.DEBUG:
            response['development_code'] = code
        return Response(response, status=status.HTTP_201_CREATED)


class ParentVerificationVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        challenge_id = request.data.get('challenge_id')
        code = request.data.get('code')
        if not (challenge_id and code):
            return Response({'error': 'challenge_id and code are required.'}, status=status.HTTP_400_BAD_REQUEST)

        challenge = ParentVerificationChallenge.objects.filter(id=challenge_id, parent=request.parent).first()
        if not challenge:
            return Response({'error': 'Verification challenge not found'}, status=status.HTTP_404_NOT_FOUND)
        if challenge.verified_at:
            return Response({'error': 'Verification challenge has already been used.'}, status=status.HTTP_400_BAD_REQUEST)
        if challenge.expires_at < timezone.now() or not verify_password(str(code), challenge.code_hash):
            return Response({'error': 'Invalid or expired verification code.'}, status=status.HTTP_400_BAD_REQUEST)

        challenge.verified_at = timezone.now()
        challenge.save(update_fields=['verified_at'])
        request.parent.full_name = challenge.full_name
        request.parent.phone = challenge.phone
        request.parent.save(update_fields=['full_name', 'phone'])
        return Response({'verified': True, 'student_id': str(challenge.student_id)})


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
        alt_grade = f"Grade {student.grade}" if not student.grade.lower().startswith("grade") else student.grade.replace("Grade", "").replace("grade", "").strip()
        curriculum = Curriculum.objects.filter(
            board__iexact=student.board,
            grade__in=[student.grade, alt_grade],
            is_active=True
        ).first()
        if not curriculum:
            curriculum = Curriculum.objects.create(
                board=student.board,
                grade=student.grade,
                name=f'{student.board} - {student.grade}',
                code=f'{slugify(student.board)}-{slugify(student.grade)}',
                is_active=True
            )
        student.curriculum = curriculum
        student.save(update_fields=['grade', 'board', 'curriculum', 'updated_at'])

        OnboardingStep.objects.get_or_create(student=student, step_key='grade_board')
        return Response(StudentSerializer(student).data)


class StudentLearningPathView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId):
        student = Student.objects.get(id=studentId)
        curriculum = get_student_curriculum(student)
        topics = get_student_topics(student).select_related('subject').order_by('subject__order_index', 'order_index')
        subjects = []
        for subject in Subject.objects.filter(topics__in=topics, is_active=True).distinct().order_by('order_index'):
            subject_topics = [serialize_topic_progress(student, topic) for topic in topics.filter(subject=subject)]
            subjects.append({'id': str(subject.id), 'name': subject.name, 'slug': subject.slug, 'topics': subject_topics})

        return Response({
            'student_id': str(student.id),
            'curriculum': {
                'id': str(curriculum.id), 'name': curriculum.name,
                'board': curriculum.board, 'grade': curriculum.grade,
            } if curriculum else None,
            'subjects': subjects,
        })


class StudentSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId):
        student = Student.objects.get(id=studentId)
        student_settings, _ = StudentSettings.objects.get_or_create(student=student)
        return Response({'settings': student_settings.values, 'updated_at': student_settings.updated_at.isoformat()})

    def patch(self, request, studentId):
        student = Student.objects.get(id=studentId)
        values = request.data.get('settings')
        if not isinstance(values, dict):
            return Response({'settings': ['A JSON object is required.']}, status=status.HTTP_400_BAD_REQUEST)
        student_settings, _ = StudentSettings.objects.get_or_create(student=student)
        student_settings.values = values
        student_settings.save(update_fields=['values', 'updated_at'])
        return Response({'settings': student_settings.values, 'updated_at': student_settings.updated_at.isoformat()})


class StudentNovaMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId):
        student = Student.objects.get(id=studentId)
        messages = NovaInteraction.objects.filter(student=student).order_by('created_at')
        return Response({'messages': [{
            'id': str(message.id), 'message': message.message, 'response': message.response,
            'context': message.context, 'created_at': message.created_at.isoformat(),
        } for message in messages]})

    def post(self, request, studentId):
        student = Student.objects.get(id=studentId)
        message = (request.data.get('message') or '').strip()
        topic_id = request.data.get('topic_id')
        if not message:
            return Response({'error': 'message is required.'}, status=status.HTTP_400_BAD_REQUEST)
        topic = None
        if topic_id:
            topic = get_student_topics(student).filter(id=topic_id).first()
            if not topic:
                return Response({'error': 'Topic is not available in this student curriculum.'}, status=status.HTTP_404_NOT_FOUND)

        if topic:
            response_text = f"Let's explore {topic.name} together! {message}"
            context = {'topic_id': str(topic.id)}
        else:
            response_text = f"Hi! I'm Nova, your learning buddy. How can I help you? You said: {message}"
            context = {}

        interaction = NovaInteraction.objects.create(
            student=student, message=message, response=response_text, context=context,
        )
        return Response({
            'id': str(interaction.id), 'message': interaction.message, 'response': interaction.response,
            'context': interaction.context, 'created_at': interaction.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


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
            first_mission = Mission.objects.filter(topic__in=get_student_topics(student)).order_by('topic__order_index', 'order_index').first()
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

        subjects = Subject.objects.filter(topics__in=get_student_topics(student), is_active=True).distinct().order_by('order_index')
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
        subjects = Subject.objects.filter(topics__in=get_student_topics(student), is_active=True).distinct().order_by('order_index')
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
        topic = get_student_topics(student).filter(id=topicId).first()
        if not topic:
            return Response({'error': 'Topic is not available in this student curriculum.'}, status=status.HTTP_404_NOT_FOUND)

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
        mission = Mission.objects.filter(id=missionId).first()
        if not mission:
            return Response({'error': 'Mission not found'}, status=status.HTTP_404_NOT_FOUND)
        content = dict(mission.content or {"type": "interactive_lesson", "steps": []})
        package_id = None
        if isinstance(content, dict) and 'package_id' in content:
            package_id = content['package_id']
        elif mission.concept and mission.concept.packages.exists():
            pkg = mission.concept.packages.first()
            package_id = str(pkg.id)
            content['package_id'] = package_id
        return Response({
            "id": str(mission.id),
            "topic_id": str(mission.topic.id),
            "tier_key": mission.tier.tier_key,
            "name": mission.name,
            "xp_reward": mission.xp_reward,
            "package_id": package_id,
            "content": content
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


class StudentMissionReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId, missionId):
        student = Student.objects.get(id=studentId)
        mission = Mission.objects.get(id=missionId)
        if not get_student_topics(student).filter(id=mission.topic_id).exists():
            return Response({'error': 'Mission is not available in this student curriculum.'}, status=status.HTTP_404_NOT_FOUND)
        progress = MissionProgress.objects.filter(student=student, mission=mission).first()
        events = LearningEvent.objects.filter(student=student, mission=mission).order_by('created_at')
        check_questions = []
        if isinstance(mission.content, dict) and mission.content.get('check_for_understanding'):
            check_questions = mission.content.get('check_for_understanding')
        elif mission.concept and mission.concept.packages.exists():
            pkg = mission.concept.packages.first()
            check_questions = CheckForUnderstandingQuestionSerializer(pkg.cfu_questions.all().order_by('order_index'), many=True).data

        return Response({
            'mission': {'id': str(mission.id), 'name': mission.name, 'topic': mission.topic.name},
            'progress': {
                'status': progress.status if progress else 'locked',
                'score': float(progress.score) if progress and progress.score is not None else None,
                'stars': progress.stars if progress else 0,
                'completed_at': progress.completed_at.isoformat() if progress and progress.completed_at else None,
            },
            'events': [{
                'event_type': event.event_type, 'is_correct': event.is_correct,
                'hint_count': event.hint_count, 'created_at': event.created_at.isoformat(),
            } for event in events],
            'check_questions': check_questions,
        })


class LearningPackageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, packageId):
        package = ConceptPackage.objects.select_related('concept__topic__subject', 'theme', 'learning_content').filter(
            id=packageId, is_published=True,
        ).first()
        if not package:
            concept = Concept.objects.filter(id=packageId).first()
            if concept and concept.packages.exists():
                package = concept.packages.select_related('concept__topic__subject', 'theme', 'learning_content').first()
            else:
                mission = Mission.objects.filter(id=packageId).first()
                if mission and mission.concept and mission.concept.packages.exists():
                    package = mission.concept.packages.select_related('concept__topic__subject', 'theme', 'learning_content').first()
        if not package:
            return Response({'error': 'Learning package not found'}, status=status.HTTP_404_NOT_FOUND)

        learning_content = getattr(package, 'learning_content', None)
        return Response({
            'id': str(package.id),
            'concept': {'id': str(package.concept_id), 'name': package.concept.name, 'topic': package.concept.topic.name},
            'theme': package.theme.name,
            'content_type': package.content_type,
            'learning_content': LearningContentSerializer(learning_content).data if learning_content else {
                'teaching_method': package.teaching_method, 'explanation': package.explanation,
                'image_url': package.image_url, 'image_prompt': package.image_prompt, 'hints': package.hints,
                'nova_script': package.nova_script, 'nova_feedback': package.nova_feedback,
                'learn_before_test': package.learn_before_test,
            },
            'learn_before_test': {
                'steps': LearnBeforeTestStepSerializer(package.learn_steps.all().order_by('order_index'), many=True).data,
            },
            'check_for_understanding': CheckForUnderstandingQuestionSerializer(
                package.cfu_questions.all().order_by('order_index'), many=True,
            ).data,
        })


# --- JOURNEY ---

class StudentJourneyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId):
        student = Student.objects.get(id=studentId)
        subject_slug = request.query_params.get('subject', 'literacy')
        
        subject = Subject.objects.filter(slug__iexact=subject_slug, topics__in=get_student_topics(student)).distinct().first()
        if not subject:
            subject = Subject.objects.filter(topics__in=get_student_topics(student)).distinct().first()

        worlds = []
        if subject:
            topics = get_student_topics(student).filter(subject=subject).order_by('order_index')
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
            "xp_awarded": int(float(attempt.score or 0) * 0.5),
            "extra_learning": recs_list
        })


class TestAttemptReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attemptId):
        attempt = TestAttempt.objects.select_related('test__topic').filter(id=attemptId).first()
        if not attempt:
            return Response({'error': 'Test attempt not found'}, status=status.HTTP_404_NOT_FOUND)
        if attempt.student.parent_id != request.parent.id:
            return Response({'error': 'Test attempt does not belong to this parent.'}, status=status.HTTP_403_FORBIDDEN)

        answers = TestAttemptAnswer.objects.filter(attempt=attempt).select_related('question').order_by('question__order_index')
        return Response({
            'attempt_id': str(attempt.id), 'test': attempt.test.name,
            'topic': attempt.test.topic.name, 'score': float(attempt.score) if attempt.score is not None else None,
            'answers': [{
                'question_id': str(answer.question_id), 'question': answer.question.question_text,
                'options': answer.question.options, 'selected_answer': answer.selected_answer,
                'correct_answer': answer.question.correct_answer, 'is_correct': answer.is_correct,
            } for answer in answers],
        })


class StudentExtraLearningView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId):
        student = Student.objects.get(id=studentId)
        recommendations = ExtraLearningRecommendation.objects.filter(
            attempt__student=student,
        ).select_related('mission__topic', 'attempt').order_by('-created_at')
        return Response({'recommendations': [{
            'id': str(recommendation.id), 'mission_id': str(recommendation.mission_id),
            'mission': recommendation.mission.name, 'topic': recommendation.mission.topic.name,
            'reason': recommendation.reason, 'attempt_id': str(recommendation.attempt_id),
            'created_at': recommendation.created_at.isoformat(),
        } for recommendation in recommendations]})


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


class ChallengeLeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, challengeId):
        challenge = Challenge.objects.filter(id=challengeId).first()
        if not challenge:
            return Response({'error': 'Challenge not found'}, status=status.HTTP_404_NOT_FOUND)
        scope = request.query_params.get('scope')
        if scope not in {'friends', 'India', 'global'}:
            return Response({'scope': ['Use friends, India, or global.']}, status=status.HTTP_400_BAD_REQUEST)
        try:
            limit = min(max(int(request.query_params.get('limit', 25)), 1), 100)
        except ValueError:
            return Response({'limit': ['Use a whole number.']}, status=status.HTTP_400_BAD_REQUEST)

        rows = ChallengeBattle.objects.filter(challenge=challenge, status='completed').values(
            'student_id', 'student__name', 'student__avatar__character__base_image_url',
        ).annotate(
            xp=Sum('score'), battles_played=Count('id'),
        ).order_by('-xp', '-battles_played')
        student_id = request.query_params.get('student_id')
        entries = []
        current_student = None
        for rank, row in enumerate(rows, 1):
            entry = {
                'rank': rank, 'student_id': str(row['student_id']), 'display_name': row['student__name'],
                'avatar_url': row['student__avatar__character__base_image_url'],
                'xp': float(row['xp'] or 0), 'battles_played': row['battles_played'],
            }
            if student_id and str(row['student_id']) == student_id:
                current_student = entry
            if len(entries) < limit:
                entries.append(entry)
        return Response({
            'scope': scope, 'updated_at': timezone.now().isoformat(), 'total_players': len(rows),
            'current_student': current_student, 'entries': entries,
        })


# --- PROFILE ---

class StudentBreakPassView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, studentId):
        student = Student.objects.get(id=studentId)
        break_passes, _ = StudentBreakPass.objects.get_or_create(student=student)
        return Response({
            'available_count': break_passes.available_count, 'used_count': break_passes.used_count,
            'updated_at': break_passes.updated_at.isoformat(),
        })

    def post(self, request, studentId):
        student = Student.objects.get(id=studentId)
        break_passes, _ = StudentBreakPass.objects.get_or_create(student=student)
        if break_passes.available_count == 0:
            return Response({'error': 'No break passes are available.'}, status=status.HTTP_409_CONFLICT)
        break_passes.available_count -= 1
        break_passes.used_count += 1
        break_passes.save(update_fields=['available_count', 'used_count', 'updated_at'])
        return Response({
            'used': True, 'available_count': break_passes.available_count,
            'used_count': break_passes.used_count,
        })


class ParentPinVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pin = request.data.get('pin')
        if not pin:
            return Response({'pin': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        if not request.parent.pin_hash:
            return Response({'error': 'Parent PIN has not been configured.'}, status=status.HTTP_409_CONFLICT)
        if not verify_password(str(pin), request.parent.pin_hash):
            return Response({'verified': False}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'verified': True})


class ParentEvidenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student_id = request.query_params.get('student_id')
        topic_id = request.query_params.get('topic_id')
        if not (student_id and topic_id):
            return Response({'error': 'student_id and topic_id are required.'}, status=status.HTTP_400_BAD_REQUEST)
        student = Student.objects.filter(id=student_id, parent=request.parent).first()
        topic = Topic.objects.filter(id=topic_id).first()
        if not student or not topic:
            return Response({'error': 'Student or topic not found.'}, status=status.HTTP_404_NOT_FOUND)

        topic_progress = StudentTopicProgress.objects.filter(student=student, topic=topic).first()
        missions = Mission.objects.filter(topic=topic)
        mission_progress = MissionProgress.objects.filter(student=student, mission__in=missions)
        test_attempts = TestAttempt.objects.filter(student=student, test__topic=topic, status='completed')
        return Response({
            'student_id': str(student.id), 'topic': {'id': str(topic.id), 'name': topic.name},
            'topic_status': topic_progress.status if topic_progress else 'locked',
            'missions_completed': mission_progress.filter(status='completed').count(),
            'missions_total': missions.count(),
            'latest_test_score': float(test_attempts.order_by('-completed_at').first().score) if test_attempts.exists() and test_attempts.order_by('-completed_at').first().score is not None else None,
            'learning_events': LearningEvent.objects.filter(student=student, mission__topic=topic).count(),
        })


class ParentWeeklyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student_id = request.query_params.get('student_id')
        week = request.query_params.get('week')
        if not (student_id and week):
            return Response({'error': 'student_id and week are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            start_date = datetime.date.fromisoformat(week)
        except ValueError:
            return Response({'week': ['Use YYYY-MM-DD.']}, status=status.HTTP_400_BAD_REQUEST)
        student = Student.objects.filter(id=student_id, parent=request.parent).first()
        if not student:
            return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        recommended_missions = MissionRecommendation.objects.filter(student=student, is_active=True).select_related('mission__topic')
        if not recommended_missions.exists():
            recommended_missions = Mission.objects.filter(topic__in=get_student_topics(student)).select_related('topic').order_by('topic__order_index', 'order_index')[:7]
            items = [{'mission': mission, 'reason': 'Continue the curriculum learning path'} for mission in recommended_missions]
        else:
            items = [{'mission': recommendation.mission, 'reason': recommendation.reason_text or 'Recommended for this week'} for recommendation in recommended_missions[:7]]
        return Response({
            'student_id': str(student.id), 'week_start': start_date.isoformat(),
            'days': [{
                'date': (start_date + datetime.timedelta(days=index)).isoformat(),
                'mission_id': str(items[index]['mission'].id) if index < len(items) else None,
                'mission': items[index]['mission'].name if index < len(items) else None,
                'topic': items[index]['mission'].topic.name if index < len(items) else None,
                'reason': items[index]['reason'] if index < len(items) else None,
            } for index in range(7)],
        })

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
        student_topics = get_student_topics(student)
        for s in Subject.objects.filter(topics__in=student_topics, is_active=True).distinct():
            topics = student_topics.filter(subject=s)
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


# --- CURRICULUM & CONTENT STUDIO INGESTION ---

# --- CURRICULUM & CONTENT STUDIO INGESTION ---

class AdminContentFeedView(APIView):
    """
    Ingests full curriculum content packages produced by Kidsverse Content Studio.
    Segregates content cleanly into dedicated relational tables:
    - Curriculum (board, grade)
    - Subject (linked to Curriculum)
    - Topic (linked to Subject and Curriculum)
    - Concept (linked to Topic)
    - Theme (name, slug)
    - ConceptPackage (binds Concept and Theme)
    - LearningContent (teaching method, image, hints, scripts)
    - CheckForUnderstandingQuestion (CFU questions)
    - ConceptTestQuestion (Test questions)
    - BattleQuestion (Battle questions)
    - Challenge & ChallengeQuestion (Challenge questions)
    Also synchronizes playable Missions, Tests, and Challenges.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.data
        if not isinstance(payload, dict):
            return Response({"error": "Invalid payload format. Expected a JSON object."}, status=status.HTTP_400_BAD_REQUEST)

        curriculum = payload.get('curriculum', {})
        concept_data = payload.get('concept', {})

        grade = curriculum.get('grade')
        board = curriculum.get('board', 'CBSE')
        subject_name = curriculum.get('subject')
        topic_name = curriculum.get('topic')
        concept_name = concept_data.get('name')

        if not (grade and subject_name and topic_name and concept_name):
            return Response({
                "error": "Missing required curriculum fields. 'grade', 'subject', 'topic', and 'concept.name' are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 1. Curriculum
        curriculum_code = f"{slugify(board)}-{slugify(grade)}"
        curriculum_obj, _ = Curriculum.objects.get_or_create(
            board=board,
            grade=grade,
            defaults={
                'name': f"{board} - {grade}",
                'code': curriculum_code,
                'is_active': True
            }
        )

        # 2. Subject
        subject_slug = slugify(subject_name)
        subject, _ = Subject.objects.get_or_create(
            slug=subject_slug,
            defaults={'name': subject_name, 'curriculum': curriculum_obj, 'is_active': True}
        )
        if not subject.curriculum:
            subject.curriculum = curriculum_obj
            subject.save(update_fields=['curriculum'])
        subject.curricula.add(curriculum_obj)

        SubjectGradeAvailability.objects.get_or_create(
            subject=subject,
            grade=grade,
            defaults={'is_unlocked_default': True}
        )

        # 3. Topic
        topic_slug = slugify(topic_name)
        topic, _ = Topic.objects.get_or_create(
            subject=subject,
            board=board,
            grade_level=grade,
            slug=topic_slug,
            defaults={'name': topic_name, 'curriculum': curriculum_obj}
        )
        if not topic.curriculum:
            topic.curriculum = curriculum_obj
            topic.save(update_fields=['curriculum'])

        # 4. Concept
        concept_slug = slugify(concept_name)
        learning_objective = concept_data.get('learning_objective', '')
        concept, _ = Concept.objects.update_or_create(
            topic=topic,
            slug=concept_slug,
            defaults={
                'name': concept_name,
                'learning_objective': learning_objective
            }
        )

        # 5. Theme
        theme_name = payload.get('theme_interest', 'Everyday Life')
        theme_slug = slugify(theme_name)
        theme_obj, _ = Theme.objects.get_or_create(
            slug=theme_slug,
            defaults={'name': theme_name, 'is_active': True}
        )

        # 6. Concept Package
        content_type = payload.get('content_type', 'concept_package')
        learning_content = payload.get('learning_content', {})
        cfu_data = payload.get('check_for_understanding', [])

        # Parse and normalize learn_before_test (Learn Before Test · 3 Steps: Understand -> Example -> Remember)
        learn_before_test_data = payload.get('learn_before_test') or payload.get('learn_before_steps', {})
        if isinstance(learn_before_test_data, list):
            steps_list = learn_before_test_data
            learn_before_test_obj = {
                "required": True,
                "order": [s.get('step_key') or s.get('stepKey') or (
                    'understand' if i == 0 else ('example' if i == 1 else 'remember')
                ) for i, s in enumerate(steps_list)],
                "starts_quiz_after": steps_list[-1].get('step_key', 'remember') if steps_list else 'remember',
                "steps": steps_list
            }
        elif isinstance(learn_before_test_data, dict):
            steps_list = learn_before_test_data.get('steps', [])
            learn_before_test_obj = learn_before_test_data
        else:
            steps_list = []
            learn_before_test_obj = {}

        package, _ = ConceptPackage.objects.update_or_create(
            concept=concept,
            theme=theme_obj,
            defaults={
                'content_type': content_type,
                'teaching_method': learning_content.get('teaching_method', ''),
                'explanation': learning_content.get('explanation', ''),
                'image_url': learning_content.get('image_url', ''),
                'image_prompt': learning_content.get('image_prompt', ''),
                'hints': learning_content.get('hints', []),
                'nova_script': learning_content.get('nova_script', ''),
                'nova_feedback': learning_content.get('nova_feedback', ''),
                'learn_before_test': learn_before_test_obj,
                'check_for_understanding': cfu_data,
                'raw_payload': payload,
                'is_published': True,
            }
        )

        # 7. Segregated LearningContent Table
        learning_obj, _ = LearningContent.objects.update_or_create(
            package=package,
            defaults={
                'concept': concept,
                'theme': theme_obj,
                'teaching_method': learning_content.get('teaching_method', ''),
                'explanation': learning_content.get('explanation', ''),
                'image_url': learning_content.get('image_url', ''),
                'image_prompt': learning_content.get('image_prompt', ''),
                'hints': learning_content.get('hints', []),
                'nova_script': learning_content.get('nova_script', ''),
                'nova_feedback': learning_content.get('nova_feedback', ''),
                'learn_before_test': learn_before_test_obj,
            }
        )

        # 8. Segregated LearnBeforeTestStep Table (Learn Before Test · 3 Steps)
        package.learn_steps.all().delete()
        for idx, s in enumerate(steps_list, 1):
            default_key = 'understand' if idx == 1 else ('example' if idx == 2 else 'remember')
            step_key = s.get('step_key') or s.get('stepKey') or default_key
            title = s.get('title', '')
            teaching_text = s.get('teaching_text') or s.get('teachingText', '')
            key_idea = s.get('key_idea') or s.get('keyIdea', '')
            image_url = s.get('image_url') or s.get('imageUrl', '')
            image_prompt = s.get('image_prompt') or s.get('imagePrompt', '')
            nova_script = s.get('nova_script') or s.get('novaScript', '')

            mini_q = s.get('mini_question') or s.get('miniQuestion') or {}
            if not isinstance(mini_q, dict):
                mini_q = {}
            mini_question = {
                'question': mini_q.get('question', ''),
                'options': mini_q.get('options', []),
                'answer': mini_q.get('answer', ''),
                'explanation': mini_q.get('explanation', '')
            }

            LearnBeforeTestStep.objects.create(
                package=package,
                learning_content=learning_obj,
                concept=concept,
                step_key=step_key,
                title=title,
                teaching_text=teaching_text,
                key_idea=key_idea,
                image_url=image_url,
                image_prompt=image_prompt,
                nova_script=nova_script,
                mini_question=mini_question,
                order_index=idx
            )

        # 9. Segregated CheckForUnderstandingQuestion Table
        package.cfu_questions.all().delete()
        for idx, q in enumerate(cfu_data, 1):
            CheckForUnderstandingQuestion.objects.create(
                package=package,
                learning_content=learning_obj,
                question_text=q.get('question', ''),
                options=q.get('options', []),
                correct_answer=q.get('answer', ''),
                difficulty=q.get('difficulty', 'Easy'),
                explanation=q.get('explanation', ''),
                order_index=idx
            )

        # 9. Segregated ConceptTestQuestion Table
        test_questions_data = payload.get('test_questions', {})
        test_is_one_time = False
        if isinstance(test_questions_data, dict):
            test_is_one_time = test_questions_data.get('one_time', False)
            test_q_list = test_questions_data.get('questions', [])
        else:
            test_q_list = test_questions_data or []

        package.test_questions.all().delete()
        for idx, q in enumerate(test_q_list, 1):
            marks = q.get('marks')
            try:
                marks = int(marks) if marks is not None else 1
            except (ValueError, TypeError):
                marks = 1
            ConceptTestQuestion.objects.create(
                package=package,
                concept=concept,
                topic=topic,
                question_text=q.get('question', ''),
                options=q.get('options', []),
                correct_answer=q.get('answer', ''),
                difficulty=q.get('difficulty', 'Medium'),
                marks=marks,
                explanation=q.get('explanation', ''),
                is_one_time=test_is_one_time,
                order_index=idx
            )

        # Synchronize with Test & TestQuestion for student testing flow
        topic_test, _ = Test.objects.get_or_create(
            topic=topic,
            slug=f"{concept.slug}-test",
            defaults={
                'name': f"{concept.name} Test",
                'intro_text': f"Practice test for {concept.name}"
            }
        )
        for idx, q in enumerate(test_q_list, 1):
            marks = q.get('marks', 1)
            try:
                marks = int(marks) if marks is not None else 1
            except (ValueError, TypeError):
                marks = 1
            TestQuestion.objects.update_or_create(
                test=topic_test,
                order_index=idx,
                defaults={
                    'question_text': q.get('question', ''),
                    'question_type': 'mcq',
                    'options': q.get('options', []),
                    'correct_answer': q.get('answer', ''),
                    'points': marks
                }
            )

        # 10. Segregated BattleQuestion Table
        battle_q_list = payload.get('battle_questions', [])
        package.battle_questions.all().delete()
        for idx, q in enumerate(battle_q_list, 1):
            xp = q.get('xp')
            try:
                xp = int(xp) if xp is not None else 20
            except (ValueError, TypeError):
                xp = 20
            BattleQuestion.objects.create(
                package=package,
                concept=concept,
                topic=topic,
                question_text=q.get('question', ''),
                options=q.get('options', []),
                correct_answer=q.get('answer', ''),
                difficulty=q.get('difficulty', 'Hard'),
                xp=xp,
                explanation=q.get('explanation', ''),
                order_index=idx
            )

        # 11. Segregated Challenge & ChallengeQuestion Table
        challenge_data = payload.get('challenge', {})
        challenge_is_one_time = False
        if isinstance(challenge_data, dict):
            challenge_is_one_time = challenge_data.get('one_time', False)
            challenge_q_list = challenge_data.get('questions', [])
        else:
            challenge_q_list = challenge_data or []

        challenge_slug = f"{topic.slug}-{concept.slug}-challenge"
        challenge_obj, _ = Challenge.objects.update_or_create(
            slug=challenge_slug,
            defaults={
                'topic': topic,
                'package': package,
                'concept': concept,
                'name': f"{concept.name} Challenge",
                'description': f"Boss challenge battle for {concept.name}",
                'is_one_time': challenge_is_one_time
            }
        )

        package.challenge_questions.all().delete()
        for idx, q in enumerate(challenge_q_list, 1):
            xp = q.get('xp')
            try:
                xp = int(xp) if xp is not None else 35
            except (ValueError, TypeError):
                xp = 35
            ChallengeQuestion.objects.create(
                challenge=challenge_obj,
                package=package,
                concept=concept,
                question_text=q.get('question', ''),
                options=q.get('options', []),
                correct_answer=q.get('answer', ''),
                difficulty=q.get('difficulty', 'Hard'),
                xp=xp,
                explanation=q.get('explanation', ''),
                nova_feedback=q.get('nova_feedback', ''),
                order_index=idx
            )

        # 12. Populate legacy ConceptQuestion for backward compatibility
        package.questions.all().delete()
        for idx, q in enumerate(cfu_data, 1):
            ConceptQuestion.objects.create(
                package=package,
                question_type='cfu',
                question_text=q.get('question', ''),
                options=q.get('options', []),
                correct_answer=q.get('answer', ''),
                difficulty=q.get('difficulty', 'Easy'),
                explanation=q.get('explanation', ''),
                order_index=idx
            )
        for idx, q in enumerate(test_q_list, 1):
            marks = q.get('marks')
            try:
                marks = int(marks) if marks is not None else 1
            except (ValueError, TypeError):
                marks = 1
            ConceptQuestion.objects.create(
                package=package,
                question_type='test',
                question_text=q.get('question', ''),
                options=q.get('options', []),
                correct_answer=q.get('answer', ''),
                difficulty=q.get('difficulty', 'Medium'),
                marks_or_xp=marks,
                explanation=q.get('explanation', ''),
                order_index=idx
            )
        for idx, q in enumerate(battle_q_list, 1):
            xp = q.get('xp')
            try:
                xp = int(xp) if xp is not None else 20
            except (ValueError, TypeError):
                xp = 20
            ConceptQuestion.objects.create(
                package=package,
                question_type='battle',
                question_text=q.get('question', ''),
                options=q.get('options', []),
                correct_answer=q.get('answer', ''),
                difficulty=q.get('difficulty', 'Hard'),
                marks_or_xp=xp,
                explanation=q.get('explanation', ''),
                order_index=idx
            )
        for idx, q in enumerate(challenge_q_list, 1):
            xp = q.get('xp')
            try:
                xp = int(xp) if xp is not None else 35
            except (ValueError, TypeError):
                xp = 35
            ConceptQuestion.objects.create(
                package=package,
                question_type='challenge',
                question_text=q.get('question', ''),
                options=q.get('options', []),
                correct_answer=q.get('answer', ''),
                difficulty=q.get('difficulty', 'Hard'),
                marks_or_xp=xp,
                explanation=q.get('explanation', ''),
                nova_feedback=q.get('nova_feedback', ''),
                order_index=idx
            )

        # 13. Synchronize Mission so student learning path immediately reflects this concept
        tier, _ = TopicTier.objects.get_or_create(
            topic=topic,
            tier_key='school_syllabus',
            defaults={'label': 'School Syllabus', 'order_index': 1, 'required_plan': 'free'}
        )
        mission, _ = Mission.objects.update_or_create(
            topic=topic,
            slug=concept_slug,
            defaults={
                'tier': tier,
                'concept': concept,
                'name': concept.name,
                'xp_reward': 30,
                'content': {
                    'type': 'concept_package',
                    'theme': theme_obj.name,
                    'teaching_method': package.teaching_method,
                    'explanation': package.explanation,
                    'image_url': package.image_url,
                    'hints': package.hints,
                    'nova_script': package.nova_script,
                    'learn_before_test': learn_before_test_obj if steps_list else package.learn_before_test,
                    'check_for_understanding': package.check_for_understanding,
                }
            }
        )

        total_questions = len(cfu_data) + len(test_q_list) + len(battle_q_list) + len(challenge_q_list)

        return Response({
            "status": "success",
            "message": "Content package successfully ingested and segregated into relational tables",
            "data": {
                "curriculum_id": str(curriculum_obj.id),
                "curriculum": curriculum_obj.name,
                "subject_id": str(subject.id),
                "subject": subject.name,
                "board": topic.board,
                "grade": topic.grade_level,
                "topic_id": str(topic.id),
                "topic": topic.name,
                "concept_id": str(concept.id),
                "concept": concept.name,
                "theme_id": str(theme_obj.id),
                "theme": theme_obj.name,
                "package_id": str(package.id),
                "learning_content_id": str(learning_obj.id),
                "mission_id": str(mission.id),
                "test_id": str(topic_test.id),
                "challenge_id": str(challenge_obj.id),
                "learn_before_test_steps_saved": len(steps_list),
                "questions_saved": {
                    "cfu": len(cfu_data),
                    "test": len(test_q_list),
                    "battle": len(battle_q_list),
                    "challenge": len(challenge_q_list),
                    "total": total_questions
                }
            }
        }, status=status.HTTP_201_CREATED)


class AdminContentPackageListView(APIView):
    """
    List all ingested concept packages with filtering options.
    Filter params: ?grade=...&board=...&subject=...&topic=...&theme=...&curriculum_id=...
    """
    permission_classes = [AllowAny]

    def get(self, request):
        qs = ConceptPackage.objects.select_related('concept__topic__subject', 'theme').all().order_by('-created_at')

        grade = request.query_params.get('grade')
        board = request.query_params.get('board')
        subject = request.query_params.get('subject')
        topic = request.query_params.get('topic')
        theme = request.query_params.get('theme')
        curriculum_id = request.query_params.get('curriculum_id')

        if grade:
            qs = qs.filter(concept__topic__grade_level__iexact=grade)
        if board:
            qs = qs.filter(concept__topic__board__iexact=board)
        if subject:
            qs = qs.filter(concept__topic__subject__name__icontains=subject)
        if topic:
            qs = qs.filter(concept__topic__name__icontains=topic)
        if theme:
            qs = qs.filter(theme__name__iexact=theme)
        if curriculum_id:
            qs = qs.filter(concept__topic__curriculum_id=curriculum_id)

        serializer = ConceptPackageListSerializer(qs, many=True)
        return Response({"packages": serializer.data, "count": qs.count()})


class AdminContentPackageDetailView(APIView):
    """
    Retrieves an individual package by querying the segregated tables and
    formatting the result to match the Kidsverse Content Studio schema.
    """
    permission_classes = [AllowAny]

    def get(self, request, packageId):
        package = ConceptPackage.objects.select_related(
            'concept__topic__subject', 'concept__topic__curriculum', 'theme'
        ).filter(id=packageId).first()
        if not package:
            return Response({"error": "Package not found"}, status=status.HTTP_404_NOT_FOUND)

        concept = package.concept
        topic = concept.topic
        subject = topic.subject
        theme = package.theme

        learning_content_obj = getattr(package, 'learning_content', None)

        cfu_questions = [
            {
                "question": q.question_text,
                "options": q.options,
                "answer": q.correct_answer,
                "difficulty": q.difficulty,
                "explanation": q.explanation
            }
            for q in package.cfu_questions.all().order_by('order_index')
        ]
        if not cfu_questions:
            cfu_questions = [
                {
                    "question": q.question_text,
                    "options": q.options,
                    "answer": q.correct_answer,
                    "difficulty": q.difficulty,
                    "explanation": q.explanation
                }
                for q in package.questions.filter(question_type='cfu').order_by('order_index')
            ]

        test_questions = [
            {
                "question": q.question_text,
                "options": q.options,
                "answer": q.correct_answer,
                "difficulty": q.difficulty,
                "marks": q.marks,
                "explanation": q.explanation
            }
            for q in package.test_questions.all().order_by('order_index')
        ]
        if not test_questions:
            test_questions = [
                {
                    "question": q.question_text,
                    "options": q.options,
                    "answer": q.correct_answer,
                    "difficulty": q.difficulty,
                    "marks": q.marks_or_xp,
                    "explanation": q.explanation
                }
                for q in package.questions.filter(question_type='test').order_by('order_index')
            ]

        battle_questions = [
            {
                "question": q.question_text,
                "options": q.options,
                "answer": q.correct_answer,
                "difficulty": q.difficulty,
                "xp": q.xp,
                "explanation": q.explanation
            }
            for q in package.battle_questions.all().order_by('order_index')
        ]
        if not battle_questions:
            battle_questions = [
                {
                    "question": q.question_text,
                    "options": q.options,
                    "answer": q.correct_answer,
                    "difficulty": q.difficulty,
                    "xp": q.marks_or_xp,
                    "explanation": q.explanation
                }
                for q in package.questions.filter(question_type='battle').order_by('order_index')
            ]

        challenge_questions = [
            {
                "question": q.question_text,
                "options": q.options,
                "answer": q.correct_answer,
                "difficulty": q.difficulty,
                "xp": q.xp,
                "explanation": q.explanation,
                "nova_feedback": q.nova_feedback
            }
            for q in package.challenge_questions.all().order_by('order_index')
        ]
        if not challenge_questions:
            challenge_questions = [
                {
                    "question": q.question_text,
                    "options": q.options,
                    "answer": q.correct_answer,
                    "difficulty": q.difficulty,
                    "xp": q.marks_or_xp,
                    "explanation": q.explanation,
                    "nova_feedback": q.nova_feedback
                }
                for q in package.questions.filter(question_type='challenge').order_by('order_index')
            ]

        teaching_method = learning_content_obj.teaching_method if learning_content_obj else package.teaching_method
        image_url = learning_content_obj.image_url if learning_content_obj else package.image_url
        image_prompt = learning_content_obj.image_prompt if learning_content_obj else package.image_prompt
        explanation = learning_content_obj.explanation if learning_content_obj else package.explanation
        hints = learning_content_obj.hints if learning_content_obj else package.hints
        nova_script = learning_content_obj.nova_script if learning_content_obj else package.nova_script
        nova_feedback = learning_content_obj.nova_feedback if learning_content_obj else package.nova_feedback

        # Reconstruct learn_before_test from segregated LearnBeforeTestStep table
        learn_steps_qs = package.learn_steps.all().order_by('order_index')
        if learn_steps_qs.exists():
            steps_data = [
                {
                    "step_key": s.step_key,
                    "title": s.title,
                    "teaching_text": s.teaching_text or '',
                    "key_idea": s.key_idea or '',
                    "image_url": s.image_url or '',
                    "image_prompt": s.image_prompt or '',
                    "nova_script": s.nova_script or '',
                    "mini_question": s.mini_question or {
                        "question": "",
                        "options": [],
                        "answer": "",
                        "explanation": ""
                    }
                }
                for s in learn_steps_qs
            ]
            learn_before_test_data = {
                "required": True,
                "order": [s.step_key for s in learn_steps_qs],
                "starts_quiz_after": learn_steps_qs.last().step_key if learn_steps_qs.last() else 'remember',
                "steps": steps_data
            }
        elif package.learn_before_test:
            learn_before_test_data = package.learn_before_test
        else:
            learn_before_test_data = {
                "required": False,
                "order": ["understand", "example", "remember"],
                "starts_quiz_after": "remember",
                "steps": []
            }

        return Response({
            "id": str(package.id),
            "curriculum": {
                "id": str(topic.curriculum_id) if topic.curriculum_id else None,
                "grade": topic.grade_level,
                "board": topic.board,
                "subject": subject.name,
                "topic": topic.name
            },
            "concept": {
                "id": str(concept.id),
                "name": concept.name,
                "learning_objective": concept.learning_objective
            },
            "theme_interest": theme.name if theme else '',
            "content_type": package.content_type,
            "learning_content": {
                "id": str(learning_content_obj.id) if learning_content_obj else None,
                "teaching_method": teaching_method,
                "image_url": image_url,
                "image_prompt": image_prompt,
                "explanation": explanation,
                "hints": hints,
                "nova_script": nova_script,
                "nova_feedback": nova_feedback
            },
            "learn_before_test": learn_before_test_data,
            "check_for_understanding": cfu_questions,
            "test_questions": {
                "one_time": False,
                "questions": test_questions
            },
            "battle_questions": battle_questions,
            "challenge": {
                "one_time": False,
                "questions": challenge_questions
            },
            "created_at": package.created_at.isoformat(),
            "updated_at": package.updated_at.isoformat()
        })


class CurriculumTreeView(APIView):
    """
    Returns the full curriculum tree (Grade + Board + Subject -> Topics -> Concepts)
    to dynamically populate curriculum dropdowns in the authoring portal.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        grade = request.query_params.get('grade')
        board = request.query_params.get('board')
        subject_query = request.query_params.get('subject')
        curriculum_id = request.query_params.get('curriculum_id')

        topics_qs = Topic.objects.select_related('subject', 'curriculum').prefetch_related('concepts__packages__theme').all()
        if grade:
            topics_qs = topics_qs.filter(grade_level__iexact=grade)
        if board:
            topics_qs = topics_qs.filter(board__iexact=board)
        if subject_query:
            topics_qs = topics_qs.filter(subject__name__icontains=subject_query)
        if curriculum_id:
            topics_qs = topics_qs.filter(curriculum_id=curriculum_id)

        topics_data = []
        for t in topics_qs.order_by('order_index'):
            concepts_data = []
            for c in t.concepts.all().order_by('order_index'):
                themes = list(c.packages.values_list('theme__name', flat=True))
                concepts_data.append({
                    "id": str(c.id),
                    "name": c.name,
                    "slug": c.slug,
                    "objective": c.learning_objective,
                    "available_themes": themes
                })

            topics_data.append({
                "id": str(t.id),
                "curriculum_id": str(t.curriculum_id) if t.curriculum_id else None,
                "name": t.name,
                "slug": t.slug,
                "subject": t.subject.name,
                "grade": t.grade_level,
                "board": t.board,
                "concepts": concepts_data
            })

        return Response({
            "filter": {"grade": grade, "board": board, "subject": subject_query, "curriculum_id": curriculum_id},
            "count": len(topics_data),
            "topics": topics_data
        })


class CurriculumListView(APIView):
    """
    List all Curriculums or create a new Curriculum.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        board = request.query_params.get('board')
        grade = request.query_params.get('grade')
        qs = Curriculum.objects.all().order_by('board', 'grade')
        if board:
            qs = qs.filter(board__iexact=board)
        if grade:
            qs = qs.filter(grade__iexact=grade)

        serializer = CurriculumSerializer(qs, many=True)
        return Response({"curriculums": serializer.data, "count": qs.count()})

    def post(self, request):
        board = request.data.get('board')
        grade = request.data.get('grade')
        name = request.data.get('name') or f"{board} - {grade}"
        description = request.data.get('description', '')

        if not (board and grade):
            return Response({"error": "'board' and 'grade' are required."}, status=status.HTTP_400_BAD_REQUEST)

        code = f"{slugify(board)}-{slugify(grade)}"
        curriculum, created = Curriculum.objects.get_or_create(
            board=board,
            grade=grade,
            defaults={'name': name, 'code': code, 'description': description}
        )
        if not created and description:
            curriculum.description = description
            curriculum.save(update_fields=['description'])

        serializer = CurriculumSerializer(curriculum)
        return Response({
            "status": "success",
            "curriculum": serializer.data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class CurriculumDetailView(APIView):
    """
    Retrieve Curriculum detail including its subjects and topics.
    """
    permission_classes = [AllowAny]

    def get(self, request, curriculumId):
        curriculum = Curriculum.objects.prefetch_related('subjects', 'topics').filter(id=curriculumId).first()
        if not curriculum:
            return Response({"error": "Curriculum not found"}, status=status.HTTP_404_NOT_FOUND)

        subjects_data = [
            {
                "id": str(s.id),
                "name": s.name,
                "slug": s.slug,
                "order_index": s.order_index,
                "is_active": s.is_active
            }
            for s in curriculum.subjects.all()
        ]
        topics_data = [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug,
                "subject": t.subject.name,
                "concepts_count": t.concepts.count()
            }
            for t in curriculum.topics.all()
        ]

        return Response({
            "id": str(curriculum.id),
            "name": curriculum.name,
            "code": curriculum.code,
            "board": curriculum.board,
            "grade": curriculum.grade,
            "description": curriculum.description,
            "is_active": curriculum.is_active,
            "subjects": subjects_data,
            "topics": topics_data
        })


class CurriculumSubjectCreateView(APIView):
    """
    Add a Subject to a Curriculum.
    """
    permission_classes = [AllowAny]

    def post(self, request, curriculumId):
        curriculum = Curriculum.objects.filter(id=curriculumId).first()
        if not curriculum:
            return Response({"error": "Curriculum not found"}, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get('name')
        if not name:
            return Response({"error": "'name' is required."}, status=status.HTTP_400_BAD_REQUEST)

        slug = slugify(name)
        subject, _ = Subject.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'curriculum': curriculum}
        )
        subject.curricula.add(curriculum)
        if not subject.curriculum:
            subject.curriculum = curriculum
            subject.save(update_fields=['curriculum'])

        SubjectGradeAvailability.objects.get_or_create(
            subject=subject,
            grade=curriculum.grade,
            defaults={'is_unlocked_default': True}
        )

        return Response({
            "status": "success",
            "subject": {
                "id": str(subject.id),
                "name": subject.name,
                "slug": subject.slug,
                "curriculum_id": str(curriculum.id)
            }
        }, status=status.HTTP_201_CREATED)


class TopicConceptCreateView(APIView):
    """
    Add a Concept to a Topic.
    """
    permission_classes = [AllowAny]

    def post(self, request, topicId):
        topic = Topic.objects.filter(id=topicId).first()
        if not topic:
            return Response({"error": "Topic not found"}, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get('name')
        learning_objective = request.data.get('learning_objective', '')
        if not name:
            return Response({"error": "'name' is required."}, status=status.HTTP_400_BAD_REQUEST)

        concept, created = Concept.objects.get_or_create(
            topic=topic,
            slug=slugify(name),
            defaults={'name': name, 'learning_objective': learning_objective}
        )

        return Response({
            "status": "success",
            "concept": {
                "id": str(concept.id),
                "name": concept.name,
                "slug": concept.slug,
                "topic_id": str(topic.id),
                "learning_objective": concept.learning_objective
            }
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ThemeListView(APIView):
    """
    List all Themes or create a new Theme.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        themes = Theme.objects.filter(is_active=True).order_by('order_index')
        serializer = ThemeSerializer(themes, many=True)
        return Response({"themes": serializer.data, "count": themes.count()})

    def post(self, request):
        name = request.data.get('name')
        if not name:
            return Response({"error": "'name' is required."}, status=status.HTTP_400_BAD_REQUEST)

        slug = slugify(name)
        theme, created = Theme.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'description': request.data.get('description', ''),
                'icon_asset': request.data.get('icon_asset', '')
            }
        )
        serializer = ThemeSerializer(theme)
        return Response({
            "status": "success",
            "theme": serializer.data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
