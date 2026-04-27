from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test

from .models import MeetingRoom, RoomParticipant, RoomMessage


def is_admin_or_conseiller(user):
    return user.is_authenticated and user.role in ('admin', 'conseiller')


@login_required
def rooms_list_view(request):
    """List all active meeting rooms."""
    rooms = MeetingRoom.objects.filter(
        is_active=True
    ).exclude(status=MeetingRoom.Status.ENDED).order_by('-created_at')

    user_rooms = []
    for room in rooms:
        user_rp = room.participants.filter(user=request.user).first()
        room.user_is_participant = user_rp is not None
        room.user_role = user_rp.role if user_rp else ""
        room.user_rooms = user_rooms
        user_rooms.append(room)

    return render(request, 'videoconf/rooms_list.html', {
        'rooms': rooms,
    })


@login_required
def room_detail_view(request, room_id):
    """View a specific meeting room."""
    room = get_object_or_404(MeetingRoom, id=room_id)
    user_rp = room.participants.filter(user=request.user).first()

    return render(request, 'videoconf/meeting_room_new.html', {
        'room': room,
        'user_rp': user_rp,
    })


@login_required
@user_passes_test(is_admin_or_conseiller)
def create_room_view(request):
    """Create a new meeting room (admin/conseiller only)."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        google_meet_link = request.POST.get('google_meet_link', '').strip()
        access_code = request.POST.get('access_code', '').strip()
        is_public = request.POST.get('is_public') == 'on'
        max_participants = int(request.POST.get('max_participants', 50))

        if not name:
            messages.error(request, "Le nom de la salle est requis.")
            return redirect('videoconf:create_room')

        room = MeetingRoom.objects.create(
            name=name,
            description=description,
            created_by=request.user,
            google_meet_link=google_meet_link,
            access_code=access_code,
            is_public=is_public,
            max_participants=max_participants,
            status=MeetingRoom.Status.LIVE,
            started_at=timezone.now(),
        )

        RoomParticipant.objects.create(
            room=room,
            user=request.user,
            role=RoomParticipant.Role.HOST,
        )

        messages.success(request, f"Salle '{name}' créée avec succès!")
        return redirect('videoconf:room_detail', room_id=room.id)

    return render(request, 'videoconf/create_room.html')


@login_required
def join_room_view(request, room_id):
    """Join a meeting room."""
    room = get_object_or_404(MeetingRoom, id=room_id)

    if not room.is_active:
        messages.error(request, "Cette salle n'est plus active.")
        return redirect('videoconf:rooms_list')

    if room.status == MeetingRoom.Status.ENDED:
        messages.error(request, "Cette réunion est terminée.")
        return redirect('videoconf:rooms_list')

    # Check access code if required
    if room.access_code:
        submitted_code = request.POST.get('access_code', '').strip()
        if submitted_code != room.access_code:
            messages.error(request, "Code d'accès incorrect.")
            return redirect('videoconf:room_detail', room_id=room.id)

    # Check if already participant
    existing = room.participants.filter(user=request.user).first()
    if existing:
        if existing.status == 'left':
            existing.status = 'in_room'
            existing.left_at = None
            existing.save()
        return redirect('videoconf:room_detail', room_id=room.id)

    # Check max participants
    if room.participants.filter(status='in_room').count() >= room.max_participants:
        messages.error(request, "La salle est pleine.")
        return redirect('videoconf:rooms_list')

    role = RoomParticipant.Role.PARTICIPANT
    if room.created_by_id == request.user.id:
        role = RoomParticipant.Role.HOST

    RoomParticipant.objects.create(
        room=room,
        user=request.user,
        role=role,
    )

    RoomMessage.objects.create(
        room=room,
        user=request.user,
        content=f"{request.user.full_name} a rejoint la salle",
        is_system_message=True,
    )

    return redirect('videoconf:room_detail', room_id=room.id)


@login_required
def leave_room_view(request, room_id):
    """Leave a meeting room."""
    rp = RoomParticipant.objects.filter(
        room_id=room_id, user=request.user
    ).first()

    if rp:
        rp.status = 'left'
        rp.left_at = timezone.now()
        rp.save()

        RoomMessage.objects.create(
            room=rp.room,
            user=request.user,
            content=f"{request.user.full_name} a quitté la salle",
            is_system_message=True,
        )

        # If host leaves and no other host/moderator, end room
        if rp.role == 'host':
            others = rp.room.participants.filter(
                status='in_room'
            ).exclude(user=request.user)
            if not others.exists():
                rp.room.status = MeetingRoom.Status.ENDED
                rp.room.ended_at = timezone.now()
                rp.room.is_active = False
                rp.room.save()

    messages.success(request, "Vous avez quitté la salle.")
    return redirect('videoconf:rooms_list')
