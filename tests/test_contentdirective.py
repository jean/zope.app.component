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
"""

$Id: test_contentdirective.py,v 1.9 2003/08/17 06:06:17 philikon Exp $
"""

import unittest
from StringIO import StringIO

import zope.app.security
import zope.app.component

from zope.component.exceptions import ComponentLookupError
from zope.configuration.xmlconfig import xmlconfig, XMLConfig
from zope.app.tests.placelesssetup import PlacelessSetup
from zope.security.management import newSecurityManager, system_user
from zope.security.proxy import Proxy
from zope.app.security.exceptions import UndefinedPermissionError
from zope.component import getService
from zope.app.services.servicenames import Factories
from zope.app.component.globalinterfaceservice import queryInterface

# explicitly import ExampleClass and IExample using full paths
# so that they are the same objects as resolve will get.
from zope.app.component.tests.exampleclass import ExampleClass
from zope.app.component.tests.exampleclass import IExample, IExample2


def configfile(s):
    return StringIO("""<configure
      xmlns='http://namespaces.zope.org/zope'
      i18n_domain='zope'>
      %s
      </configure>
      """ % s)

class TestContentDirective(PlacelessSetup, unittest.TestCase):
    def setUp(self):
        PlacelessSetup.setUp(self)
        newSecurityManager(system_user)
        XMLConfig('meta.zcml', zope.app.component)()
        XMLConfig('meta.zcml', zope.app.security)()

        try:
            del ExampleClass.__implements__
        except AttributeError:
            pass

    def testEmptyDirective(self):
        f = configfile("""
<content class="zope.app.component.tests.exampleclass.ExampleClass">
</content>
                       """)
        xmlconfig(f)


    def testImplements(self):
        self.assertEqual(queryInterface(
            "zope.app.component.tests.exampleclass.IExample"), None)

        f = configfile("""
<content class="zope.app.component.tests.exampleclass.ExampleClass">
  <implements interface="zope.app.component.tests.exampleclass.IExample" />
</content>
                       """)
        xmlconfig(f)
        self.failUnless(IExample.isImplementedByInstancesOf(ExampleClass))

        self.assertEqual(queryInterface(
            "zope.app.component.tests.exampleclass.IExample"), IExample)


    def testMulImplements(self):
        self.assertEqual(queryInterface(
            "zope.app.component.tests.exampleclass.IExample"), None)
        self.assertEqual(queryInterface(
            "zope.app.component.tests.exampleclass.IExample2"), None)

        f = configfile("""
<content class="zope.app.component.tests.exampleclass.ExampleClass">
  <implements interface="
           zope.app.component.tests.exampleclass.IExample
           zope.app.component.tests.exampleclass.IExample2
                       " />
</content>
                       """)
        xmlconfig(f)
        self.failUnless(IExample.isImplementedByInstancesOf(ExampleClass))
        self.failUnless(IExample2.isImplementedByInstancesOf(ExampleClass))

        self.assertEqual(queryInterface(
            "zope.app.component.tests.exampleclass.IExample"), IExample)
        self.assertEqual(queryInterface(
            "zope.app.component.tests.exampleclass.IExample2"),
                         IExample2)

    def testRequire(self):
        f = configfile("""
<permission id="zope.View" title="Zope view permission" />
<content class="zope.app.component.tests.exampleclass.ExampleClass">
    <require permission="zope.View"
                      attributes="anAttribute anotherAttribute" />
</content>
                       """)
        xmlconfig(f)

    def testAllow(self):
        f = configfile("""
<content class="zope.app.component.tests.exampleclass.ExampleClass">
    <allow attributes="anAttribute anotherAttribute" />
</content>
                       """)
        xmlconfig(f)

    def testMimic(self):
        f = configfile("""
<content class="zope.app.component.tests.exampleclass.ExampleClass">
    <require like_class="zope.app.component.tests.exampleclass.ExampleClass" />
</content>
                       """)
        xmlconfig(f)


class TestFactorySubdirective(PlacelessSetup, unittest.TestCase):
    def setUp(self):
        PlacelessSetup.setUp(self)
        newSecurityManager(system_user)
        XMLConfig('meta.zcml', zope.app.component)()
        XMLConfig('meta.zcml', zope.app.security)()

    def testFactory(self):
        f = configfile("""
<permission id="zope.Foo" title="Zope Foo Permission" />

<content class="zope.app.component.tests.exampleclass.ExampleClass">
    <factory
      id="Example"
      permission="zope.Foo"
      title="Example content"
      description="Example description"
    />
</content>
                       """)
        xmlconfig(f)
        factory = getService(None, Factories).getFactory('Example')
        self.assertEquals(factory.title, "Example content")
        self.assertEquals(factory.description, "Example description")

    def testFactoryNoId(self):
        f = configfile("""
<permission id="zope.Foo" title="Zope Foo Permission" />

<content class="zope.app.component.tests.exampleclass.ExampleClass">
    <factory
      permission="zope.Foo"
      title="Example content"
      description="Example description"
    />
</content>
                       """)
        xmlconfig(f)
        fservice = getService(None, Factories)
        self.assertRaises(ComponentLookupError, fservice.getFactory, 'Example')
        factory = fservice.getFactory('zope.app.component.tests.exampleclass.ExampleClass')
        self.assertEquals(factory.title, "Example content")
        self.assertEquals(factory.description, "Example description")

    def testFactoryUndefinedPermission(self):

        f = configfile("""
<permission id="zope.Foo" title="Zope Foo Permission" />

<content class="zope.app.component.tests.exampleclass.ExampleClass">
    <factory
      id="Example"
      permission="zope.UndefinedPermission"
      title="Example content"
      description="Example description"
    />
</content>
            """)
        self.assertRaises(UndefinedPermissionError, xmlconfig, f,
                          testing=1)


    def testFactoryPublicPermission(self):

        f = configfile("""
<permission id="zope.Foo" title="Zope Foo Permission" />

<content class="zope.app.component.tests.exampleclass.ExampleClass">
    <factory
      id="Example"
      permission="zope.Public"
      title="Example content"
      description="Example description"
    />
</content>
            """)
        xmlconfig(f)
        factory = getService(None, Factories).getFactory('Example')
        self.failUnless(type(factory) is Proxy)


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestContentDirective))
    suite.addTest(loader.loadTestsFromTestCase(TestFactorySubdirective))
    return suite


if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
