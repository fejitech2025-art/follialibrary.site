from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import Profile
from social.models import Post

User = get_user_model()


class RankingApiTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="rank-author")
        self.reader = User.objects.create_user(username="rank-reader")
        for user in (self.author, self.reader):
            Profile.objects.update_or_create(user=user, defaults={"username": user.username})
        self.post = Post.objects.create(author=self.author, body="A real post for ranking")
        self.client = APIClient()
        self.client.force_authenticate(self.reader)

    def test_repeated_like_unlike_and_relike_share_one_reversible_event(self):
        url = f"/api/posts/{self.post.pk}/like/"
        self.assertEqual(self.client.post(url).status_code, 200)
        self.client.delete(url)
        self.client.post(url)

        from ranking.models import RankEvent
        from ranking.service import rank_for_user
        events = RankEvent.objects.filter(user=self.author, activity_key=f"post-like:{self.reader.pk}:{self.post.pk}")
        self.assertEqual(events.count(), 1)
        self.assertTrue(events.get().active)
        self.assertEqual(rank_for_user(self.author.pk, "overall")["score"], 2)
        self.assertEqual(self.client.get("/api/ranks/?period=overall").data["me"]["score"], 0)

    @override_settings(RANKING_DAILY_COMMENT_LIMIT=2)
    def test_comment_awards_are_capped_and_self_comments_do_not_score(self):
        comment_url = f"/api/posts/{self.post.pk}/comments/"
        for content in ("A meaningful comment one", "A meaningful comment two", "A meaningful comment three"):
            response = self.client.post(comment_url, {"content": content}, format="json")
            self.assertEqual(response.status_code, 201, response.data)

        from ranking.service import rank_for_user
        self.assertEqual(rank_for_user(self.reader.pk, "overall")["score"], 2)
        self.assertEqual(rank_for_user(self.author.pk, "overall")["score"], 6)

        self.client.force_authenticate(self.author)
        self.client.post(comment_url, {"content": "A long self comment should not score"}, format="json")
        self.assertEqual(rank_for_user(self.author.pk, "overall")["score"], 6)

    @override_settings(RANKING_DAILY_POST_LIMIT=1)
    def test_deleting_a_post_does_not_reopen_the_daily_publication_cap(self):
        from ranking.service import award_post, rank_for_user, undo_post

        first = Post.objects.create(author=self.author, body="First capped post")
        award_post(first)
        undo_post(first)
        second = Post.objects.create(author=self.author, body="Second post on the same day")
        award_post(second)

        self.assertEqual(rank_for_user(self.author.pk, "overall")["score"], 0)

    def test_leaderboard_uses_authoritative_scores_and_period(self):
        from ranking.service import record_event

        record_event(self.author, "post_published", "rank-api-author-post")
        record_event(self.reader, "resource_published", "rank-api-reader-resource")
        response = self.client.get("/api/ranks/?period=overall")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["leaderboard"][0]["user_id"], self.author.pk)
        self.assertEqual(response.data["me"], {"rank": 2, "score": 8})
        self.assertEqual(self.client.get("/api/ranks/?period=weekly").status_code, 400)
