from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .service import leaderboard, rank_for_user


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ranks(request):
    period = request.query_params.get("period", "overall")
    if period not in {"overall", "daily"}:
        return Response({"detail": "Period must be daily or overall."}, status=400)
    rows = leaderboard(period=period, limit=100)
    for row in rows:
        row["is_me"] = row["user_id"] == request.user.pk
    return Response({
        "period": period,
        "leaderboard": rows,
        "me": rank_for_user(request.user.pk, period),
        "rules": {
            "post": int(settings.RANKING_WEIGHTS.get("post_published", 0)),
            "like_received": int(settings.RANKING_WEIGHTS.get("post_like_received", 0)),
            "comment_written": int(settings.RANKING_WEIGHTS.get("comment_written", 0)),
            "comment_daily_limit": settings.RANKING_DAILY_COMMENT_LIMIT,
        },
    })

from django.conf import settings
