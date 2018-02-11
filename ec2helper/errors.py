# -*- coding: utf-8 -*-
"""
Exception classes
=================

.. code-block:: none
    :caption: Exception hierarchy
    
    Exception
     +-- Ec2HelperError
          +-- ResourceLockingError
               +-- ResourceAlreadyLocked
               +-- InstanceUnhealthy
"""


class Ec2HelperError(Exception):
    """
    Common base class for all exceptions raised by :mod:`ec2helper`.
    """
    pass


class ResourceLockingError(Ec2HelperError):
    """
    Common base class for all exceptions raised by 
    :class:`~ec2helper.instance.Instance`'s
    :func:`~ec2helper.instance.Instance.lock` context guard.
    """
    pass


class ResourceAlreadyLocked(ResourceLockingError):
    """
    Raised by :class:`~ec2helper.instance.Instance`'s
    :func:`~ec2helper.instance.Instance.lock` context guard if another EC2
    instance already holds the requested lock.
    """
    pass


class InstanceUnhealthy(ResourceLockingError):
    """
    Raised by :class:`~ec2helper.instance.Instance`'s 
    :func:`~ec2helper.instance.Instance.lock` context guard if this EC2 instance
    can't retrieve the lock because it is considered unhealthy by autoscaling
    group.
    """
    pass


class TagNotFound(Ec2HelperError):
    """
    Raised if a requested tag is not found.
    """
    pass
