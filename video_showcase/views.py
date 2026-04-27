from django.shortcuts import render
from .models import VideoAnnouncement


def showcase_view(request):
    """Full-screen video showcase page."""
    videos = VideoAnnouncement.objects.filter(
        is_active=True
    ).order_by('order', '-created_at')[:12]

    return render(request, 'video_showcase/showcase.html', {
        'videos': videos,
        'is_showcase': True,
    })
