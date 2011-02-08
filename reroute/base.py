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

from django.conf.urls.defaults import patterns as django_patterns
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import RegexURLPattern, RegexURLResolver

from utils import rollup

class RerouteRegexURLPattern(RegexURLPattern):
    _configured = False
    
    def reroute_config(self, wrappers, patterns_id):
        self.wrappers = wrappers
        self._configured = True
        
    def reroute_callback(self, request, *args, **kwargs):
        callback = rollup(self.callback, self.wrappers)
        return callback(request, *args, **kwargs)
                  
    def resolve(self, path):
        # Lifted from django.core.urlresolvers.RegexURLPattern.resolve
        if not self._configured:
            raise ImproperlyConfigured('RerouteRegexURLPattern patterns must be used within reroute.patterns or reroute_patterns (for pattern %r)' % self.regex.pattern)
        
        match = self.regex.search(path)
        if match:
            # If there are any named groups, use those as kwargs, ignoring
            # non-named groups. Otherwise, pass all non-named arguments as
            # positional arguments.
            kwargs = match.groupdict()
            if kwargs:
                args = ()
            else:
                args = match.groups()
            # In both cases, pass any extra_kwargs as **kwargs.
            kwargs.update(self.default_args)

            # We unfortunately need another wrapper here since arbitrary attributes can't be set
            # on an instancemethod
            callback = lambda request, *args, **kwargs: self.reroute_callback(request, *args, **kwargs)
            
            if hasattr(self.callback, 'csrf_exempt'):
                callback.csrf_exempt = self.callback.csrf_exempt

            return callback, args, kwargs

def reroute_patterns(wrappers, prefix, *args):
    # TODO(dnerdy) Require that all patterns be instances of RerouteRegexURLPattern
    # TODO(dnerdy) Remove additional patterns with identical regexes, if present (occurs
    #   when using verb_url)
    
    patterns_id = object()
    pattern_list = django_patterns(prefix, *args)
    
    for pattern in pattern_list:
        if isinstance(pattern, RerouteRegexURLPattern):            
            pattern.reroute_config(wrappers, patterns_id)
        
    return pattern_list
    
patterns = partial(reroute_patterns, [])

def url_with_pattern_class(pattern_class, regex, view, kwargs=None, name=None, prefix=''):
    # Lifted from django.conf.urls.defaults
    
    if isinstance(view, (list,tuple)):
        # For include(...) processing.
        urlconf_module, app_name, namespace = view
        return RegexURLResolver(regex, urlconf_module, kwargs, app_name=app_name, namespace=namespace)
    else:
        if isinstance(view, basestring):
            if not view:
                raise ImproperlyConfigured('Empty URL pattern view name not permitted (for pattern %r)' % regex)
            if prefix:
                view = prefix + '.' + view
        return pattern_class(regex, view, kwargs, name)
        
url = partial(url_with_pattern_class, RerouteRegexURLPattern)
