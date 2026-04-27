from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import CalendarEvent


@login_required
def calendar_view(request):
    events = CalendarEvent.objects.filter(
        start_date__gte=timezone.now() - timezone.timedelta(days=30)
    )[:50]
    return render(request, 'calendar/calendar.html', {'events': events})


@login_required
@require_http_methods(["GET"])
def event_list_api(request):
    events = CalendarEvent.objects.filter(
        start_date__gte=timezone.now() - timezone.timedelta(days=30)
    )[:50]
    
    data = [{
        'id': str(e.id),
        'title': e.title,
        'start': e.start_date.isoformat(),
        'end': e.end_date.isoformat() if e.end_date else None,
        'color': e.color,
        'type': e.event_type,
    } for e in events]
    
    return JsonResponse({'events': data})


@login_required
@require_http_methods(["POST"])
def event_create_api(request):
    import json
    data = json.loads(request.body)
    
    event = CalendarEvent.objects.create(
        title=data.get('title'),
        description=data.get('description', ''),
        event_type=data.get('event_type', 'other'),
        color=data.get('color', 'primary'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        is_all_day=data.get('is_all_day', False),
        location=data.get('location', ''),
        link=data.get('link', ''),
        created_by=request.user,
    )
    
    return JsonResponse({'id': str(event.id), 'message': 'Event created'})
