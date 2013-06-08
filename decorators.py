#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of frestq.
# Copyright (C) 2013  Eduardo Robles Elvira <edulix AT wadobo DOT com>

# election-orchestra is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License.

# election-orchestra  is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with election-orchestra.  If not, see <http://www.gnu.org/licenses/>.

from functools import wraps
from action_handlers import ActionHandlers

def message_action(action, queue, **kwargs):
    """
    Decorator for message actions
    """
    check_static = kwargs.pop('check_static', None)

    if check_static:
        lookup_variables = [check_static]

    # Check if perm is given as string in order not to decorate
    # view function itself which makes debugging harder
    if not isinstance(action, basestring) or not isinstance(queue, basestring):
        raise Exception("action and queue args for message decorator must be strings")

    def decorator(view_func):
        '''
        This is the static wrapper, called when loading the code a wrapped
        funcion
        '''
        # register view_func as an action handler for the given queue
        ActionHandlers.add_action_handler(action, queue, view_func, kwargs)

        def wrapped(*args, **kwargs):
            '''
            This is the runtime wrapper, called when a wrapped function is
            being called.
            '''
            # TODO: Place some callbacks in the scheduler
            return view_func(*args, **kwargs)
        return wraps(view_func)(wrapped)
    return decorator
