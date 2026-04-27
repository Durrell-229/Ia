from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SubscriptionPlan, UserSubscription

@login_required
def plan_list_view(request):
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    current_subscription = getattr(request.user, 'subscription', None)
    return render(request, 'subscriptions/plan_list.html', {
        'plans': plans,
        'current_subscription': current_subscription
    })

@login_required
def subscribe_action(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    # Logique de création d'abonnement (Simulation de succès de paiement)
    UserSubscription.objects.update_or_create(
        user=request.user,
        defaults={
            'plan': plan,
            'is_active': True
        }
    )
    
    messages.success(request, f"Félicitations ! Vous êtes maintenant abonné au plan {plan.name}.")
    return redirect('dashboard')
