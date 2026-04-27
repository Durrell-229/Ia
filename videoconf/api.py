from ninja import Router, Schema
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from typing import List, Optional

from .models import MeetingRoom, RoomParticipant, RoomMessage
from accounts.models import User

router = Router(tags=['Videoconf'])


# ─── Schemas ───

class RoomCreateSchema(Schema):
    name: str
    description: Optional[str] = ""
    google_meet_link: Optional[str] = ""
    access_code: Optional[str] = ""
    is_public: bool = True
    max_participants: int = 50


class RoomParticipantSchema(Schema):
    id: str
    user_id: str
    user_name: str
    user_email: str
    user_avatar: Optional[str] = None
    role: str
    status: str
    is_muted: bool
    is_camera_on: bool
    joined_at: str


class RoomMessageSchema(Schema):
    id: str
    user_id: str
    user_name: str
    user_avatar: Optional[str] = None
    content: str
    created_at: str
    is_system_message: bool


class RoomDetailSchema(Schema):
    id: str
    name: str
    description: str
    google_meet_link: str
    has_access_code: bool
    is_public: bool
    status: str
    is_active: bool
    max_participants: int
    participant_count: int
    created_by_name: str
    created_at: str
    is_participant: bool = False
    user_role: str = ""


class RoomListSchema(Schema):
    id: str
    name: str
    description: str
    status: str
    is_public: bool
    participant_count: int
    max_participants: int
    created_by_name: str
    has_google_meet: bool
    created_at: str


class ChatMessageSchema(Schema):
    content: str


class ModerateSchema(Schema):
    user_id: str
    action: str  # mute, unmute, kick, promote, demote


# ─── Helpers ───

def user_to_participant_schema(rp: RoomParticipant) -> RoomParticipantSchema:
    return RoomParticipantSchema(
        id=str(rp.id),
        user_id=str(rp.user.id),
        user_name=rp.user.full_name,
        user_email=rp.user.email,
        user_avatar=rp.user.avatar.url if rp.user.avatar else None,
        role=rp.role,
        status=rp.status,
        is_muted=rp.is_muted,
        is_camera_on=rp.is_camera_on,
        joined_at=rp.joined_at.isoformat(),
    )


def message_to_schema(msg: RoomMessage) -> RoomMessageSchema:
    return RoomMessageSchema(
        id=str(msg.id),
        user_id=str(msg.user.id),
        user_name=msg.user.full_name,
        user_avatar=msg.user.avatar.url if msg.user.avatar else None,
        content=msg.content,
        created_at=msg.created_at.isoformat(),
        is_system_message=msg.is_system_message,
    )


# ─── Endpoints ───

@router.get("/rooms", response=List[RoomListSchema])
@login_required
def list_rooms(request: HttpRequest):
    """List all active public rooms + rooms the user is in."""
    public_rooms = MeetingRoom.objects.filter(
        is_active=True, is_public=True
    ).exclude(status=MeetingRoom.Status.ENDED).order_by('-created_at')

    rooms = []
    for room in public_rooms:
        user_rp = room.participants.filter(user=request.user).first()
        rooms.append(RoomListSchema(
            id=str(room.id),
            name=room.name,
            description=room.description[:100],
            status=room.status,
            is_public=room.is_public,
            participant_count=room.participant_count,
            max_participants=room.max_participants,
            created_by_name=room.created_by.full_name,
            has_google_meet=bool(room.google_meet_link),
            created_at=room.created_at.isoformat(),
        ))
    return rooms


@router.post("/rooms/create", response={201: RoomDetailSchema})
@login_required
def create_room(request: HttpRequest, data: RoomCreateSchema):
    """Create a new meeting room (admin/conseiller only)."""
    if request.user.role not in ('admin', 'conseiller'):
        return 403, {"error": "Seuls les admins et conseillers peuvent créer des salles."}

    room = MeetingRoom.objects.create(
        name=data.name,
        description=data.description,
        created_by=request.user,
        google_meet_link=data.google_meet_link,
        access_code=data.access_code,
        is_public=data.is_public,
        max_participants=data.max_participants,
        status=MeetingRoom.Status.LIVE,
        started_at=timezone.now(),
    )

    # Creator becomes host
    RoomParticipant.objects.create(
        room=room,
        user=request.user,
        role=RoomParticipant.Role.HOST,
    )

    return 201, _room_to_detail(room, request.user)


@router.get("/rooms/{room_id}", response=RoomDetailSchema)
@login_required
def get_room(request: HttpRequest, room_id: str):
    """Get room details."""
    room = get_object_or_404(MeetingRoom, id=room_id)
    return _room_to_detail(room, request.user)


