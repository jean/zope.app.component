##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Support for delegation among service managers

$Id: nextservice.py,v 1.3 2003/03/11 21:08:40 jim Exp $
"""

from zope.component.exceptions import ComponentLookupError
from zope.component.service import serviceManager
from zope.proxy.context import getWrapperContainer
from zope.proxy.introspection import removeAllProxies
from zope.app.interfaces.services.service import IServiceManagerContainer
from zope.app.component.hooks import getServiceManager_hook

# placeful service manager convenience tools

def queryNextServiceManager(context, default=None):
    try:
        return getNextServiceManager(context)
    except ComponentLookupError:
        return default

def getNextService(context, name):
    service = queryNextService(context, name)
    if service is None:
        raise ComponentLookupError('service', name)
    return service

def queryNextService(context, name, default=None):
    try:
        sm = getNextServiceManager(context)
    except ComponentLookupError:
        return default
    return sm.queryService(name, default)

def getNextServiceManager(context):
    """if the context is a service manager or a placeful service, tries
    to return the next highest service manager"""

    # IMPORTANT
    #
    # This is not allowed to use any services to get it's job done!

    # get this service manager
    sm = getServiceManager_hook(context)
    if sm is serviceManager:
        raise ComponentLookupError('Services')

    # get the service manager container, which ought to be the context
    # contaioner.
    container = getWrapperContainer(sm)

    # But we're *really* paranoid, so we'll double check.
    while ((container is not None) and not
           IServiceManagerContainer.isImplementedBy(
                      removeAllProxies(container))
           ):
        container = getWrapperContainer(container) # we should be

    # Now we need to step up so we can look for a service manager above.
    context = getWrapperContainer(container)

    # But we have to make sure we haven't got the same object..
    while (context is not None) and (context == container):
        context = getWrapperContainer(context)

    return getServiceManager_hook(context, local=True)
