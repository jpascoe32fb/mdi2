from django.http import HttpResponseForbidden
from functools import wraps
from .models import Unit

def group_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Retrieve all units associated with the user's groups
        user_groups = request.user.groups.all()
        units = Unit.objects.filter(name__groups__in=user_groups)

        #If no units are found for the user's groups, return forbidden
        if not units.exists():
            return HttpResponseForbidden("You don't have permission to access this page. Contact an admin if you suspect this to be an error.")
        
        # Otherwise, proceed to the view function
        return view_func(request, *args, **kwargs)
    return _wrapped_view