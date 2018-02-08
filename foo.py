#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from ec2helper import Instance, json_dump
from ec2helper.errors import *
import time

i = Instance()
#with i.lock("mylock", "Stage", "test") as lock:
try:
    with i.lock("MyLockTag") as lock:
        print("start with-block with tag lock: " + lock.name + " @ " + str(lock.time) + " valid until " + str(lock.end_time))
        time.sleep(10)
        print("end with-block with tag lock: " + lock.name)
except ResourceLockingError:
    print("Could not retrieve lock")
#data = i.autoscaling
#json_dump(data)
#json_dump(get_instance_tags_by_autoscaling_group(data["AutoScalingGroupName"]))
