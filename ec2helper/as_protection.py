# -*- coding: utf-8 -*-
"""
The AutoscalingProtection context guard
=======================================

This class is not meant to be used directly, use
:func:`ec2helper.instance.Instance.autoscaling_protection` instead.
The properties of this context guard are readonly and can be accessed inside 
the with-block.
"""
from __future__ import unicode_literals, absolute_import


class AutoscalingProtection(object):
    """
    Context guard for scale in protection.
        
    :param instance: The instance to protect.
    """
    _locked = False

    def __init__(self, instance):
        """Constructor - see class docu."""
        self._instance = instance
        #: The autoscaling status data as returned by
        #: :attr:`ec2helper.instance.Instance.autoscaling` at the time the 
        #: protection was set.
        self.autoscaling = None

    def __enter__(self):
        """
        Protect this instance.
        """
        self.autoscaling = self._instance.autoscaling
        if self.autoscaling is not None:
            self._instance.autoscaling_protected = True
        self._locked = True
        return self

    def __exit__(self, type, value, traceback):
        """
        Reset protection for this instance.
        """
        if self.autoscaling is not None:
            self._instance.autoscaling_protected = self.autoscaling[
                "ProtectedFromScaleIn"]

    def __setattr__(self, name, value):
        """
        Make all attributes readonly after protection was set.
        """
        if self._locked:
            raise AttributeError(
                "Attributes of class '{0}' are readonly.".format(
                    self.__class__.__name__))
        else:
            super(type(self), self).__setattr__(name, value)
