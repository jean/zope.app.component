##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Registration Tests

$Id$
"""
__docformat__ = "reStructuredText"
import unittest

import zope.interface
from zope.testing import doctest

from zope.app.testing import setup
from zope.app.component import interfaces
from zope.app.folder import folder

class SiteManagerStub(object):
    zope.interface.implements(interfaces.ILocalSiteManager)

class CustomFolder(folder.Folder):

    def __init__(self, name):
        self.__name__ = name
        super(CustomFolder, self).__init__()

    def __repr__(self):
        return '<%s %s>' %(self.__class__.__name__, self.__name__)


def test_SiteManagerAdapter():
    """
    The site manager adapter is used to find the nearest site for any given
    location. If the provided context is a site,

      >>> site = folder.Folder()
      >>> sm = SiteManagerStub()
      >>> site.setSiteManager(sm)

    then the adapter simply return's the site's site manager:
    
      >>> from zope.app.component.site import SiteManagerAdapter
      >>> SiteManagerAdapter(site) is sm
      True

    If the context is a location (i.e. has a `__parent__` attribute),

      >>> ob = folder.Folder()
      >>> ob.__parent__ = site
      >>> ob2 = folder.Folder()
      >>> ob2.__parent__ = ob

    we 'acquire' the closest site and return its site manager: 

      >>> SiteManagerAdapter(ob) is sm
      True
      >>> SiteManagerAdapter(ob2) is sm
      True

    If we are unable to find a site manager, a `ComponentLookupError` is
    raised:
    
      >>> orphan = CustomFolder('orphan')
      >>> SiteManagerAdapter(orphan) #doctest: +NORMALIZE_WHITESPACE
      Traceback (most recent call last):
      ...
      ComponentLookupError:
      'Could not adapt <CustomFolder orphan> to ISiteManager'
    """


def test_setThreadSite_clearThreadSite():
    """
    This test ensures that the site is corectly set and cleared in a thread
    during traversal using event subscribers. Before we start, no site is set:

      >>> from zope.app.component import hooks
      >>> hooks.getSite() is None
      True

    If a non-site is traversed, 

      >>> ob = object()
      >>> request = object()

      >>> from zope.app import publication
      >>> ev = publication.interfaces.BeforeTraverseEvent(ob, request)
      >>> from zope.app.component import site
      >>> site.threadSiteSubscriber(ev)

    still no site is set:

      >>> hooks.getSite() is None
      True
      
    On the other hand, if a site is traversed, 

      >>> sm = SiteManagerStub()
      >>> mysite = CustomFolder('mysite')
      >>> mysite.setSiteManager(sm)

      >>> ev = publication.interfaces.BeforeTraverseEvent(mysite, request)
      >>> site.threadSiteSubscriber(ev)

      >>> hooks.getSite()
      <CustomFolder mysite>

    Once the request is completed,

      >>> ev = publication.interfaces.EndRequestEvent(mysite, request)
      >>> site.clearThreadSiteSubscriber(ev)

    the site assignment is cleared again:

      >>> hooks.getSite() is None
      True
    """

def setUp(test):
    setup.placefulSetUp()

def tearDown(test):
    setup.placefulTearDown()

def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite(),
        doctest.DocFileSuite('../site.txt',
                             setUp=setUp, tearDown=tearDown),
        ))

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
    
