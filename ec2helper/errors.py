# -*- coding: utf-8 -*-
"""
Exception classes
"""
from __future__ import unicode_literals, absolute_import

class Ec2HelperError(Exception):
    pass

class ResourceLockingError(Ec2HelperError):
    pass

class ResourceAlreadyLocked(ResourceLockingError):
    pass

class InstanceUnhealthy(ResourceLockingError):
    pass
