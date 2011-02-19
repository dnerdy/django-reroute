from functools import wraps

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

CONFLICTING_CONTEXTS = 'The view {module}.{view} and @render define conflicting contexts. These keys collide: {keys}'

def render(template, **extra_context):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            response = func(request, *args, **kwargs)
            if isinstance(response, dict):
                common_keys = set(response) & set(extra_context)
                if common_keys:
                    raise ValueError(CONFLICTING_CONTEXTS.format(
                        module = func.__module__,
                        view = func.__name__,
                        keys = ', '.join(common_keys)
                    ))
                response.update(extra_context)
                response = render_to_response(template, response, context_instance=RequestContext(request))
                return response
            else:
                return response
        return wrapper
    return decorator

def redirect(reverse_viewname):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            if isinstance(response, dict):
                return HttpResponseRedirect(reverse(reverse_viewname, kwargs=response))
            else:
                return response
        return wrapper
    return decorator
