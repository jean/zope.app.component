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
"""Generic Components ZCML Handlers

$Id$
"""
__docformat__ = 'restructuredtext'
from persistent.interfaces import IPersistent

from zope.component.interfaces import IDefaultViewName, IFactory
from zope.component.service import UndefinedService
from zope.configuration.exceptions import ConfigurationError
from zope.interface import Interface, classImplements
from zope.interface.interfaces import IInterface

from zope.security.checker import InterfaceChecker, CheckerPublic
from zope.security.checker import Checker, NamesChecker
from zope.security.proxy import Proxy, ProxyFactory

from zope.app import zapi
from zope.app.annotation.interfaces import IAttributeAnnotatable
from zope.app.component.contentdirective import ContentDirective
from zope.app.component.interface import queryInterface
from zope.app.component.interfaces import ILocalUtility
from zope.app.location.interfaces import ILocation
from zope.app.security.adapter import TrustedAdapterFactory


PublicPermission = 'zope.Public'

# I prefer the indirection (using getService and getServices vs.
# directly importing the various services)  not only because it makes
# unit tests easier, but also because it reinforces that the services
# should always be obtained through the
# IPlacefulComponentArchitecture interface methods.

# But these services aren't placeful! And we need to get at things that
# normal service clients don't need!   Jim


def handler(serviceName, methodName, *args, **kwargs):
    method=getattr(zapi.getGlobalService(serviceName), methodName)
    method(*args, **kwargs)

# We can't use the handler for serviceType, because serviceType needs
# the interface service.
from zope.app.component.interface import provideInterface

def managerHandler(methodName, *args, **kwargs):
    method=getattr(zapi.getGlobalServices(), methodName)
    method(*args, **kwargs)

def interface(_context, interface, type=None):
    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = ('', interface, type)
        )


def proxify(ob, checker):
    """Try to get the object proxied with the `checker`, but not too soon

    We really don't want to proxy the object unless we need to.
    """

    try:
        ob.__Security_checker__ = checker
    except AttributeError:
        ob = Proxy(ob, checker)

    return ob

def subscriber(_context, factory, for_, provides=None, permission=None,
               trusted=False):
    factory = [factory]

    if permission is not None:
        if permission == PublicPermission:
            permission = CheckerPublic
        checker = InterfaceChecker(provides, permission)
        factory.append(lambda c: proxify(c, checker))

    for_ = tuple(for_)

    # Generate a single factory from multiple factories:
    factories = factory
    if len(factories) == 1:
        factory = factories[0]
    elif len(factories) < 1:
        raise ValueError("No factory specified")
    elif len(factories) > 1 and len(for_) != 1:
        raise ValueError("Can't use multiple factories and multiple for")
    else:
        def factory(ob):
            for f in factories:
                ob = f(ob)
            return ob

    if trusted:
        factory = TrustedAdapterFactory(factory)

    _context.action(
        discriminator = None,
        callable = handler,
        args = (zapi.servicenames.Adapters, 'subscribe',
                for_, provides, factory),
        )

    if provides is not None:
        _context.action(
            discriminator = None,
            callable = provideInterface,
            args = ('', provides)
            )
    
    # For each interface, state that the adapter provides that interface.
    for iface in for_:
        if iface is not None:
            _context.action(
                discriminator = None,
                callable = provideInterface,
                args = ('', iface)
                )

def adapter(_context, factory, provides, for_, permission=None, name='',
            trusted=False):
    if permission is not None:
        if permission == PublicPermission:
            permission = CheckerPublic
        checker = InterfaceChecker(provides, permission)
        factory.append(lambda c: proxify(c, checker))

    for_ = tuple(for_)

    # Generate a single factory from multiple factories:
    factories = factory
    if len(factories) == 1:
        factory = factories[0]
    elif len(factories) < 1:
        raise ValueError("No factory specified")
    elif len(factories) > 1 and len(for_) != 1:
        raise ValueError("Can't use multiple factories and multiple for")
    else:
        def factory(ob):
            for f in factories:
                ob = f(ob)
            return ob
        # Store the original factory for documentation
        factory.factory = factories[0]

    if trusted:
        factory = TrustedAdapterFactory(factory)

    _context.action(
        discriminator = ('adapter', for_, provides, name),
        callable = handler,
        args = (zapi.servicenames.Adapters, 'register',
                for_, provides, name, factory, _context.info),
        )
    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = ('', provides)
               )
    if for_:
        for iface in for_:
            if iface is not None:
                _context.action(
                    discriminator = None,
                    callable = provideInterface,
                    args = ('', iface)
                    )

def utility(_context, provides, component=None, factory=None,
            permission=None, name=''):
    if factory:
        if component:
            raise TypeError("Can't specify factory and component.")
        component = factory()

    if permission is not None:
        if permission == PublicPermission:
            permission = CheckerPublic
        checker = InterfaceChecker(provides, permission)

        component = proxify(component, checker)

    _context.action(
        discriminator = ('utility', provides, name),
        callable = handler,
        args = ('Utilities', 'provideUtility',
                provides, component, name),
        )
    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = (provides.__module__ + '.' + provides.getName(), provides)
               )

def factory(_context, component, id, title=None, description=None):
    if title is not None:
        component.title = title
        
    if description is not None:
        component.description = description

    utility(_context, IFactory, component,
            permission=PublicPermission, name=id)


def _checker(_context, permission, allowed_interface, allowed_attributes):
    if (not allowed_attributes) and (not allowed_interface):
        allowed_attributes = ["__call__"]

    if permission == PublicPermission:
        permission = CheckerPublic

    require={}
    if allowed_attributes:
        for name in allowed_attributes:
            require[name] = permission
    if allowed_interface:
        for i in allowed_interface:
            for name in i.names(all=True):
                require[name] = permission

    checker = Checker(require)
    return checker

