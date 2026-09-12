from django.core.management.base import BaseCommand
from api.models import (
    Interest, Goal, AvatarCharacter, AvatarCategory, AvatarItem,
    Subject, SubjectGradeAvailability, Topic, TopicJourneyMeta, TopicTier,
    Mission, Test, TestQuestion, Challenge, ChallengeOpponent, CompanionActivity
)

class Command(BaseCommand):
    help = 'Seeds initial catalog data for Kidsverse'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Kidsverse data...")

        # 1. Interests
        interests_data = [
            {"key": "space", "name": "Space", "thumbnail_url": "https://assets.kidsverse.app/interests/space.png", "order_index": 1},
            {"key": "animals", "name": "Animals", "thumbnail_url": "https://assets.kidsverse.app/interests/animals.png", "order_index": 2},
            {"key": "art", "name": "Art", "thumbnail_url": "https://assets.kidsverse.app/interests/art.png", "order_index": 3},
            {"key": "sports", "name": "Sports", "thumbnail_url": "https://assets.kidsverse.app/interests/sports.png", "order_index": 4},
        ]
        for item in interests_data:
            Interest.objects.update_or_create(key=item["key"], defaults=item)

        # 2. Goals
        goals_data = [
            {"key": "master_school_topics", "name": "Master school topics", "tagline": "Better grades, strong foundation", "icon_asset": "book", "order_index": 1},
            {"key": "build_confidence", "name": "Build confidence", "tagline": "Feel empowered in every subject", "icon_asset": "star", "order_index": 2},
            {"key": "prepare_competitions", "name": "Prepare for competitions", "tagline": "Olympiads and advanced problem solving", "icon_asset": "trophy", "order_index": 3},
            {"key": "not_sure_yet", "name": "Not sure yet — let Nova decide", "tagline": "Adaptive learning path tailored by AI", "icon_asset": "sparkles", "order_index": 4},
        ]
        for item in goals_data:
            Goal.objects.update_or_create(key=item["key"], defaults=item)

        # 3. Avatar Characters & Categories & Items
        char1, _ = AvatarCharacter.objects.update_or_create(
            slug="explorer-boy-1",
            defaults={"name": "Explorer Boy 1", "base_image_url": "https://assets.kidsverse.app/avatars/explorer_boy_1.png", "order_index": 1}
        )
        char2, _ = AvatarCharacter.objects.update_or_create(
            slug="explorer-girl-1",
            defaults={"name": "Explorer Girl 1", "base_image_url": "https://assets.kidsverse.app/avatars/explorer_girl_1.png", "order_index": 2}
        )

        cat_outfit, _ = AvatarCategory.objects.update_or_create(key="outfit", defaults={"label": "Outfit", "order_index": 1})
        cat_hair, _ = AvatarCategory.objects.update_or_create(key="hair", defaults={"label": "Hair", "order_index": 2})
        cat_acc, _ = AvatarCategory.objects.update_or_create(key="accessories", defaults={"label": "Accessories", "order_index": 3})

        AvatarItem.objects.update_or_create(
            category=cat_outfit, slug="explorers-jacket",
            defaults={"name": "Explorer's Jacket", "description": "Ready for every adventure, near or far.", "thumbnail_url": "https://assets.kidsverse.app/items/jacket.png", "is_default": True}
        )
        AvatarItem.objects.update_or_create(
            category=cat_hair, slug="explorer-cap",
            defaults={"name": "Explorer Cap", "description": "Keep cool while exploring.", "thumbnail_url": "https://assets.kidsverse.app/items/cap.png", "is_default": True}
        )
        AvatarItem.objects.update_or_create(
            category=cat_acc, slug="explorer-compass",
            defaults={"name": "Explorer Compass", "description": "Never get lost on your journey.", "thumbnail_url": "https://assets.kidsverse.app/items/compass.png", "is_default": True}
        )

        # 4. Subjects
        subj_maths, _ = Subject.objects.update_or_create(slug="maths", defaults={"name": "Maths", "icon_asset": "calculator", "order_index": 1})
        subj_lit, _ = Subject.objects.update_or_create(slug="literacy", defaults={"name": "Literacy", "icon_asset": "book-open", "order_index": 2})
        subj_comp, _ = Subject.objects.update_or_create(slug="computer", defaults={"name": "Computer", "icon_asset": "cpu", "order_index": 3})

        SubjectGradeAvailability.objects.update_or_create(subject=subj_maths, grade="4", defaults={"is_unlocked_default": True})
        SubjectGradeAvailability.objects.update_or_create(subject=subj_lit, grade="4", defaults={"is_unlocked_default": True})
        SubjectGradeAvailability.objects.update_or_create(subject=subj_comp, grade="4", defaults={"is_unlocked_default": False})

        # 5. Topics
        topic_frac, _ = Topic.objects.update_or_create(
            subject=subj_maths, grade_level="4", slug="fractions",
            defaults={"name": "Fractions", "description": "Understand parts of a whole, equivalent fractions, compare and order...", "order_index": 1}
        )
        TopicJourneyMeta.objects.update_or_create(
            topic=topic_frac,
            defaults={"world_name": "Numbers Nebula", "tagline": "Master parts of a whole", "map_x": 12.5, "map_y": 30.0}
        )

        topic_lit, _ = Topic.objects.update_or_create(
            subject=subj_lit, grade_level="4", slug="alphabet-bay",
            defaults={"name": "Alphabet Bay", "description": "Letters and sounds", "order_index": 1}
        )
        TopicJourneyMeta.objects.update_or_create(
            topic=topic_lit,
            defaults={"world_name": "Alphabet Bay", "tagline": "Letters and sounds", "map_x": 12.5, "map_y": 30.0}
        )

        # 6. Tiers
        tier1, _ = TopicTier.objects.update_or_create(topic=topic_frac, tier_key="school_syllabus", defaults={"label": "School Syllabus", "order_index": 1, "required_plan": "free"})
        tier2, _ = TopicTier.objects.update_or_create(topic=topic_frac, tier_key="kidsverse_plus", defaults={"label": "Kidsverse Plus", "order_index": 2, "required_plan": "plus"})
        tier3, _ = TopicTier.objects.update_or_create(topic=topic_frac, tier_key="competition_edge", defaults={"label": "Competition Edge", "order_index": 3, "required_plan": "plus"})

        # 7. Missions
        m1, _ = Mission.objects.update_or_create(
            topic=topic_frac, slug="what-is-a-fraction",
            defaults={"tier": tier1, "name": "What is a Fraction?", "order_index": 1, "xp_reward": 30, "content": {"type": "interactive_lesson", "steps": ["Lesson 1: Parts of a whole"]}}
        )
        m2, _ = Mission.objects.update_or_create(
            topic=topic_frac, slug="equivalent-fractions",
            defaults={"tier": tier1, "name": "Equivalent Fractions", "order_index": 2, "xp_reward": 30, "content": {"type": "interactive_lesson", "steps": ["Lesson 2: Finding equivalent fractions"]}}
        )
        m3, _ = Mission.objects.update_or_create(
            topic=topic_frac, slug="compare-and-order",
            defaults={"tier": tier1, "name": "Compare & Order", "order_index": 3, "xp_reward": 30, "content": {"type": "interactive_lesson", "steps": ["Lesson 3: Ordering fractions"]}}
        )
        m4, _ = Mission.objects.update_or_create(
            topic=topic_frac, slug="mars-supply-rescue",
            defaults={"tier": tier2, "name": "Mars Supply Rescue", "order_index": 4, "xp_reward": 50, "content": {"type": "challenge_lesson", "steps": ["Rescue mission"]}}
        )

        # 8. Test & Test Questions
        test1, _ = Test.objects.update_or_create(
            topic=topic_frac, slug="fractions",
            defaults={"name": "Fractions Check", "intro_text": "Let's see what you've learned about fractions!"}
        )

        TestQuestion.objects.update_or_create(
            test=test1, order_index=1,
            defaults={
                "question_text": "3/4 is the same as?",
                "question_type": "mcq",
                "options": [{"id": "a", "text": "6/8"}, {"id": "b", "text": "3/5"}, {"id": "c", "text": "1/2"}, {"id": "d", "text": "4/3"}],
                "correct_answer": "a",
                "points": 1
            }
        )

        # 9. Challenge & Opponents
        ch1, _ = Challenge.objects.update_or_create(
            slug="fractions-duel",
            defaults={"topic": topic_frac, "name": "Fractions Duel", "description": "Battle AI opponents in fraction arithmetic!"}
        )
        ChallengeOpponent.objects.update_or_create(
            challenge=ch1, name="Robo Rex",
            defaults={"avatar_id": "robo-rex-1", "difficulty": "medium", "ai_profile": {"speed": "normal", "accuracy": 0.8}}
        )

        # 10. Companion Activities
        CompanionActivity.objects.update_or_create(subject=subj_lit, name="Raise the Flag", defaults={"order_index": 1})
        CompanionActivity.objects.update_or_create(subject=subj_lit, name="Read Together", defaults={"order_index": 2})
        CompanionActivity.objects.update_or_create(subject=subj_lit, name="Talk with Nova", defaults={"order_index": 3})

        self.stdout.write(self.style.SUCCESS("Successfully seeded catalog data!"))
