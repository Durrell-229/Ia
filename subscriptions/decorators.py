from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def subscription_required(level='PRO'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Vérifier si l'utilisateur a un abonnement actif du niveau requis
            sub = getattr(request.user, 'subscription', None)
            
            if not sub or sub.is_expired or sub.plan.level == 'FREE' and level != 'FREE':
                messages.warning(request, f"Cette fonctionnalité nécessite un abonnement {level}. Veuillez mettre à jour votre plan.")
                return redirect('welcome') # Ou une page de tarification
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
