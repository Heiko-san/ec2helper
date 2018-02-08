#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from ec2helper import Instance, json_dump, get_instance_tags_by_tag, get_instance_tags_by_autoscaling_group
import ec2helper.utils
import boto3
import time

i = Instance()
#tags = i.tags
#json_dump(tags)

#def lock(locktag, searchtag=locktag, searchvalue=None)

json_dump(get_instance_tags_by_tag("OS"))#, "CachingProxyTest"))
#data = i.autoscaling
#json_dump(data)
#json_dump(get_instance_tags_by_autoscaling_group(data["AutoScalingGroupName"]))
