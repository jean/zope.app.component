##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
""" Register class directive.

$Id: contentdirective.py,v 1.16 2004/03/08 12:05:54 srichter Exp $
"""
from types import ModuleType
from zope.interface import classImplements
from zope.component.factory import FactoryInfo
from zope.app.services.servicenames import Factories
from zope.configuration.exceptions import ConfigurationError
from zope.app.component.classfactory import ClassFactory
from zope.app.security.protectclass \
    import protectLikeUnto, protectName, protectSetAttribute
from zope.app.component.interface import provideInterface
from zope.app import zapi
from zope.security.checker import CheckerPublic
from zope.app.security.permission import checkPermission 

from zope.schema.interfaces import IField

PublicPermission = 'zope.Public'

def dottedName(klass):
    if klass is None:
        return 'None'
    return klass.__module__ + '.' + klass.__name__

class ProtectionDeclarationException(Exception):
    """Security-protection-specific exceptions."""
    pass

def handler(serviceName, methodName, *args, **kwargs):
    method=getattr(zapi.getService(None, serviceName), methodName)
    method(*args, **kwargs)

def assertPermission(permission=None, *args, **kw):
    """Check if permission is defined"""
    if permission is not None:
        checkPermission(None, permission)

class ContentDirective:

    def __init__(self, _context, class_):
        self.__id = dottedName(class_)
        self.__class = class_
        if isinstance(self.__class, ModuleType):
            raise ConfigurationError('Content class attribute must be a class')
        # not used yet
        #self.__name = class_
        #self.__normalized_name = _context.getNormalizedName(class_)
        self.__context = _context

    def implements(self, _context, interface):
        for interface in interface:
            _context.action(
                discriminator = (
                'ContentDirective', self.__class, object()),
                callable = classImplements,
                args = (self.__class, interface),
                )
            _context.action(
                discriminator = None,
                callable = provideInterface,
                args = (interface.__module__ + '.' + interface.getName(),
                        interface)
                )

    def require(self, _context,
                permission=None, attributes=None, interface=None,
                like_class=None, set_attributes=None, set_schema=None):
        """Require a the permission to access a specific aspect"""
        if like_class:
            self.__mimic(_context, like_class)

        if not (interface or attributes or set_attributes or set_schema):
            if like_class:
                return
            raise ConfigurationError("Nothing required")

        if not permission:
            raise ConfigurationError("No permission specified")

        if interface:
            for i in interface:
                if i:
                    self.__protectByInterface(i, permission)
        if attributes:
            self.__protectNames(attributes, permission)
        if set_attributes:
            self.__protectSetAttributes(set_attributes, permission)
        if set_schema:
            for s in set_schema:
                self.__protectSetSchema(s, permission)

    def __mimic(self, _context, class_):
        """Base security requirements on those of the given class"""
        _context.action(
            discriminator=('mimic', self.__class, object()),
            callable=protectLikeUnto,
            args=(self.__class, class_),
            )

    def allow(self, _context, attributes=None, interface=None):
        """Like require, but with permission_id zope.Public"""
        return self.require(_context, PublicPermission, attributes, interface)

    def __protectByInterface(self, interface, permission_id):
        "Set a permission on names in an interface."
        for n, d in interface.namesAndDescriptions(1):
            self.__protectName(n, permission_id)
        self.__context.action(
            discriminator = None,
            callable = provideInterface,
            args = (interface.__module__ + '.' + interface.getName(),
                    interface)
            )

    def __protectName(self, name, permission_id):
        "Set a permission on a particular name."
        self.__context.action(
            discriminator = ('protectName', self.__class, name),
            callable = protectName,
            args = (self.__class, name, permission_id)
            )

    def __protectNames(self, names, permission_id):
        "Set a permission on a bunch of names."
        for name in names:
            self.__protectName(name, permission_id)

    def __protectSetAttributes(self, names, permission_id):
        "Set a permission on a bunch of names."
        for name in names:
            self.__context.action(
                discriminator = ('protectSetAttribute', self.__class, name),
                callable = protectSetAttribute,
                args = (self.__class, name, permission_id)
                )

    def __protectSetSchema(self, schema, permission_id):
        "Set a permission on a bunch of names."
        _context = self.__context
        for name in schema:
            field = schema[name]
            if IField.providedBy(field) and not field.readonly:
                _context.action(
                    discriminator = ('protectSetAttribute', self.__class, name),
                    callable = protectSetAttribute,
                    args = (self.__class, name, permission_id)
                    )
        _context.action(
            discriminator = None,
            callable = provideInterface,
            args = (schema.__module__ + '.' + schema.getName(),
                    schema)
            )

    def __call__(self):
        "Handle empty/simple declaration."
        return ()

    def factory(self, _context,
                permission=None, title="", id=None, description=''):
        """Register a zmi factory for this class"""

        id = id or self.__id

        # note factories are all in one pile, services and content,
        # so addable names must also act as if they were all in the
        # same namespace, despite the service/content division
        _context.action(
            discriminator = ('FactoryFromClass', id),
            callable = provideClass,
            args = (id, self.__class,
                    permission, title, description)
            )

def provideClass(id, _class, permission=None,
                 title='', description=''):
    """Provide simple class setup

    - create a component

    - set component permission
    """

    assertPermission(permission)

    if permission == PublicPermission:
        permission = CheckerPublic

    factory = ClassFactory(_class, title, description, permission)
    info = FactoryInfo(title, description)

    zapi.getService(None, Factories).provideFactory(id, factory, info)