@router.post("/rooms/{room_id}/join", response={200: dict})
@login_required
def join_room(request: HttpRequest, room_id: str):
    """Join a meeting room."""
    room = get_object_or_404(MeetingRoom, id=room_id)

    if not room.is_active:
        return 400, {"error": "Cette salle n'est plus active."}

    if room.status == MeetingRoom.Status.ENDED:
        return 400, {"error": "Cette réunion est terminée."}

    # Check if already participant
    existing = room.participants.filter(user=request.user).first()
    if existing:
        if existing.status == 'left':
            existing.status = 'in_room'
            existing.left_at = None
            existing.save()
        return 200, {"message": "Déjà dans la salle", "room_id": str(room.id)}

    # Check max participants
    if room.participants.filter(status='in_room').count() >= room.max_participants:
        return 400, {"error": "Salle pleine."}

    # Determine role
    role = RoomParticipant.Role.PARTICIPANT
    if room.created_by_id == request.user.id:
        role = RoomParticipant.Role.HOST

    RoomParticipant.objects.create(
        room=room,
        user=request.user,
        role=role,
    )

    # Create system message
    RoomMessage.objects.create(
        room=room,
        user=request.user,
        content=f"{request.user.full_name} a rejoint la salle",
        is_system_message=True,
    )

    return 200, {"message": "Rejoint avec succès", "room_id": str(room.id)}


@router.post("/rooms/{room_id}/leave", response={200: dict})
@login_required
def leave_room(request: HttpRequest, room_id: str):
    """Leave a meeting room."""
    rp = get_object_or_404(
        RoomParticipant, room_id=room_id, user=request.user
    )
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

    return 200, {"message": "Salle quittée"}


@router.get("/rooms/{room_id}/participants", response=List[RoomParticipantSchema])
@login_required
def list_participants(request: HttpRequest, room_id: str):
    """List room participants."""
    room = get_object_or_404(MeetingRoom, id=room_id)
    participants = room.participants.filter(status='in_room').order_by('joined_at')
    return [user_to_participant_schema(rp) for rp in participants]


@router.post("/rooms/{room_id}/chat", response={201: RoomMessageSchema})
@login_required
def send_message(request: HttpRequest, room_id: str, data: ChatMessageSchema):
    """Send a chat message in a room."""
    room = get_object_or_404(MeetingRoom, id=room_id)

    # Check user is in room
    rp = room.participants.filter(user=request.user, status='in_room').first()
    if not rp:
        return 403, {"error": "Vous devez être dans la salle pour envoyer des messages."}

    msg = RoomMessage.objects.create(
        room=room,
        user=request.user,
        content=data.content,
    )

    return 201, message_to_schema(msg)


@router.get("/rooms/{room_id}/messages", response=List[RoomMessageSchema])
@login_required
def get_messages(request: HttpRequest, room_id: str):
    """Get chat messages for a room."""
    room = get_object_or_404(MeetingRoom, id=room_id)
    messages = room.messages.order_by('created_at')[:200]
    return [message_to_schema(m) for m in messages]


@router.post("/rooms/{room_id}/moderate", response={200: dict})
@login_required
def moderate_room(request: HttpRequest, room_id: str, data: ModerateSchema):
    """Moderate a room (mute, kick, promote)."""
    room = get_object_or_404(MeetingRoom, id=room_id)

    # Check moderator permissions
    moderator_rp = room.participants.filter(
        user=request.user, status='in_room'
    ).first()
    if not moderator_rp or moderator_rp.role not in ('host', 'moderator'):
        return 403, {"error": "Permissions insuffisantes."}

    target_rp = get_object_or_404(
        RoomParticipant, room=room, user_id=data.user_id
    )

    # Cannot moderate host
    if target_rp.role == 'host' and moderator_rp.role != 'host':
        return 403, {"error": "Impossible de modérer l'hôte."}

    if data.action == 'mute':
        target_rp.is_muted = True
        target_rp.save()
        return 200, {"message": "Utilisateur muet"}

    elif data.action == 'unmute':
        target_rp.is_muted = False
        target_rp.save()
        return 200, {"message": "Utilisateur démueté"}

    elif data.action == 'kick':
        target_rp.status = 'left'
        target_rp.left_at = timezone.now()
        target_rp.save()

        RoomMessage.objects.create(
            room=room,
            user=request.user,
            content=f"{target_rp.user.full_name} a été expulsé par {request.user.full_name}",
            is_system_message=True,
        )
        return 200, {"message": "Utilisateur expulsé"}

    elif data.action == 'promote':
        target_rp.role = RoomParticipant.Role.MODERATOR
        target_rp.save()
        return 200, {"message": "Utilisateur promu modérateur"}

    elif data.action == 'demote':
        target_rp.role = RoomParticipant.Role.PARTICIPANT
        target_rp.save()
        return 200, {"message": "Utilisateur dépromu"}

    return 400, {"error": "Action invalide"}


# ─── Helper ───

def _room_to_detail(room: MeetingRoom, user: User) -> RoomDetailSchema:
    user_rp = room.participants.filter(user=user).first()
    return RoomDetailSchema(
        id=str(room.id),
        name=room.name,
        description=room.description,
        google_meet_link=room.google_meet_link,
        has_access_code=bool(room.access_code),
        is_public=room.is_public,
        status=room.status,
        is_active=room.is_active,
        max_participants=room.max_participants,
        participant_count=room.participant_count,
        created_by_name=room.created_by.full_name,
        created_at=room.created_at.isoformat(),
        is_participant=user_rp is not None,
        user_role=user_rp.role if user_rp else "",
    )
