##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Interfaces for the Local Component Architecture

$Id$
"""
import zope.interface
import zope.schema
from zope.component.interfaces import ISiteManager
from zope.app.container.interfaces import IContainer
from zope.app.container.constraints import ContainerTypesConstraint
from zope.app.container.constraints import ItemTypePrecondition
from zope.app.i18n import ZopeMessageIDFactory as _
import registration

class ILocalAdapterRegistry(registration.IRegistry,
                            registration.ILocatedRegistry):

    def adaptersChanged():
        """Update the adapter surrogates, since the registrations changed."""

    def baseChanged():
        """Someone changed the base registry

        This should only happen during testing
        """

class IComponentManager(zope.interface.Interface):

    def queryComponent(type=None, filter=None, all=True):
        """Return all components that match the given type and filter

        The arguments are:

        type -- An argument is the interface a returned component must
                provide.

        filter -- A Python expression that must evaluate to `True` for any
                  returned component; `None` means that no filter has been
                  specified.

        all -- A flag indicating whether all component managers in
               this place should be queried, or just the local one.

        The objects are returned a sequence of mapping objects with keys:

        path -- The component path

        component -- The component
        """

class IBindingAware(zope.interface.Interface):

    def bound(name):
        """Inform a service component that it is providing a service

        Called when an immediately-containing service manager binds
        this object to perform the named service.
        """

    def unbound(name):
        """Inform a service component that it is no longer providing a service

        Called when an immediately-containing service manager unbinds
        this object from performing the named service.
        """

class IPossibleSite(zope.interface.Interface):
    """An object that could be a site
    """

    def setSiteManager(sitemanager):
        """Sets the service manager for this object.
        """

    def getSiteManager():
        """Returns the service manager contained in this object.

        If there isn't a service manager, raise a component lookup.
        """

class ISite(IPossibleSite):
    """Marker interface to indicate that we have a site
    """

class ILocalSiteManager(ISiteManager, IComponentManager,
                        registration.IRegistry):
    """Service Managers act as containers for Services.

    If a Service Manager is asked for a service, it checks for those it
    contains before using a context-based lookup to find another service
    manager to delegate to.  If no other service manager is found they defer
    to the ComponentArchitecture ServiceManager which contains file based
    services.
    """

    def addSubsite(subsite):
        """Add a subsite of the site

        Local sites are connected in a tree. Each site knows about
        its containing sites and its subsites.
        """

    next = zope.interface.Attribute('The site that this site is a subsite of.')

    def findModule(name):
        """Find the module of the given name.

        If the module can be find in the folder or a parent folder
        (within the site manager), then return it, otherwise, delegate
        to the module service.

        This must return None when the module is not found.

        """

    def resolve(name):
        """Resolve a dotted object name.

        A dotted object name is a dotted module name and an object
        name within the module.

        TODO: We really should switch to using some other character than
        a dot for the delimiter between the module and the object
        name.

        """

class ISiteManagementFolder(registration.IRegisterableContainer,
                            IContainer):
    """Component and component registration containers."""

    __parent__ = zope.schema.Field(
        constraint = ContainerTypesConstraint(
            ISiteManager,
            registration.IRegisterableContainer,
            ),
        )

class ILocalUtility(registration.IRegisterable):
    """Local utility marker.

    A marker interface that indicates that a component can be used as
    a local utility.

    Utilities should usually also declare they implement
    IAttributeAnnotatable, so that the standard adapter to
    IRegistered can be used; otherwise, they must provide
    another way to be adaptable to IRegistered.
    """


class IAdapterRegistration(registration.IComponentRegistration):
    """Local Adapter Registration for Local Adapter Registry

    The adapter registration is used to provide local adapters via the
    adapter registry. It is an extended component registration, whereby the
    component is the adapter factory in this case.
    """
    required = zope.schema.Choice(
        title = _("For interface"),
        description = _("The interface of the objects being adapted"),
        vocabulary="Interfaces",
        readonly = True,
        required=False,
        default=None)

    with = zope.schema.Tuple(
        title = _("With interfaces"),
        description = _("Additionally required interfaces"),
        readonly=True,
        value_type = zope.schema.Choice(vocabulary='Interfaces'),
        required=False,
        default=())

    provided = zope.schema.Choice(
        title = _("Provided interface"),
        description = _("The interface provided"),
        vocabulary="Interfaces",
        readonly = True,
        required = True)

    name = zope.schema.TextLine(
        title=_(u"Name"),
        readonly=True,
        required=False,
        )

    permission = zope.schema.Choice(
        title=_("The permission required for use"),
        vocabulary="Permission Ids",
        readonly=False,
        required=False,
        )


class IUtilityRegistration(IAdapterRegistration):
    """Utility registration object.

    Adapter registries are also used to to manage utilities, since utilities
    are adapters that are instantiated and have no required interfaces. Thus,
    utility registrations must fulfill all requirements of an adapter
    registration as well.
    """

    name = zope.schema.TextLine(
        title=_("Register As"),
        description=_("The name under which the utility will be known."),
        readonly=True,
        required=True,
        )

    provided = zope.schema.Choice(
        title=_("Provided interface"),
        description=_("The interface provided by the utility"),
        vocabulary="Utility Component Interfaces",
        readonly=True,
        required=True,
        )
