django-reroute
==============

django-reroute is a drop-in replacement for django.conf.urls.defaults that supports HTTP verb dispatch and view wrapping.

Changes in version 1.0.0
------------------------

- [**NEW**] Added support for the csrf_exempt decorator
- [**FIXED**] The incorrect default kwargs are used for verb_url patterns that have the same regex

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
    
Rerouting through wrappers
--------------------------

You can configure a list of view wrappers for a set of url patterns::

    from reroute import reroute_patterns
    
    def params_wrapper(view, request, *args, **kwargs):
        # Provide uniform access of GET, POST or PUT parameters
        # through request.PARAMS
        
        if request.method == 'POST':
            request.PARAMS = dict(request.POST.iteritems())
        else:
            request.PARAMS = dict(request.GET.iteritems())
            
        return view(request, *args, **kwargs)
    
    urlpatterns = reroute_patterns([params_wrapper], 'myapp.views',
        verb_url('GET', '^restful$', 'restful_view'),
        verb_url('PUT', '^restful$', 'another_restful_view')   
    )
    
A wrapper is any callable that takes the arguments: view, request, \*args, \*\*kwargs::
    
    class Wrapper(object):
        def __call__(self, view, request, *args, **kwargs):
            return view(request, *args, **kwargs)
            
    urlpatterns = reroute_patterns([Wrapper()], 'myapp.views',
        verb_url('GET', '^restful$', 'restful_view'),
        verb_url('PUT', '^restful$', 'another_restful_view')   
    )
    
And you can even get fancy and create your own drop-in replacement for patterns::

    from functools import partial
    import logging
    
    def wrapper_one(view, request, *args, **kwargs):
        logging.debug("wrapper one")
        return view(request, *args, **kwargs)
    
    def wrapper_two(view, request, *args, **kwargs):
        logging.debug("wrapper two")
        return view(request, *args, **kwargs)
        
    patterns = partial(reroute_patterns, [wrapper_one, wrapper_two])
    
    urlpatterns = patterns('myapp.views',
        verb_url('GET', '^restful$', 'restful_view'),
        verb_url('PUT', '^restful$', 'another_restful_view')   
    )  

Author
------

django-reroute was written by Mark Sandstrom.
