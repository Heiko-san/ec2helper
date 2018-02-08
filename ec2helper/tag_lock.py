# -*- coding: utf-8 -*-
"""
TagLock class to create a tag based lock accross all instances of a given
group.
"""
from __future__ import unicode_literals, absolute_import
from ec2helper.get_instances import get_instance_tags_by_tag, \
    get_instance_tags_by_autoscaling_group
from ec2helper.errors import ResourceLockingError, ResourceAlreadyLocked, \
    InstanceUnhealthy
from datetime import datetime, timedelta
from dateutil import tz


class TagLock(object):
    """
    Create a tag based lock accross all instances of a given group, group can
    be selected by autoscaling group of this instance (default), by tag-key
    (group_tag) or tag-key and tag-value combination (group_tag, group_value).
    Lock is released after with-block is left, but also has a validity timeout
    (ttl=1800) in minutes as a fallback, adjust if you expect the process to
    run longer.
    Lock will not be assigned to an unhealthy autoscaling instance by default
    (check_health=True), disable to ignore health and lifecycle state.
    If this instance can't be locked a ResourceLockingError will be raised
    (ResourceAlreadyLocked or InstanceUnhealthy).

    import time
    from ec2helper import Instance
    from ec2helper.errors import *
    i = Instance()
    try:                                                                            
        with i.lock("MyLockTag") as lock:                                           
            print("start with-block with tag lock: " + lock.name)
            time.sleep(10)                                                          
            print("end with-block with tag lock: " + lock.name)                     
    except ResourceLockingError:                                                    
        print("Could not retrieve lock")
    """
    _locked = False

    def __init__(self, instance, lock_name, group_tag=None, group_value=None,
        ttl=1800, check_health=True):
        """constructor"""
        self._instance = instance
        self.name = lock_name
        self.group_tag = group_tag
        self.group_value = group_value
        self.ttl = ttl
        self.check_health = check_health

    def __enter__(self):
        """
        Lock this instance.
        """
        self.__set_lock_time()
        self.__backup_autoscaling_data()
        self.__report_unhealthy()
        self.__refresh_lock_group_instaces()
        self.__report_locked_ressource()
        self.__autoscaling_protect()
        self.__set_lock_tag()
        self.__refresh_lock_group_instaces()
        try:
            self.__report_locked_ressource(ignore_self=True)
        except ResourceLockingError:
            self.__unlock()
            raise
        self._locked = True
        return self

    def __exit__(self, type, value, traceback):
        """
        Unlock this instance.
        """
        self.__unlock()

    def __setattr__(self, name, value):
        """
        Make all attributes readonly after lock was set.
        """
        if self._locked:
            raise AttributeError(
                "Attributes of class '{0}' are readonly.".format(
                self.__class__.__name__))
        else:
            super(type(self), self).__setattr__(name, value)

    def __unlock(self):
        """
        Unlock this instance.
        """
        self.__remove_lock_tag()
        self.__autoscaling_reset_protection()

    def __set_lock_tag(self):
        """
        Set the lock tag with the calculated end time.
        """
        self._instance.tags = {self.name: self.end_time}

    def __remove_lock_tag(self):
        """
        Remove the lock tag.
        """
        self._instance.delete_tags(self.name)

    def __report_locked_ressource(self, ignore_self=False):
        """
        Check if any other instance holds a still valid resource lock.
        """
        for instance in self.group_instances:
            if ignore_self and instance == self._instance.id:
                continue
            if self.name in self.group_instances[instance
                ] and self.group_instances[instance][self.name] > self.time:
                raise ResourceAlreadyLocked()

    def __set_lock_time(self):
        """
        Save internal datetime representations of "now" and "now+ttl" in UTC
        time zone for ttl calculation.
        """
        self.time = datetime.now(tz=tz.tzutc()).replace(microsecond=0)
        self.end_time = self.time + timedelta(seconds=self.ttl*60)

    def __report_unhealthy(self):
        """
        Do not allow unhealty instances to get the lock if check_health = True
        (default).
        """
        if self.check_health:
            if self.autoscaling is not None:
                if "HEALTHY" != self.autoscaling["HealthStatus"
                ] or self.autoscaling["LifecycleState"] != "InService":
                    raise InstanceUnhealthy()

    def __refresh_lock_group_instaces(self):
        """
        Refresh the list of all instances and their tags for this "lock-group".
        Lock group can be autoscaling group, a tag-key or a tag-key-value
        combination.
        """
        if self.group_tag is not None:
            self.group_instances = get_instance_tags_by_tag(self.group_tag,
                self.group_value)
        else:
            assert self.autoscaling is not None, ("Instance must be in an "
                "autoscaling group or 'group_tag' must be given.")
            self.group_instances = get_instance_tags_by_autoscaling_group(
                self.autoscaling["AutoScalingGroupName"])

    def __backup_autoscaling_data(self):
        """
        Create a backup of the current autoscaling state of the instance.
        """
        self.autoscaling = self._instance.autoscaling

    def __autoscaling_protect(self):
        """
        If autoscaling, protect instance from scale in for lock duration.
        """
        if self.autoscaling is not None:
            self._instance.autoscaling_protected = True

    def __autoscaling_reset_protection(self):
        """
        If autoscaling, set the original scale in protection state of the
        instance on unlock.
        """
        if self.autoscaling is not None:
            self._instance.autoscaling_protected = self.autoscaling[
                "ProtectedFromScaleIn"]
