from functools import partial

def rollup(function, wrappers):            
    for wrapper in reversed(wrappers):
        function = partial(wrapper, function)
    return function