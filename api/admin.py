from django.contrib import admin
from api.models import (
    Parent, Student, Interest, Goal, AvatarCharacter, AvatarCategory, AvatarItem,
    Curriculum, Theme, Subject, SubjectGradeAvailability, Topic, TopicJourneyMeta, Concept,
    ConceptPackage, LearningContent, LearnBeforeTestStep, CheckForUnderstandingQuestion, ConceptTestQuestion,
    BattleQuestion, ConceptQuestion, TopicTier, Mission, Test, TestQuestion,
    Challenge, ChallengeQuestion, ChallengeOpponent
)

@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'board', 'grade', 'is_active')
    list_filter = ('board', 'grade', 'is_active')
    search_fields = ('name', 'code')

@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order_index', 'is_active')
    search_fields = ('name', 'slug')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'curriculum', 'slug', 'order_index', 'is_active')
    list_filter = ('curriculum', 'is_active')
    search_fields = ('name', 'slug')

@admin.register(SubjectGradeAvailability)
class SubjectGradeAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('subject', 'grade', 'is_unlocked_default')
    list_filter = ('grade', 'is_unlocked_default')

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'curriculum', 'subject', 'board', 'grade_level', 'order_index')
    list_filter = ('curriculum', 'board', 'grade_level', 'subject')
    search_fields = ('name', 'slug')

class LearnBeforeTestStepInline(admin.TabularInline):
    model = LearnBeforeTestStep
    extra = 3

class CFUQuestionInline(admin.TabularInline):
    model = CheckForUnderstandingQuestion
    extra = 1

class ConceptTestQuestionInline(admin.TabularInline):
    model = ConceptTestQuestion
    extra = 1

class BattleQuestionInline(admin.TabularInline):
    model = BattleQuestion
    extra = 1

class ChallengeQuestionInline(admin.TabularInline):
    model = ChallengeQuestion
    extra = 1

@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display = ('name', 'topic', 'order_index', 'created_at')
    list_filter = ('topic__board', 'topic__grade_level', 'topic__subject')
    search_fields = ('name', 'learning_objective')

@admin.register(ConceptPackage)
class ConceptPackageAdmin(admin.ModelAdmin):
    list_display = ('concept', 'theme', 'is_published', 'created_at')
    list_filter = ('theme', 'is_published')
    search_fields = ('concept__name', 'teaching_method', 'explanation')
    inlines = [LearnBeforeTestStepInline, CFUQuestionInline, ConceptTestQuestionInline, BattleQuestionInline, ChallengeQuestionInline]

@admin.register(LearningContent)
class LearningContentAdmin(admin.ModelAdmin):
    list_display = ('package', 'concept', 'theme', 'created_at')
    search_fields = ('teaching_method', 'explanation')

@admin.register(LearnBeforeTestStep)
class LearnBeforeTestStepAdmin(admin.ModelAdmin):
    list_display = ('package', 'step_key', 'title', 'order_index', 'created_at')
    list_filter = ('step_key',)
    search_fields = ('title', 'teaching_text', 'key_idea')

@admin.register(CheckForUnderstandingQuestion)
class CheckForUnderstandingQuestionAdmin(admin.ModelAdmin):
    list_display = ('package', 'question_text', 'difficulty', 'correct_answer')
    search_fields = ('question_text', 'explanation')

@admin.register(ConceptTestQuestion)
class ConceptTestQuestionAdmin(admin.ModelAdmin):
    list_display = ('package', 'question_text', 'difficulty', 'marks', 'order_index')
    search_fields = ('question_text', 'explanation')

@admin.register(BattleQuestion)
class BattleQuestionAdmin(admin.ModelAdmin):
    list_display = ('package', 'question_text', 'difficulty', 'xp', 'order_index')
    search_fields = ('question_text', 'explanation')

@admin.register(ChallengeQuestion)
class ChallengeQuestionAdmin(admin.ModelAdmin):
    list_display = ('package', 'question_text', 'difficulty', 'xp', 'order_index')
    search_fields = ('question_text', 'explanation')

@admin.register(ConceptQuestion)
class ConceptQuestionAdmin(admin.ModelAdmin):
    list_display = ('package', 'question_type', 'difficulty', 'marks_or_xp', 'order_index')
    list_filter = ('question_type', 'difficulty')
    search_fields = ('question_text', 'explanation')

@admin.register(TopicTier)
class TopicTierAdmin(admin.ModelAdmin):
    list_display = ('topic', 'tier_key', 'label', 'required_plan', 'order_index')
    list_filter = ('tier_key', 'required_plan')

@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'topic', 'tier', 'concept', 'xp_reward', 'order_index')
    list_filter = ('topic__subject', 'tier')
    search_fields = ('name', 'slug')

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('name', 'topic', 'slug')
    search_fields = ('name', 'slug')

@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ('test', 'question_type', 'points', 'order_index')
    list_filter = ('question_type',)

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('name', 'topic', 'slug')
    search_fields = ('name', 'slug')

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'order_index', 'is_active')

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'order_index', 'is_active')
