##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Hooks for getting and setting a site in the thread global namespace.

$Id$
"""
__docformat__ = 'restructuredtext'

import zope.component
from zope.component import getService
from zope.component.interfaces import IServiceService
from zope.app.site.interfaces import ISite
from zope.component.service import serviceManager
from zope.component.exceptions import ComponentLookupError
from zope.security.proxy import removeSecurityProxy
from zope.app.traversing.interfaces import IContainmentRoot
from zope.app.location.interfaces import ILocation
from zope.app.location import locate
from zope.interface import Interface
from zope.component.servicenames import Adapters
import warnings
import zope.thread

def getServices_hook(context=None):

    if context is None:
        return siteinfo.services

    # Deprecated support for a context that isn't adaptable to
    # IServiceService.  Return the default service manager.
    try:


        # We remove the security proxy because there's no way for
        # untrusted code to get at it without it being proxied again.

        # We should really look look at this again though, especially
        # once site managers do less.  There's probably no good reason why
        # they can't be proxied.  Well, except maybe for performance.


        return removeSecurityProxy(IServiceService(context,
                                                   serviceManager))
    except ComponentLookupError:
        return serviceManager
    
def queryView(object, name, request, default=None,
              providing=Interface, context=None):
    adapters = getService(Adapters, context)
    view = adapters.queryMultiAdapter((object, request), providing,
                                      name, default)
    if ILocation.providedBy(view):
        locate(view, object, name)

    return view


def setHooks():
    # Hook up a new implementation of looking up views.
    zope.component.getServices.sethook(getServices_hook)
    zope.component.queryView.sethook(queryView)

def resetHooks():
    # Reset hookable functions to original implementation.
    zope.component.getServices.reset()
    zope.component.queryView.reset()
    