def resource(_context, factory, type, name, layer=None,
             permission=None,
             allowed_interface=None, allowed_attributes=None,
             provides=Interface):

    if ((allowed_attributes or allowed_interface)
        and (not permission)):
        raise ConfigurationError(
            "Must use name attribute with allowed_interface or "
            "allowed_attributes"
            )

    if permission:

        checker = _checker(_context, permission,
                           allowed_interface, allowed_attributes)

        def proxyResource(request, factory=factory, checker=checker):
            return proxify(factory(request), checker)

        factory = proxyResource

    if layer is None:
        layer = zapi.queryAdapter(type, IInterface, 'defaultLayer')
    if layer is None:
        layer = type

    _context.action(
        discriminator = ('resource', name, layer, provides),
        callable = handler,
        args = (zapi.servicenames.Adapters, 'register',
                (layer,), provides, name, factory, _context.info),
        )
    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = (type.__module__ + '.' + type.__name__, type)
               )
    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = (provides.__module__ + '.' + provides.__name__, type)
               )

def view(_context, factory, type, name, for_, layer=None,
         permission=None, allowed_interface=None, allowed_attributes=None,
         provides=Interface):

    if ((allowed_attributes or allowed_interface)
        and (not permission)):
        raise ConfigurationError(
            "Must use name attribute with allowed_interface or "
            "allowed_attributes"
            )

    if not factory:
        raise ConfigurationError("No view factory specified.")

    if permission:

        checker = _checker(_context, permission,
                           allowed_interface, allowed_attributes)

        class ProxyView(object):
            """Class to create simple proxy views."""

            def __init__(self, factory, checker):
                self.factory = factory
                self.checker = checker

            def __call__(self, *objects):
                return proxify(self.factory(*objects), self.checker)

        factory[-1] = ProxyView(factory[-1], checker)


    if not for_:
        raise ValueError("No for interfaces specified");
    for_ = tuple(for_)

    # Generate a single factory from multiple factories:
    factories = factory
    if len(factories) == 1:
        factory = factories[0]
    elif len(factories) < 1:
        raise ValueError("No factory specified")
    elif len(factories) > 1 and len(for_) > 1:
        raise ValueError("Can't use multiple factories and multiple for")
    else:
        def factory(ob, request):
            for f in factories[:-1]:
                ob = f(ob)
            return factories[-1](ob, request)

    # if layer not specified, use default layer for type
    if layer is None:
        layer = zapi.queryAdapter(type, IInterface, 'defaultLayer')
    if layer is not None:
        for_ = for_ + (layer,)
    else:
        for_ = for_ + (type,)

    _context.action(
        discriminator = ('view', for_, name, provides),
        callable = handler,
        args = (zapi.servicenames.Adapters, 'register',
                for_, provides, name, factory, _context.info),
        )
    if type is not None:
        _context.action(
            discriminator = None,
            callable = provideInterface,
            args = ('', type)
            )
        
    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = ('', provides)
        )

    if for_ is not None:
        for iface in for_:
            if iface is not None:
                _context.action(
                    discriminator = None,
                    callable = provideInterface,
                    args = ('', iface)
                    )

def defaultView(_context, type, name, for_):

    _context.action(
        discriminator = ('defaultViewName', for_, type, name),
        callable = handler,
        args = (zapi.servicenames.Adapters, 'register',
                (for_, type), IDefaultViewName, '', name, _context.info)
        )
    
    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = ('', type)
        )

    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = ('', for_)
        )

def defaultLayer(_context, type, layer):
    _context.action(
        discriminator=('defaultLayer', type, layer),
        callable=handler,
        args = (zapi.servicenames.Adapters, 'register',
               (type,), IInterface, 'defaultLayer',
               lambda request: layer, _context.info)
        )


class LocalUtilityDirective(ContentDirective):
    r"""localUtility directive handler.

    Examples:

      >>> from zope.interface import implements
      >>> class LU1(object):
      ...     pass

      >>> class LU2(LU1):
      ...     implements(ILocation)

      >>> class LU3(LU1):
      ...     __parent__ = None

      >>> class LU4(LU2):
      ...     implements(IPersistent)

      >>> dir = LocalUtilityDirective(None, LU4)
      >>> IAttributeAnnotatable.implementedBy(LU4)
      True
      >>> ILocalUtility.implementedBy(LU4)
      True

      >>> LocalUtilityDirective(None, LU3)
      Traceback (most recent call last):
      ...
      ConfigurationError: Class `LU3` does not implement `IPersistent`.

      >>> LocalUtilityDirective(None, LU2)
      Traceback (most recent call last):
      ...
      ConfigurationError: Class `LU2` does not implement `IPersistent`.

      >>> LocalUtilityDirective(None, LU1)
      Traceback (most recent call last):
      ...
      ConfigurationError: Class `LU1` does not implement `ILocation`.
    """

    def __init__(self, _context, class_):
        if not ILocation.implementedBy(class_) and \
               not hasattr(class_, '__parent__'):
            raise ConfigurationError, \
                  'Class `%s` does not implement `ILocation`.' %class_.__name__

        if not IPersistent.implementedBy(class_):
            raise ConfigurationError, \
                 'Class `%s` does not implement `IPersistent`.' %class_.__name__

        classImplements(class_, IAttributeAnnotatable)
        classImplements(class_, ILocalUtility)

        super(LocalUtilityDirective, self).__init__(_context, class_)
