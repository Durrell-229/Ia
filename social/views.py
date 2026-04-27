from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Forum, Topic, Post, StudyGroup


@login_required
def forum_list(request):
    forums = Forum.objects.filter(is_active=True)
    return render(request, 'social/forum_list.html', {'forums': forums})


@login_required
def forum_detail(request, forum_id):
    forum = get_object_or_404(Forum, id=forum_id)
    topics = forum.topics.filter(is_active=True).order_by('-is_pinned', '-updated_at')
    return render(request, 'social/forum_detail.html', {'forum': forum, 'topics': topics})


@login_required
def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, is_active=True)
    topic.views += 1
    topic.save()
    posts = topic.posts.filter(is_active=True)
    return render(request, 'social/topic_detail.html', {'topic': topic, 'posts': posts})


@login_required
def group_list(request):
    groups = StudyGroup.objects.all()
    return render(request, 'social/group_list.html', {'groups': groups})


@login_required
def group_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        max_members = int(request.POST.get('max_members', 20))
        is_private = request.POST.get('is_private') == 'on'
        
        group = StudyGroup.objects.create(
            name=name,
            description=description,
            creator=request.user,
            max_members=max_members,
            is_private=is_private,
        )
        group.members.add(request.user)
        messages.success(request, "Groupe créé avec succès!")
        return redirect('social:group_detail', group_id=group.id)
    
    return render(request, 'social/group_create.html')


@login_required
def group_detail(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    return render(request, 'social/group_detail.html', {'group': group})
