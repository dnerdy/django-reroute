# Copyright (c) 2010 Mark Sandstrom
# 
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

from functools import partial

from django.http import HttpResponse

from base import RerouteRegexURLPattern, url_with_pattern_class
from utils import rollup

__all__ = ['verb_url', 'request_method']

def request_method(request):
    '''Returns the effective HTTP method of a request. To support the entire range of HTTP methods
    from HTML forms (which only support GET and POST), an HTTP method may be emulated by
    setting a POST parameter named "_method" to the name of the HTTP method to be emulated.
    
    Example HTML:
        <!-- Submits a form using the PUT method -->
        
        <form>
            <input type="text" name="name" value="value" />
            <button type="submit" name="_method" value="put">Update</button>
        </form>
    
    Args:
        request: an HttpRequest
    
    Returns:
        An upper-case string naming the HTTP method (like django.http.HttpRequest.method)
    '''
    
    # For security reasons POST is the only method that supports HTTP method emulation.
    # For example, if POST requires csrf_token, we don't want POST methods to be called via
    # GET (thereby bypassing CSRF protection). POST has the most limited semantics, and it
    # is therefore safe to emulate HTTP methods with less-limited semantics. See
    # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html ("Safe and Idempotent Methods")
    # for details.

    if request.method == 'POST' and '_method' in request.POST:
        method = request.POST['_method'].upper()
    else:
        method = request.method
        
    return method        

class VerbRegexURLPattern(RerouteRegexURLPattern):
    patterns_index = {}
    
    def __init__(self, method, *args, **kwargs):
        super(VerbRegexURLPattern, self).__init__(*args, **kwargs)
        self.method = method.upper() 
    
    def reroute_callback(self, request, *args, **kwargs):
        record = self.method_callbacks.get(request_method(request))
        
        if not record:
            return HttpResponse(status=405)
            
        callback = record['callback']
        kwargs.update(record['default_args'])
           
        callback = rollup(callback, self.wrappers)
        return callback(request, *args, **kwargs)
    
    def reroute_config(self, wrappers, patterns_id):
        super(VerbRegexURLPattern, self).reroute_config(wrappers, patterns_id)
        
        # Let patterns with identical regexes that are defined within the same call
        # to reroute_patterns be called a pattern group. Each pattern in a pattern group
        # has a reference to shared dict (shared by the group) which maps http methods
        # to pattern callbacks. Only one pattern from a group will ever be resolved (remember
        # that the patterns all have identical regexes), so this shared dict is used to route
        # to the correct callback for a given http method. All this hoopla is necessary since
        # patterns are resolved outside the context of a request.
        
        method_callbacks_by_regex = self.patterns_index.setdefault(patterns_id, {})
        method_callbacks = method_callbacks_by_regex.setdefault(self.regex.pattern, {})
        
        if self.method not in method_callbacks:
            method_callbacks[self.method] = {'callback': self.callback, 'default_args': self.default_args}
            self.default_args = {}
        
        # Borg-like
        self.method_callbacks = method_callbacks       

def verb_url(method, regex, view, kwargs=None, name=None, prefix=''):
    pattern_class = partial(VerbRegexURLPattern, method)
    return url_with_pattern_class(pattern_class, regex, view, kwargs, name, prefix)
