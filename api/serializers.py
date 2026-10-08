from rest_framework import serializers
from api.models import (
    Parent, Student, Interest, StudentInterest, Goal, StudentGoal,
    OnboardingStep, Curriculum, Theme, Subject, SubjectGradeAvailability, StudentSubjectUnlock,
    Topic, TopicJourneyMeta, StudentTopicProgress, TopicTier, Mission,
    MissionProgress, Test, TestQuestion, TestAttempt, TestAttemptAnswer,
    ExtraLearningRecommendation, Challenge, ChallengeOpponent, ChallengeBattle,
    JourneyMilestone, StudentJourneyProgress, StudentCard, NovaInteraction,
    AvatarCharacter, AvatarCategory, AvatarItem, StudentAvatar, StudentStat,
    Concept, ConceptPackage, LearningContent, LearnBeforeTestStep, CheckForUnderstandingQuestion,
    ConceptTestQuestion, BattleQuestion, ChallengeQuestion, ConceptQuestion
)

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ['id', 'email', 'full_name', 'phone', 'created_at', 'last_login_at']


class ParentSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    parent_pin = serializers.RegexField(r'^\d{4,8}$', required=False, write_only=True)


class ParentLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class StudentSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'parent_id', 'name', 'grade', 'board', 'avatar', 'onboarding_completed_at', 'created_at']

    def get_avatar(self, obj):
        try:
            student_avatar = StudentAvatar.objects.get(student=obj)
            return {
                "character_id": str(student_avatar.character.id),
                "thumbnail_url": student_avatar.character.base_image_url
            }
        except StudentAvatar.DoesNotExist:
            return None


class GradeBoardSerializer(serializers.Serializer):
    grade = serializers.CharField()
    board = serializers.CharField()


class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'key', 'name', 'thumbnail_url', 'order_index', 'is_active']


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ['id', 'key', 'name', 'tagline', 'icon_asset', 'order_index', 'is_active']


class AvatarCharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvatarCharacter
        fields = ['id', 'name', 'slug', 'base_image_url', 'order_index']


class AvatarItemSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='key', read_only=True)

    class Meta:
        model = AvatarItem
        fields = ['id', 'category', 'name', 'slug', 'description', 'thumbnail_url', 'render_asset_url', 'unlock_type', 'is_default', 'order_index']


class SaveAvatarSerializer(serializers.Serializer):
    character_id = serializers.UUIDField()
    outfit_item_id = serializers.UUIDField(required=False, allow_null=True)
    hair_item_id = serializers.UUIDField(required=False, allow_null=True)
    accessory_item_id = serializers.UUIDField(required=False, allow_null=True)


class SetInterestsSerializer(serializers.Serializer):
    interest_ids = serializers.ListField(child=serializers.UUIDField())


class SetGoalsSerializer(serializers.Serializer):
    goal_ids = serializers.ListField(child=serializers.UUIDField())


class SubjectSerializer(serializers.ModelSerializer):
    subject_id = serializers.CharField(source='id', read_only=True)
    progress_percent = serializers.SerializerMethodField()
    locked = serializers.SerializerMethodField()
    badge = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ['id', 'subject_id', 'name', 'slug', 'icon_asset', 'progress_percent', 'locked', 'badge']

    def get_progress_percent(self, obj):
        student = self.context.get('student')
        if not student:
            return 0
        topics = Topic.objects.filter(subject=obj, curriculum=student.curriculum)
        if not topics.exists():
            return 0
        completed = StudentTopicProgress.objects.filter(student=student, topic__in=topics, status='completed').count()
        return int((completed / topics.count()) * 100)

    def get_locked(self, obj):
        student = self.context.get('student')
        if not student:
            return False
        if student.grade:
            availability = SubjectGradeAvailability.objects.filter(subject=obj, grade=student.grade).first()
            if availability and not availability.is_unlocked_default:
                unlock = StudentSubjectUnlock.objects.filter(student=student, subject=obj).exists()
                return not unlock
        return False

    def get_badge(self, obj):
        student = self.context.get('student')
        if not student:
            return None
        current_topic = StudentTopicProgress.objects.filter(student=student, topic__subject=obj, status='current').first()
        if current_topic:
            return f"Next: {current_topic.topic.name}"
        return None


class TopicSerializer(serializers.ModelSerializer):
    student_status = serializers.SerializerMethodField()
    world_name = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ['id', 'name', 'slug', 'grade_level', 'order_index', 'student_status', 'world_name']

    def get_student_status(self, obj):
        student = self.context.get('student')
        if not student:
            return 'locked'
        prog = StudentTopicProgress.objects.filter(student=student, topic=obj).first()
        return prog.status if prog else 'locked'

    def get_world_name(self, obj):
        if hasattr(obj, 'journey_meta') and obj.journey_meta:
            return obj.journey_meta.world_name
        return obj.name


class MissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mission
        fields = ['id', 'topic_id', 'tier_id', 'name', 'slug', 'order_index', 'xp_reward', 'content']


class TestSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    estimated_minutes = serializers.SerializerMethodField()

    class Meta:
        model = Test
        fields = ['id', 'name', 'slug', 'intro_text', 'question_count', 'estimated_minutes']

    def get_question_count(self, obj):
        return obj.questions.count()

    def get_estimated_minutes(self, obj):
        return max(1, obj.questions.count() * 1)


class TestQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestQuestion
        fields = ['id', 'question_text', 'question_type', 'options', 'order_index', 'points']


class ChallengeSerializer(serializers.ModelSerializer):
    topic = serializers.CharField(source='topic.name', read_only=True, allow_null=True)

    class Meta:
        model = Challenge
        fields = ['id', 'name', 'slug', 'description', 'topic']


class ChallengeOpponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeOpponent
        fields = ['id', 'name', 'avatar_id', 'difficulty', 'ai_profile']


class StudentCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentCard
        fields = ['id', 'card_type', 'title', 'data', 'earned_at']


class CurriculumSerializer(serializers.ModelSerializer):
    subjects_count = serializers.SerializerMethodField()
    topics_count = serializers.SerializerMethodField()

    class Meta:
        model = Curriculum
        fields = ['id', 'name', 'code', 'board', 'grade', 'description', 'is_active', 'subjects_count', 'topics_count', 'created_at', 'updated_at']

    def get_subjects_count(self, obj):
        return obj.subjects.count()

    def get_topics_count(self, obj):
        return obj.topics.count()


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = ['id', 'name', 'slug', 'description', 'icon_asset', 'order_index', 'is_active']


class LearnBeforeTestStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnBeforeTestStep
        fields = [
            'id', 'step_key', 'title', 'teaching_text', 'key_idea',
            'image_url', 'image_prompt', 'nova_script', 'mini_question', 'order_index'
        ]


class LearningContentSerializer(serializers.ModelSerializer):
    learn_steps = LearnBeforeTestStepSerializer(many=True, read_only=True)

    class Meta:
        model = LearningContent
        fields = [
            'id', 'package_id', 'teaching_method', 'explanation', 'image_url',
            'image_prompt', 'hints', 'nova_script', 'nova_feedback', 'learn_before_test', 'learn_steps'
        ]


class CheckForUnderstandingQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckForUnderstandingQuestion
        fields = ['id', 'question_text', 'options', 'correct_answer', 'difficulty', 'explanation', 'order_index']


class ConceptTestQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptTestQuestion
        fields = ['id', 'question_text', 'options', 'correct_answer', 'difficulty', 'marks', 'explanation', 'order_index', 'is_one_time']


class BattleQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BattleQuestion
        fields = ['id', 'question_text', 'options', 'correct_answer', 'difficulty', 'xp', 'explanation', 'order_index']


class ChallengeQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeQuestion
        fields = ['id', 'question_text', 'options', 'correct_answer', 'difficulty', 'xp', 'explanation', 'nova_feedback', 'order_index']


class ConceptQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptQuestion
        fields = [
            'id', 'question_type', 'question_text', 'options', 'correct_answer',
            'difficulty', 'marks_or_xp', 'explanation', 'nova_feedback', 'order_index'
        ]


class ConceptSerializer(serializers.ModelSerializer):
    packages_count = serializers.SerializerMethodField()
    available_themes = serializers.SerializerMethodField()

    class Meta:
        model = Concept
        fields = ['id', 'topic_id', 'name', 'slug', 'learning_objective', 'order_index', 'packages_count', 'available_themes']

    def get_packages_count(self, obj):
        return obj.packages.count()

    def get_available_themes(self, obj):
        return list(obj.packages.values_list('theme__name', flat=True))


class ConceptPackageListSerializer(serializers.ModelSerializer):
    concept_name = serializers.CharField(source='concept.name', read_only=True)
    topic_name = serializers.CharField(source='concept.topic.name', read_only=True)
    subject_name = serializers.CharField(source='concept.topic.subject.name', read_only=True)
    grade = serializers.CharField(source='concept.topic.grade_level', read_only=True)
    board = serializers.CharField(source='concept.topic.board', read_only=True)
    theme = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    learn_steps_count = serializers.SerializerMethodField()

    class Meta:
        model = ConceptPackage
        fields = [
            'id', 'concept_id', 'concept_name', 'topic_name', 'subject_name',
            'grade', 'board', 'theme', 'content_type', 'is_published',
            'learn_steps_count', 'question_count', 'created_at', 'updated_at'
        ]

    def get_theme(self, obj):
        return obj.theme.name if obj.theme else ''

    def get_learn_steps_count(self, obj):
        return obj.learn_steps.count()

    def get_question_count(self, obj):
        segregated_count = (
            obj.cfu_questions.count() +
            obj.test_questions.count() +
            obj.battle_questions.count() +
            obj.challenge_questions.count()
        )
        legacy_count = obj.questions.count()
        return max(segregated_count, legacy_count)
