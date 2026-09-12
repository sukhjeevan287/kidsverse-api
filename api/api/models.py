import uuid
from django.db import models

class Parent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    password_hash = models.TextField()
    full_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'parents'

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        return self.email


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='students')
    name = models.CharField(max_length=255)
    grade = models.CharField(max_length=20, null=True, blank=True)
    board = models.CharField(max_length=50, null=True, blank=True)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'

    def __str__(self):
        return f"{self.name} ({self.grade or 'No Grade'})"


class Interest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    thumbnail_url = models.TextField(null=True, blank=True)
    order_index = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'interests'

    def __str__(self):
        return self.name


class StudentInterest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_interests')
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    selected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_interests'
        unique_together = ('student', 'interest')


class Goal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    tagline = models.CharField(max_length=150, null=True, blank=True)
    icon_asset = models.CharField(max_length=100, null=True, blank=True)
    order_index = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'goals'

    def __str__(self):
        return self.name


class StudentGoal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_goals')
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    selected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_goals'
        unique_together = ('student', 'goal')


class OnboardingStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='onboarding_steps')
    step_key = models.CharField(max_length=50)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'onboarding_steps'
        unique_together = ('student', 'step_key')


class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True)
    icon_asset = models.CharField(max_length=100, null=True, blank=True)
    order_index = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'subjects'

    def __str__(self):
        return self.name


class SubjectGradeAvailability(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grade_availabilities')
    grade = models.CharField(max_length=20)
    is_unlocked_default = models.BooleanField(default=True)

    class Meta:
        db_table = 'subject_grade_availability'
        unique_together = ('subject', 'grade')


class StudentSubjectUnlock(models.Model):
    SOURCE_CHOICES = [
        ('default', 'default'),
        ('achievement', 'achievement'),
        ('plan_upgrade', 'plan_upgrade'),
        ('parent_action', 'parent_action'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='subject_unlocks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=30, default='default', choices=SOURCE_CHOICES)

    class Meta:
        db_table = 'student_subject_unlocks'
        unique_together = ('student', 'subject')


class Topic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=150)
    slug = models.CharField(max_length=150)
    grade_level = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)
    order_index = models.IntegerField(default=0)

    class Meta:
        db_table = 'topics'
        unique_together = ('subject', 'grade_level', 'slug')

    def __str__(self):
        return f"{self.name} ({self.grade_level})"


class TopicJourneyMeta(models.Model):
    topic = models.OneToOneField(Topic, on_delete=models.CASCADE, primary_key=True, related_name='journey_meta')
    world_name = models.CharField(max_length=150)
    tagline = models.CharField(max_length=150, null=True, blank=True)
    map_x = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    map_y = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    icon_asset = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'topic_journey_meta'


class StudentTopicProgress(models.Model):
    STATUS_CHOICES = [
        ('locked', 'locked'),
        ('unlocked', 'unlocked'),
        ('current', 'current'),
        ('completed', 'completed'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='topic_progress')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='locked', choices=STATUS_CHOICES)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'student_topic_progress'
        unique_together = ('student', 'topic')


class CompanionActivity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=150)
    icon_asset = models.CharField(max_length=100, null=True, blank=True)
    order_index = models.IntegerField(default=0)

    class Meta:
        db_table = 'companion_activities'

    def __str__(self):
        return self.name


class StudentCompanionActivityLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='companion_logs')
    activity = models.ForeignKey(CompanionActivity, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_companion_activity_log'


class TopicTier(models.Model):
    TIER_KEY_CHOICES = [
        ('school_syllabus', 'School Syllabus'),
        ('kidsverse_plus', 'Kidsverse Plus'),
        ('competition_edge', 'Competition Edge'),
    ]
    PLAN_CHOICES = [
        ('free', 'free'),
        ('plus', 'plus'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='tiers')
    tier_key = models.CharField(max_length=30, choices=TIER_KEY_CHOICES)
    label = models.CharField(max_length=100)
    order_index = models.IntegerField(default=0)
    required_plan = models.CharField(max_length=30, default='free', choices=PLAN_CHOICES)

    class Meta:
        db_table = 'topic_tiers'
        unique_together = ('topic', 'tier_key')

    def __str__(self):
        return f"{self.topic.name} - {self.label}"


class Mission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='missions')
    tier = models.ForeignKey(TopicTier, on_delete=models.CASCADE, related_name='missions')
    name = models.CharField(max_length=150)
    slug = models.CharField(max_length=150)
    order_index = models.IntegerField(default=0)
    xp_reward = models.IntegerField(default=0)
    content = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'missions'
        unique_together = ('topic', 'slug')

    def __str__(self):
        return self.name


class MissionProgress(models.Model):
    STATUS_CHOICES = [
        ('locked', 'locked'),
        ('unlocked', 'unlocked'),
        ('in_progress', 'in_progress'),
        ('completed', 'completed'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='mission_progress')
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='locked', choices=STATUS_CHOICES)
    stars = models.SmallIntegerField(default=0)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'mission_progress'
        unique_together = ('student', 'mission')


class Test(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='tests')
    name = models.CharField(max_length=150)
    slug = models.CharField(max_length=150)
    intro_text = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'tests'
        unique_together = ('topic', 'slug')

    def __str__(self):
        return self.name


class TestQuestion(models.Model):
    TYPE_CHOICES = [
        ('mcq', 'mcq'),
        ('true_false', 'true_false'),
        ('short_answer', 'short_answer'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, default='mcq', choices=TYPE_CHOICES)
    options = models.JSONField(null=True, blank=True)
    correct_answer = models.CharField(max_length=255)
    order_index = models.IntegerField(default=0)
    points = models.IntegerField(default=1)

    class Meta:
        db_table = 'test_questions'


class TestAttempt(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'in_progress'),
        ('completed', 'completed'),
        ('abandoned', 'abandoned'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='in_progress', choices=STATUS_CHOICES)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'test_attempts'


class TestAttemptAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=255, null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'test_attempt_answers'
        unique_together = ('attempt', 'question')


class ExtraLearningRecommendation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='recommendations')
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    reason = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'extra_learning_recommendations'


class Challenge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=150)
    slug = models.CharField(max_length=150, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'challenges'

    def __str__(self):
        return self.name


class ChallengeOpponent(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'easy'),
        ('medium', 'medium'),
        ('hard', 'hard'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='opponents')
    name = models.CharField(max_length=150)
    avatar_id = models.CharField(max_length=100, null=True, blank=True)
    difficulty = models.CharField(max_length=20, default='medium', choices=DIFFICULTY_CHOICES)
    ai_profile = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'challenge_opponents'


class ChallengeBattle(models.Model):
    STATUS_CHOICES = [
        ('preview', 'preview'),
        ('in_progress', 'in_progress'),
        ('completed', 'completed'),
    ]
    RESULT_CHOICES = [
        ('win', 'win'),
        ('loss', 'loss'),
        ('draw', 'draw'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='challenge_battles')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    opponent = models.ForeignKey(ChallengeOpponent, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='preview', choices=STATUS_CHOICES)
    result = models.CharField(max_length=10, null=True, blank=True, choices=RESULT_CHOICES)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'challenge_battles'


class JourneyMilestone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=150)
    order_index = models.IntegerField(default=0)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'journey_milestones'


class StudentJourneyProgress(models.Model):
    STATUS_CHOICES = [
        ('locked', 'locked'),
        ('unlocked', 'unlocked'),
        ('completed', 'completed'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='journey_progress')
    milestone = models.ForeignKey(JourneyMilestone, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='locked', choices=STATUS_CHOICES)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'student_journey_progress'
        unique_together = ('student', 'milestone')


class StudentCard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='cards')
    card_type = models.CharField(max_length=50)
    title = models.CharField(max_length=150)
    data = models.JSONField(null=True, blank=True)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_cards'


class NovaInteraction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='nova_interactions')
    message = models.TextField(null=True, blank=True)
    response = models.TextField(null=True, blank=True)
    context = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nova_interactions'


class AvatarCharacter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, unique=True)
    base_image_url = models.TextField()
    order_index = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'avatar_characters'


class AvatarCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=30, unique=True)
    label = models.CharField(max_length=50)
    order_index = models.IntegerField(default=0)

    class Meta:
        db_table = 'avatar_categories'


