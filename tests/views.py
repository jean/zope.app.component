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

Revision information: $Id: views.py,v 1.1 2003/12/17 10:05:54 jim Exp $
"""

from zope.interface import Interface, implements

class IR(Interface):
    pass

class IV(Interface):
    def index():
        pass

class IC(Interface): pass

class V1:
    implements(IV)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def index(self):
        return 'V1 here'

    def action(self):
        return 'done'

class VZMI(V1):
    def index(self):
        return 'ZMI here'

class R1:

    def index(self):
        return 'R1 here'

    def action(self):
        return 'R done'

    def __init__(self, request):
        pass

    implements(IV)

class RZMI(R1):
    pass