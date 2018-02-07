#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from ec2helper import Instance, json_dump, get_instance_tags_by_tag
import ec2helper.utils
import boto3

i = Instance()
#tags = i.tags
#json_dump(tags)

#def lock(locktag, searchtag=locktag, searchvalue=None)

client = boto3.client('autoscaling', region_name=i.region)
response = client.describe_auto_scaling_instances(
    InstanceIds=[i.id]
)
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
"""


#json_dump(get_instance_tags_by_tag("MetricGroup"))#, "CachingProxyTest"))
json_dump(response)
