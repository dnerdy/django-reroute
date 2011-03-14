django-reroute
==============

django-reroute is a set of tools for simplifying your views, especially when you're implementing a REST API. django-reroute provides a drop-in replacement for django.conf.urls.defaults that supports HTTP verb dispatch so that your views don't become cluttered with ``if request.method == 'GET'`` statements. It also provides a nifty set of view decorators for simplifying common tasks like rendering a template using a RequestContext and redirecting to a particular view after request processing.

Download
--------

Github: http://github.com/dnerdy/django-reroute

easy_install::
    
    easy_install django-reroute
    
Source::
    
    # Download the source and run
    python setup.py install
    

Adding django-reroute to your project
-------------------------------------

django-reroute is a drop-in replacement for django.conf.urls.defaults::

    # Replace
    from django.conf.urls.defaults *
    
    # with   
    from reroute import *
    
Although it's better to be explicit::
    
    # Replace
    from django.conf.urls.defaults import handler404, handler500, patterns, url, include
    
    # with   
    from reroute import handler404, handler500, patterns, url, include  
    
HTTP verb dispatching
---------------------

verb_url patterns can match HTTP verbs in addition to regexes::

    from reroute.verbs import verb_url
    
    urlpatterns = patterns('myapp.views',
        url('^regular$', 'regular_old_view'),
        verb_url('GET', '^restful$', 'restful_view')
    )
    
verb_url pattern regexes can be overloaded, enabling routing solely based on HTTP verb::
    
    urlpatterns = patterns('myapp.views',
        verb_url('GET', '^restful$', 'restful_view'),
        verb_url('PUT', '^restful$', 'another_restful_view')   
    )
    
Restful resource example::

    paychecks = patterns('myapp.views.employees.paychecks',
        verb_url('GET',     '^paychecks$', 'index_paychecks'),
        verb_url('POST',    '^paychecks$', 'add_paycheck'),
    )
    
    urlpatterns = patterns('myapp.views.employees',
        verb_url('GET',     '^employees$', 'index_employees'),
        verb_url('POST',    '^employees$', 'add_employee'),
        
        verb_url('GET',     '^employees/(?P<employee_id>\d+)$', 'show_employee')
        verb_url('PUT',     '^employees/(?P<employee_id>\d+)$', 'update_employee')
        verb_url('DELETE',  '^employees/(?P<employee_id>\d+)$', 'delete_employee'),
        
        url('^employees/(?P<employee_id>\d+)/', include(paychecks)),
    )

Rendering templates
-------------------

Return a dictionary of values to add to the template context::

    @render('template.html')
    def view(request):
        return {'title': 'This is the page title'}

        # The template is rendered using a RequestContext instance

If you need, return an HttpResponse and it will be used::

    @render('template.html')
    def view(request):
        if special_case:
            return HttpResponse('This response will be used instead of rendering template.html')
        else:
            return {'title': 'This is the page title'}

Redirecting
-----------

Return a dictionary of values to use as reverse kwargs::

    @redirect('other_view_name')
    def view(request):
        return {'view_kwarg': 42}

        # This is equivalent to:
        # return HttpResponseRedirect(reverse('other_view_name', kwargs={'view_kwarg': 42}))

    @render('other_tempate.html')
    def other_view(request, view_kwarg):
        return {
            'title': 'This is the other view page title',
            'message': 'Meaning of life? {0}'.format(view_kwarg)
        }

Again, if you return an HttpResponse it will be used::

    @redirect('other_view_name')
    def view(request):
        if special_case:
            return HttpResponse('This response will be used instead of redirecting')
        else:
            return {'view_kwarg': 42}

Internals: wrappers
-------------------

Wrappers are like middleware that are applied to a selective set of urls. A wrapper is any callable that takes the arguments: ``view``, ``request``, ``*args``, ``**kwargs``::

    import logging
    from reroute import reroute_patterns

    def wrapper_one(view, request, *args, **kwargs):
        logging.debug("wrapper one")
        return view(request, *args, **kwargs)

    def wrapper_two(view, request, *args, **kwargs):
        logging.debug("wrapper two")
        return view(request, *args, **kwargs)

    urlpatterns = reroute_patterns([wrapper_one, wrapper_two], 'myapp.views',
        verb_url('GET', '^restful$', 'restful_view'),
        verb_url('PUT', '^restful$', 'another_restful_view')
    )

You can even get fancy and create your own drop-in replacement for patterns::

    from functools import partial

    patterns = partial(reroute_patterns, [wrapper_one, wrapper_two])

    urlpatterns = patterns('myapp.views',
        verb_url('GET', '^restful$', 'restful_view'),
        verb_url('PUT', '^restful$', 'another_restful_view')
    )

Changes in version 1.1.0
------------------------

- [**NEW**] Added ``render`` and ``redirect`` decorators to ``reroute.decorators`` for simplifying common views tasks (namely rendering a template or redirecting to another view)
- [**FIXED**] verb_url patterns are sporadically grouped incorrectly resulting in 405 responses. Python maintains a regex cache that is cleared after 100 entries, and verb_url patterns are group by regex object as opposed to the regex pattern. When the cache is cleared, regex objects with the same regex pattern are no longer equal.

Changes in version 1.0.1
------------------------

- [**FIXED**] The PyPI package doesn't work with pip

Changes in version 1.0.0
------------------------

- [**NEW**] Added support for the csrf_exempt decorator
- [**FIXED**] The incorrect default kwargs are used for verb_url patterns that have the same regex


Author
------

django-reroute was written by Mark Sandstrom.
