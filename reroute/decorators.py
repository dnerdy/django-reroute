# Copyright (c) 2011 Mark Sandstrom

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.

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
