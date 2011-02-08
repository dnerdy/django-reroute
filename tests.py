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

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from functools import partial
import unittest

from django.conf.urls.defaults import patterns as django_patterns
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import resolve, reverse
from django.http import HttpRequest, HttpResponse

try:
    from django.views.decorators.csrf import csrf_exempt  # django >= 1.2
except ImportError:
    from django.contrib.csrf.middleware import csrf_exempt  # django < 1.2

import reroute
from reroute import patterns, url, include, reroute_patterns
from reroute.verbs import verb_url

class URLConf():
    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns
    
def request_with_method(method, path, urlconf):
    callback, callback_args, callback_kwargs = resolve(path, urlconf)
    request = HttpRequest()
    request.method = method
    response = callback(request, *callback_args, **callback_kwargs)
    return response
    
def content_with_method(method, path, urlconf):
    response = request_with_method(method, path, urlconf)
    return response.content
    
content = partial(content_with_method, 'GET')
    
# Test views

def view_one(request):
    return HttpResponse('ONE')

def view_two(request):
    return HttpResponse('TWO')
    
def view_three(request):
    return HttpResponse('THREE')
    
def kwarg_view(request, key):
    return HttpResponse(key)
    
def generic_view(request):
    return HttpResponse('OK')
        
def method_view(request):
    return HttpResponse(request.method)
    
def wrapper_view(request):
    return HttpResponse('wrapper ' + request.WRAPPER_TEST)

@csrf_exempt
def csrf_exempt_view(request):
    return HttpResponse('OK')
    
class HandlerExistenceTestCase(unittest.TestCase):
    def test(self):
        self.assertTrue(hasattr(reroute, 'handler404'))
        self.assertTrue(hasattr(reroute, 'handler500'))
        
class DjangoCompatibilityTestCase(unittest.TestCase):
    def setUp(self):
        included_urlpatterns = patterns('tests',
            url('^included_view$', 'generic_view')
        )
        
        urlpatterns = patterns('tests',
            ('^tuple$', 'generic_view'),
            url('^url$', 'generic_view'),
            url('^non_string_view$', generic_view),
            url('^view_with_name$', 'generic_view', name='view_with_name'),
            url('^kwargs$', 'kwarg_view', kwargs={'key': 'value'}),
            url('^url_reverse$', 'view_one'),
            url('^non_string_view_reverse$', view_two),
            url('^view_with_name_reverse$', 'view_three', name='view_with_name_reverse'),
            url('^include/', include(included_urlpatterns)),
            url('^csrf_exempt_view$', csrf_exempt_view),
        )
        
        urlpatterns += patterns('',
            url('^prefix' , 'generic_view', prefix='tests'),
        )
        
        self.urlconf = URLConf(urlpatterns)
    
    def testTuple(self):
        self.assertEqual(content('/tuple', self.urlconf), 'OK')
        
    def testURL(self):
        self.assertEqual(content('/url', self.urlconf), 'OK')
        
    def testNonStringView(self):
        self.assertEqual(content('/non_string_view', self.urlconf), 'OK')
        
    def testViewWithName(self):
        self.assertEqual(content('/view_with_name', self.urlconf), 'OK')
        
    def testKwargs(self):
        self.assertEqual(content('/kwargs', self.urlconf), 'value')
        
    def testPrefix(self):
        self.assertEqual(content('/prefix', self.urlconf), 'OK')
        
    def testUrlReverse(self):
        self.assertEqual(reverse('tests.view_one', self.urlconf), '/url_reverse')
    
    def testNonStringViewReverse(self):
        self.assertEqual(reverse('tests.view_two', self.urlconf), '/non_string_view_reverse')
        
    def testNonStringViewReverse(self):
        self.assertEqual(reverse('view_with_name_reverse', self.urlconf), '/view_with_name_reverse')
        
    def testIncludedView(self):
        self.assertEqual(content('/include/included_view', self.urlconf), 'OK')

    def testCsrfExemptView(self):
        callback, callback_args, callback_kwargs = resolve('/csrf_exempt_view', self.urlconf)
        self.assertTrue(hasattr(callback, 'csrf_exempt'))
        self.assertTrue(callback.csrf_exempt, True)
        
# Wrappers

def wrapper1(view, request, *args, **kwargs):
    request.WRAPPER_TEST = '1'
    return view(request, *args, **kwargs)
    
def wrapper2(view, request, *args, **kwargs):
    request.WRAPPER_TEST += ' 2'
    return view(request, *args, **kwargs)

class ReroutePatternsTestCase(unittest.TestCase):
    def testReroutePatterns(self): 
        urlconf = URLConf(reroute_patterns([wrapper1], 'tests',
            url('^test$', 'wrapper_view')
        ))
           
        self.assertEqual(content('/test', urlconf), 'wrapper 1')
        
    def testWrapperOrder(self):       
        urlconf = URLConf(reroute_patterns([wrapper1, wrapper2], 'tests',
            url('^test$', 'wrapper_view')
        ))
        
        self.assertEqual(content('/test', urlconf), 'wrapper 1 2')
        
    def testURLWithDjangoPatternsShouldFail(self):
        urlconf = URLConf(django_patterns('tests',
            url('^test$', 'wrapper_view')
        ))
        
        self.assertRaises(ImproperlyConfigured, content, '/test', urlconf)
        
class VerbURLTestCase(unittest.TestCase):
    def setUp(self):
        included_urlpatterns = patterns('tests',
            verb_url('GET',     '^test$', 'method_view'),
            verb_url('POST',    '^test$', 'method_view')
        )
        
        self.urlconf = URLConf(patterns('tests',
            verb_url('GET',     '^test$', 'method_view'),
            verb_url('POST',    '^test$', 'method_view'),
            verb_url('PUT',     '^test$', 'method_view'),
            verb_url('DELETE',  '^test$', 'method_view'),
            verb_url('GET',     '^kwarg', 'kwarg_view', {'key': 'get view'}),
            verb_url('POST',    '^kwarg', 'kwarg_view', {'key': 'post view'}),
            url('^include/', include(included_urlpatterns))
        ))
                
    def testGet(self):
        self.assertEqual(content_with_method('GET', '/test', self.urlconf), 'GET')
        
    def testPost(self):
        self.assertEqual(content_with_method('POST', '/test', self.urlconf), 'POST')
        
    def testPut(self):
        self.assertEqual(content_with_method('PUT', '/test', self.urlconf), 'PUT')
        
    def testDelete(self):
        self.assertEqual(content_with_method('DELETE', '/test', self.urlconf), 'DELETE')
        
    def testKwargs(self):
        self.assertEqual(content_with_method('GET', '/kwarg', self.urlconf), 'get view')
        self.assertEqual(content_with_method('POST', '/kwarg', self.urlconf), 'post view')
        
    def testIncludeGet(self):
        self.assertEqual(content_with_method('GET', '/include/test', self.urlconf), 'GET')
        
    def testIncludePost(self):
        self.assertEqual(content_with_method('POST', '/include/test', self.urlconf), 'POST')
        
    def testMethodNotAllowed(self):
        response = request_with_method('PUT', '/include/test', self.urlconf)
        self.assertEqual(response.status_code, 405)

if __name__ == '__main__':
    unittest.main()
