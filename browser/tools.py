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
"""Tools View

$Id$
"""
import zope.interface
import zope.event
from zope.component.interfaces import IFactory

from zope.app import zapi
from zope.app.component import site, interfaces
from zope.app.container.browser import adding
from zope.app.event import objectevent

class IToolType(zope.interface.interfaces.IInterface):
    """Interfaces implementing the tool type are considered tools."""


class IToolConfiguration(zope.interface.Interface):
    """This is an object that represents a tool configuration"""

    #title
    #
    #description
    #
    #interface
    #
    #unique


class ToolConfiguration(object):
    """ """
    zope.interface.implements(IToolConfiguration)

    def __init__(self, interface, title, description=None, unique=False,
                 folder='tools'):
        self.interface = interface
        self.title = title
        self.description = description
        self.unique = unique
        self.folder = folder


class SiteManagementView(adding.Adding):
    """A Site Management via Tools"""

    activeTool = None
    addTool = False
    renameList = []

    def __init__(self, context, request):
        super(SiteManagementView, self).__init__(context, request)
        if 'activeTool' in request:
            self.activeTool = zapi.getUtility(IToolConfiguration,
                                              request['activeTool'])

    def update(self):
        """ """
        msg = u''
        if "INSTALL-SUBMIT" in self.request:
            self.install()
            msg = u'Tools successufully installed.'
        if "UNINSTALL-SUBMIT" in self.request:
            self.uninstall()
            msg = u'Tools successufully uninstalled.'
        if "ADD-TOOL-SUBMIT" in self.request:
            self.action(self.request['type_name'], self.request['id'])
        elif "CANCEL-ADD-TOOL-SUBMIT" in self.request:
            self.activeTool = None
        elif "ACTIVATE-SUBMIT" in self.request:
            self.changeStatus(interfaces.registration.ActiveStatus)
            msg = u'Tools successfully activated.'
        elif "DEACTIVATE-SUBMIT" in self.request:
            self.changeStatus(interfaces.registration.InactiveStatus)
            msg = u'Tools successfully deactivated.'
        elif "ADD-SUBMIT" in self.request:
            self.addTool = True
        elif "DELETE-SUBMIT" in self.request:
            self.delete()
        elif "RENAME-SUBMIT" in self.request:
            if 'selected' in self.request:
                self.renameList = self.request['selected']
            if 'new_names' in self.request:
                self.rename()
                msg = u'Tools successullfy renamed.'
        elif "RENAME-CANCEL-SUBMIT" in self.request:
            self.activeTool = None
        return msg

    def getSiteManagementFolder(self, tool):
        """Get the site management folder for this tool."""
        sm = zapi.getSiteManager()
        if not tool.folder in sm:
            folder = site.SiteManagementFolder()
            zope.event.notify(objectevent.ObjectCreatedEvent(folder))
            sm[tool.folder] = folder            
        return sm[tool.folder]

    def toolExists(self, interface, name=''):
        """Check whether a tool already exists in this site"""
        sm = zapi.getSiteManager()
        for reg in sm.registrations():
            if isinstance(reg, site.UtilityRegistration):
                if reg.name == name and reg.provided == interface:
                    return True
        return False

    def getUniqueTools(self):
        """Get unique tools info for display."""
        results = [{'name': tool.interface.getName(),
                    'title': tool.title,
                    'description': tool.description,
                    'exists': self.toolExists(tool.interface)
                    }
                   for name, tool in zapi.getUtilitiesFor(IToolConfiguration)
                   if tool.unique]
        results.sort(lambda x, y: cmp(x['title'], y['title']))
        return results

    def getToolInstances(self, tool):
        """Find every registered utility for a given tool configuration."""
        regManager = self.context[tool.folder].registrationManager
        return [
            {'name': reg.name,
             'url': zapi.absoluteURL(reg.component, self.request),
             'rename': tool is self.activeTool and reg.name in self.renameList,
             'active': reg.status == u'Active'
            }
            for reg in regManager.values()
            if (zapi.isinstance(reg, site.UtilityRegistration) and
                reg.provided.isOrExtends(tool.interface))]

    def getTools(self):
        """Return a list of all tools"""
        results = [{'name': tool.interface.getName(),
                    'title': tool.title,
                    'description': tool.description,
                    'instances': self.getToolInstances(tool),
                    'add': tool is self.activeTool and self.addTool,
                    'rename': tool is self.activeTool and self.renameList
                    }
                   for name, tool in zapi.getUtilitiesFor(IToolConfiguration)
                   if not tool.unique]
        results.sort(lambda x, y: cmp(x['title'], y['title']))
        return results

    def install(self):
        tool_names = self.request['selected']
        for tool_name in tool_names:
            self.activeTool = zapi.getUtility(IToolConfiguration, tool_name)
            type_name = list(self.addingInfo())[0]['extra']['factory']
            self.action(type_name)
        self.activeTool = None

    def uninstall(self):
        type_names = self.request['selected']
        self.request.form['selected'] = [u'']
        for name, tool in zapi.getUtilitiesFor(IToolConfiguration):
            if name in type_names:
                self.activeTool = tool
                self.delete()
        self.activeTool = None

    def changeStatus(self, status):
        tool = self.activeTool
        regManager = self.context[tool.folder].registrationManager
        names = self.request.form['selected']
        print names
        for reg in regManager.values():
            if reg.provided.isOrExtends(tool.interface) and reg.name in names:
                print reg.name
                reg.status = status

    def delete(self):
        tool = self.activeTool
        regManager = self.context[tool.folder].registrationManager
        names = self.request.form['selected']
        for reg in regManager.values():
            if reg.provided.isOrExtends(tool.interface) and reg.name in names:
                component = reg.component
                reg.status = interfaces.registration.InactiveStatus
                del regManager[zapi.name(reg)]
                del zapi.getParent(component)[zapi.name(component)]

    def rename(self):
        tool = self.activeTool
        regManager = self.context[tool.folder].registrationManager
        new_names = self.request['new_names']
        old_names = self.request['old_names']
        for reg in regManager.values():
            if reg.provided.isOrExtends(tool.interface) and \
                   reg.name in old_names:
                orig_status = reg.status
                reg.status = interfaces.registration.InactiveStatus
                reg.name = new_names[old_names.index(reg.name)]
                reg.status = orig_status

    def add(self, content):
        """See zope.app.container.interfaces.IAdding"""
        sm = self.context
        self.context = self.getSiteManagementFolder(self.activeTool)

        util = super(SiteManagementView, self).add(content)

        # Add registration
        name = not self.activeTool.unique and self.contentName or u''
        registration = site.UtilityRegistration(
            name, self.activeTool.interface, util)
        self.context.registrationManager.addRegistration(registration)
        registration.status = interfaces.registration.ActiveStatus

        self.context = sm
        return util
        
    def nextURL(self):
        """See zope.app.container.interfaces.IAdding"""
        return (zapi.absoluteURL(self.context, self.request)
                + '/@@SiteManagement')

    def addingInfo(self):
        """See zope.app.container.interfaces.IAdding"""
        sm = self.context
        self.context = self.getSiteManagementFolder(self.activeTool)
        self._addFilterInterface = self.activeTool.interface
        results = super(SiteManagementView, self).addingInfo()
        self.context = sm
        self._addFilterInterface = None
        return results
