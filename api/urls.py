from django.urls import path
from api import views

urlpatterns = [
    # Auth & Parent Accounts
    path('auth/parent/signup', views.ParentSignupView.as_view(), name='parent-signup'),
    path('auth/parent/login', views.ParentLoginView.as_view(), name='parent-login'),
    path('auth/parent/forgot-password', views.ParentForgotPasswordView.as_view(), name='parent-forgot-password'),
    path('auth/parent/logout', views.ParentLogoutView.as_view(), name='parent-logout'),
    path('parent/me', views.ParentMeView.as_view(), name='parent-me'),
    path('parent/students', views.ParentStudentsView.as_view(), name='parent-students'),
    path('parent/overview', views.ParentOverviewView.as_view(), name='parent-overview'),
    path('parent/verification/start', views.ParentVerificationStartView.as_view(), name='parent-verification-start'),
    path('parent/verification/verify', views.ParentVerificationVerifyView.as_view(), name='parent-verification-verify'),
    path('parent/pin/verify', views.ParentPinVerifyView.as_view(), name='parent-pin-verify'),
    path('parent/evidence', views.ParentEvidenceView.as_view(), name='parent-evidence'),
    path('parent/plan', views.ParentWeeklyPlanView.as_view(), name='parent-weekly-plan'),

    # Students & Onboarding
    path('students', views.CreateStudentView.as_view(), name='create-student'),
    path('students/<uuid:studentId>/grade-board', views.UpdateGradeBoardView.as_view(), name='update-grade-board'),
    path('students/<uuid:studentId>/learning-path', views.StudentLearningPathView.as_view(), name='student-learning-path'),
    path('students/<uuid:studentId>/settings', views.StudentSettingsView.as_view(), name='student-settings'),
    path('students/<uuid:studentId>/nova/messages', views.StudentNovaMessagesView.as_view(), name='student-nova-messages'),
    path('avatar/characters', views.AvatarCharactersView.as_view(), name='avatar-characters'),
    path('avatar/items', views.AvatarItemsView.as_view(), name='avatar-items'),
    path('students/<uuid:studentId>/avatar', views.SaveStudentAvatarView.as_view(), name='save-student-avatar'),
    path('interests', views.InterestsCatalogView.as_view(), name='interests-catalog'),
    path('students/<uuid:studentId>/interests', views.StudentInterestsView.as_view(), name='student-interests'),
    path('goals', views.GoalsCatalogView.as_view(), name='goals-catalog'),
    path('students/<uuid:studentId>/goals', views.StudentGoalsView.as_view(), name='student-goals'),
    path('students/<uuid:studentId>/onboarding/steps/<str:stepKey>/complete', views.CompleteOnboardingStepView.as_view(), name='complete-onboarding-step'),
    path('students/<uuid:studentId>/onboarding/status', views.OnboardingStatusView.as_view(), name='onboarding-status'),
    path('students/<uuid:studentId>/nova/greet', views.NovaGreetView.as_view(), name='nova-greet'),

    # Home
    path('students/<uuid:studentId>/home', views.StudentHomeView.as_view(), name='student-home'),

    # Learn
    path('students/<uuid:studentId>/subjects', views.StudentSubjectsView.as_view(), name='student-subjects'),
    path('subjects/<uuid:subjectId>/topics', views.SubjectTopicsView.as_view(), name='subject-topics'),
    path('students/<uuid:studentId>/topics/<uuid:topicId>', views.StudentTopicDetailView.as_view(), name='student-topic-detail'),
    path('missions/<uuid:missionId>', views.MissionDetailView.as_view(), name='mission-detail'),
    path('students/<uuid:studentId>/missions/<uuid:missionId>/start', views.StartMissionView.as_view(), name='start-mission'),
    path('students/<uuid:studentId>/missions/<uuid:missionId>/complete', views.CompleteMissionView.as_view(), name='complete-mission'),
    path('students/<uuid:studentId>/missions/<uuid:missionId>/review', views.StudentMissionReviewView.as_view(), name='mission-review'),
    path('learning-packages/<uuid:packageId>', views.LearningPackageDetailView.as_view(), name='learning-package-detail'),

    # Journey
    path('students/<uuid:studentId>/journey', views.StudentJourneyView.as_view(), name='student-journey'),
    path('students/<uuid:studentId>/companion-activities/<uuid:activityId>/complete', views.CompleteCompanionActivityView.as_view(), name='complete-companion-activity'),

    # Test
    path('topics/<uuid:topicId>/tests', views.TopicTestsView.as_view(), name='topic-tests'),
    path('tests/<uuid:testId>', views.TestDetailView.as_view(), name='test-detail'),
    path('students/<uuid:studentId>/tests/<uuid:testId>/attempts', views.StartTestAttemptView.as_view(), name='start-test-attempt'),
    path('tests/attempts/<uuid:attemptId>/questions/<int:order>', views.GetTestQuestionView.as_view(), name='get-test-question'),
    path('tests/attempts/<uuid:attemptId>/answers', views.SubmitTestAnswerView.as_view(), name='submit-test-answer'),
    path('tests/attempts/<uuid:attemptId>/complete', views.CompleteTestAttemptView.as_view(), name='complete-test-attempt'),
    path('tests/attempts/<uuid:attemptId>/result', views.GetTestResultView.as_view(), name='get-test-result'),
    path('tests/attempts/<uuid:attemptId>/review', views.TestAttemptReviewView.as_view(), name='test-attempt-review'),
    path('students/<uuid:studentId>/extra-learning', views.StudentExtraLearningView.as_view(), name='student-extra-learning'),

    # Challenge
    path('challenges', views.ListChallengesView.as_view(), name='list-challenges'),
    path('challenges/<uuid:challengeId>/opponents', views.ChallengeOpponentsView.as_view(), name='challenge-opponents'),
    path('challenges/<uuid:challengeId>/preview', views.PreviewChallengeView.as_view(), name='preview-challenge'),
    path('students/<uuid:studentId>/challenge-battles', views.StartChallengeBattleView.as_view(), name='start-challenge-battle'),
    path('challenge-battles/<uuid:battleId>/complete', views.CompleteChallengeBattleView.as_view(), name='complete-challenge-battle'),
    path('challenge-battles/<uuid:battleId>/result', views.ChallengeBattleResultView.as_view(), name='challenge-battle-result'),
    path('challenges/<uuid:challengeId>/leaderboard', views.ChallengeLeaderboardView.as_view(), name='challenge-leaderboard'),

    # Profile
    path('students/<uuid:studentId>/profile', views.StudentProfileView.as_view(), name='student-profile'),
    path('students/<uuid:studentId>/profile/our-journey', views.StudentOurJourneyView.as_view(), name='student-our-journey'),
    path('students/<uuid:studentId>/profile/cards', views.StudentCardsView.as_view(), name='student-cards'),
    path('students/<uuid:studentId>/break-passes', views.StudentBreakPassView.as_view(), name='student-break-passes'),

    # Curriculum & Content Studio Ingestion
    path('admin/content/feed', views.AdminContentFeedView.as_view(), name='admin-content-feed'),
    path('admin/content/packages', views.AdminContentPackageListView.as_view(), name='admin-content-packages-list'),
    path('admin/content/packages/<uuid:packageId>', views.AdminContentPackageDetailView.as_view(), name='admin-content-package-detail'),
    path('curriculum/tree', views.CurriculumTreeView.as_view(), name='curriculum-tree'),
    path('curriculums', views.CurriculumListView.as_view(), name='curriculum-list'),
    path('curriculums/<uuid:curriculumId>', views.CurriculumDetailView.as_view(), name='curriculum-detail'),
    path('curriculums/<uuid:curriculumId>/subjects', views.CurriculumSubjectCreateView.as_view(), name='curriculum-add-subject'),
    path('topics/<uuid:topicId>/concepts', views.TopicConceptCreateView.as_view(), name='topic-add-concept'),
    path('themes', views.ThemeListView.as_view(), name='themes-list'),
]
