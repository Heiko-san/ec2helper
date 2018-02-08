#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from ec2helper import Instance, json_dump, get_instance_tags_by_tag
import ec2helper.utils
import boto3
import time

i = Instance()
#tags = i.tags
#json_dump(tags)

#def lock(locktag, searchtag=locktag, searchvalue=None)

"""
{
    "AutoScalingInstances": [], 
    "ResponseMetadata": {
        "HTTPHeaders": {
            "content-length": "350", 
            "content-type": "text/xml", 
            "date": "Wed, 07 Feb 2018 08:38:53 GMT", 
            "x-amzn-requestid": "5466aeb7-0be2-11e8-815a-8f44496317ef"
        }, 
        "HTTPStatusCode": 200, 
        "RequestId": "5466aeb7-0be2-11e8-815a-8f44496317ef", 
        "RetryAttempts": 0
    }
}
{
    "AutoScalingInstances": [
        {
"AutoScalingGroupName": "hfi-amazon2-boreus-ami", 
            "AvailabilityZone": "eu-central-1b", 
   "HealthStatus": "HEALTHY", 
            "InstanceId": "i-0d2cb773a18dfa487", 
            "LaunchConfigurationName": "hfi-amazon2-boreus-ami", 
   "LifecycleState": "InService", 
"ProtectedFromScaleIn": false
        }
    ], 
    "ResponseMetadata": {
        "HTTPHeaders": {
            "content-length": "833", 
            "content-type": "text/xml", 
            "date": "Wed, 07 Feb 2018 16:12:41 GMT", 
            "x-amzn-requestid": "b959e409-0c21-11e8-9ea5-f90d60e343bb"
        }, 
        "HTTPStatusCode": 200, 
        "RequestId": "b959e409-0c21-11e8-9ea5-f90d60e343bb", 
        "RetryAttempts": 0
    }
}
"""


#json_dump(get_instance_tags_by_tag("MetricGroup"))#, "CachingProxyTest"))
json_dump(i.autoscaling)
i.autoscaling_healthy = False
json_dump(i.autoscaling)
time.sleep(10)
json_dump(i.autoscaling)
i.autoscaling_healthy = True
json_dump(i.autoscaling)
time.sleep(10)
json_dump(i.autoscaling)
