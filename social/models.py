import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Forum(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nom du forum', max_length=255)
    description = models.TextField('Description', blank=True)
    icon = models.CharField('Icon (FontAwesome)', max_length=50, default='fa-comments')
    color = models.CharField('Couleur', max_length=20, default='#4F46E5')
    is_active = models.BooleanField('Actif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Forum'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def topic_count(self):
        return self.topics.filter(is_active=True).count()

    @property
    def post_count(self):
        return sum(t.post_count for t in self.topics.filter(is_active=True))


class Topic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField('Titre', max_length=500)
    content = models.TextField('Contenu')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topics')
    is_pinned = models.BooleanField('Épinglé', default=False)
    is_active = models.BooleanField('Actif', default=True)
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sujet'
        ordering = ['-is_pinned', '-updated_at']

    def __str__(self):
        return self.title

    @property
    def post_count(self):
        return self.posts.filter(is_active=True).count()

    @property
    def last_post(self):
        return self.posts.filter(is_active=True).order_by('-created_at').first()


class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField('Message')
    is_active = models.BooleanField('Actif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Message'
        ordering = ['created_at']

    def __str__(self):
        return f"Post by {self.author.full_name} in {self.topic.title}"


class StudyGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nom du groupe', max_length=255)
    description = models.TextField('Description', blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='study_groups')
    max_members = models.IntegerField(default=20)
    is_private = models.BooleanField('Privé', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Groupe d\'étude'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()


class Like(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.CharField('Type', max_length=20)  # 'post', 'topic'
    content_id = models.UUIDField('ID contenu')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['content_type', 'content_id', 'user']
        verbose_name = 'Like'

    def __str__(self):
        return f"Like by {self.user.full_name}"
