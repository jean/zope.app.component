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
""" Test handler for 'factory' subdirective of 'content' directive

$Id: test_factory.py,v 1.11 2004/03/09 12:39:25 srichter Exp $
"""
import unittest
from cStringIO import StringIO

from zope.configuration.xmlconfig import xmlconfig
from zope.configuration.xmlconfig import XMLConfig
from zope.component import createObject
from zope.proxy import removeAllProxies
from zope.app.tests.placelesssetup import PlacelessSetup
from zope.security.management import newInteraction, system_user

from zope.app import zapi
import zope.app.security
import zope.app.component

from zope.app.component.tests.exampleclass import ExampleClass


class ParticipationStub:

    def __init__(self, principal):
        self.principal = principal
        self.interaction = None


def configfile(s):
    return StringIO("""<configure
      xmlns='http://namespaces.zope.org/zope'
      i18n_domain='zope'>
      %s
      </configure>
      """ % s)

class Test(PlacelessSetup, unittest.TestCase):
    def setUp(self):
        super(Test, self).setUp()
        newInteraction(ParticipationStub(system_user))
        XMLConfig('meta.zcml', zope.app.component)()
        XMLConfig('meta.zcml', zope.app.security)()

    def testFactory(self):
        f = configfile('''
<permission id="zope.Foo" title="Zope Foo Permission" />
<content class="zope.app.component.tests.exampleclass.ExampleClass">
    <factory
      id="Example"
      title="Example content"
      description="Example description"
       />
</content>''')
        xmlconfig(f)
        obj = createObject(None, 'Example')
        obj = removeAllProxies(obj)
        self.failUnless(isinstance(obj, ExampleClass))

def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