class AvatarItem(models.Model):
    UNLOCK_CHOICES = [
        ('free', 'free'),
        ('achievement', 'achievement'),
        ('premium', 'premium'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(AvatarCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=150)
    slug = models.CharField(max_length=150)
    description = models.CharField(max_length=255, null=True, blank=True)
    thumbnail_url = models.TextField()
    render_asset_url = models.TextField(null=True, blank=True)
    unlock_type = models.CharField(max_length=20, default='free', choices=UNLOCK_CHOICES)
    is_default = models.BooleanField(default=False)
    order_index = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'avatar_items'
        unique_together = ('category', 'slug')


class StudentAvatar(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, primary_key=True, related_name='avatar')
    character = models.ForeignKey(AvatarCharacter, on_delete=models.CASCADE)
    outfit_item = models.ForeignKey(AvatarItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    hair_item = models.ForeignKey(AvatarItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    accessory_item = models.ForeignKey(AvatarItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_avatars'


class StudentAvatarUnlock(models.Model):
    SOURCE_CHOICES = [
        ('default', 'default'),
        ('achievement', 'achievement'),
        ('challenge_reward', 'challenge_reward'),
        ('premium', 'premium'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='avatar_unlocks')
    item = models.ForeignKey(AvatarItem, on_delete=models.CASCADE)
    source = models.CharField(max_length=30, default='default', choices=SOURCE_CHOICES)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_avatar_unlocks'
        unique_together = ('student', 'item')


class StudentStat(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, primary_key=True, related_name='stats')
    day_streak = models.IntegerField(default=0)
    total_xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    last_active_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_stats'


class MissionRecommendation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='mission_recommendations')
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    reason_text = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mission_recommendations'


class Skill(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'easy'),
        ('medium', 'medium'),
        ('hard', 'hard'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='skills')
    skill_key = models.CharField(max_length=100)
    name = models.CharField(max_length=150)
    difficulty = models.CharField(max_length=20, default='medium', choices=DIFFICULTY_CHOICES)
    order_index = models.IntegerField(default=0)

    class Meta:
        db_table = 'skills'
        unique_together = ('topic', 'skill_key')


class SkillPrerequisite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='prerequisites')
    prerequisite_skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='dependent_skills')
    required_mastery = models.DecimalField(max_digits=5, decimal_places=2, default=70.0)
    weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)

    class Meta:
        db_table = 'skill_prerequisites'
        unique_together = ('skill', 'prerequisite_skill')


class MissionSkill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)

    class Meta:
        db_table = 'mission_skills'
        unique_together = ('mission', 'skill')


class TestQuestionSkill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)

    class Meta:
        db_table = 'test_question_skills'
        unique_together = ('question', 'skill')


class StudentSkillMastery(models.Model):
    MASTERY_STATE_CHOICES = [
        ('not_started', 'not_started'),
        ('learning', 'learning'),
        ('secure', 'secure'),
        ('review_due', 'review_due'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='skill_masteries')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    mastery_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    independence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    attempt_count = models.IntegerField(default=0)
    correct_count = models.IntegerField(default=0)
    retention_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    last_practiced_at = models.DateTimeField(null=True, blank=True)
    next_review_at = models.DateTimeField(null=True, blank=True)
    mastery_state = models.CharField(max_length=20, default='not_started', choices=MASTERY_STATE_CHOICES)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_skill_mastery'
        unique_together = ('student', 'skill')


class LearningEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('answer', 'answer'),
        ('hint', 'hint'),
        ('retry', 'retry'),
        ('explanation', 'explanation'),
        ('read_aloud', 'read_aloud'),
        ('skip', 'skip'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy', 'easy'),
        ('medium', 'medium'),
        ('hard', 'hard'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='learning_events')
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True)
    mission = models.ForeignKey(Mission, on_delete=models.SET_NULL, null=True, blank=True)
    question = models.ForeignKey(TestQuestion, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    is_correct = models.BooleanField(null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    hint_count = models.IntegerField(default=0)
    attempt_number = models.IntegerField(default=1)
    help_requested = models.BooleanField(default=False)
    nova_intervention_used = models.BooleanField(default=False)
    confidence_before = models.SmallIntegerField(null=True, blank=True)
    confidence_after = models.SmallIntegerField(null=True, blank=True)
    difficulty_level = models.CharField(max_length=20, null=True, blank=True, choices=DIFFICULTY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'learning_events'
