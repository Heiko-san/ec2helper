# -*- coding: utf-8 -*-
"""
Get instance lists and tags by different means.
"""
from __future__ import unicode_literals, absolute_import
import boto3
from ec2helper.utils import IS_EC2, metadata, tags_to_dict


def get_instances_by_tag(key, value=None, region=metadata("region")):
    """
    Get a list of instance data (describe_instances) from any tag-key or
    tag-key-value combination and return the whole data as returned by the API,
    only that the list is flattened, removing the reservation level and tags
    are converted to dict.
    
    .. code-block:: none
            :caption: AWS API permissions
            
            autoscaling:DescribeAutoScalingGroups
            autoscaling:DescribeAutoScalingInstances
            autoscaling:SetInstanceHealth
            autoscaling:SetInstanceProtection
            ec2:DescribeInstances
            ec2:DeleteTags
            ec2:DescribeTags
            ec2:CreateTags
    """
    client = boto3.client("ec2", region_name=region)
    if value is None:
        tag_filter = {"Name": "tag-key", "Values": [key]}
    else:
        tag_filter = {"Name": "tag:"+key, "Values": [value]}
    paginator = client.get_paginator("describe_instances")
    instances = list()
    for page in paginator.paginate(
        Filters=[tag_filter]
    ):
        instances.extend(
            [i for r in page["Reservations"] for i in r["Instances"]]
        )
    for i in instances:
        i["Tags"] = tags_to_dict(i["Tags"])
    return instances


def get_instance_tags_by_tag(key, value=None, region=metadata("region")):
    """
    Like get_instances_by_tag, but only returns a dict of instance IDs and
    their tags as dict.

    {
        "i-0a36bbb38a85877f0": {
            "Name": "my-server1",
            "OS": "Amazon Linux 2",
            "Stage": "test",
        },
        "i-0d2cb773a18dfa487": {
            "Name": "my-server2",
            "OS": "Amazon Linux 2",
            "Stage": "test",
        }
    }
    """
    return dict([(x["InstanceId"], x["Tags"]) for x
        in get_instances_by_tag(key, value, region)])


def get_instance_status_by_autoscaling_group(asg, region=metadata("region")):
    """
    Get a list of instance data ("Instances" of describe_auto_scaling_groups)
    from given autoscaling group name.

    [
        {
            "AvailabilityZone": "eu-central-1a",
            "HealthStatus": "Healthy",
            "InstanceId": "i-0a36bbb38a85877f0",
            "LaunchConfigurationName": "my-lc",
            "LifecycleState": "InService",
            "ProtectedFromScaleIn": false
        },
        {
            "AvailabilityZone": "eu-central-1b",
            "HealthStatus": "Healthy",
            "InstanceId": "i-0d2cb773a18dfa487",
            "LaunchConfigurationName": "my-lc",
            "LifecycleState": "InService",
            "ProtectedFromScaleIn": true
        }
    ]
    """
    client = boto3.client("autoscaling", region_name=region)
    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asg]
    )
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    return response["AutoScalingGroups"][0]["Instances"]


def get_instances_by_autoscaling_group(asg, region=metadata("region")):
    """
    Get a list of instance data (describe_instances) from given autoscaling
    group name and return the whole data as returned by the API, only that the
    list is flattened, removing the reservation level and tags are converted to
    dict.
    """
    asg_instances = get_instance_status_by_autoscaling_group(asg, region)
    client = boto3.client("ec2", region_name=region)
    paginator = client.get_paginator("describe_instances")
    instances = list()
    for page in paginator.paginate(
        InstanceIds=[x["InstanceId"] for x in asg_instances]
    ):
        instances.extend(
            [i for r in page["Reservations"] for i in r["Instances"]]
        )
    for i in instances:
        i["Tags"] = tags_to_dict(i["Tags"])
    return instances


def get_instance_tags_by_autoscaling_group(asg, region=metadata("region")):
    """
    Like get_instances_by_autoscaling_group, but only returns a dict of
    instance IDs and their tags as dict.

    {
        "i-0a36bbb38a85877f0": {
            "Name": "my-asg",
            "OS": "Amazon Linux 2",
            "Stage": "test",
            "aws:autoscaling:groupName": "my-asg"
        },
        "i-0d2cb773a18dfa487": {
            "Name": "my-asg",
            "OS": "Amazon Linux 2",
            "Stage": "test",
            "aws:autoscaling:groupName": "my-asg"
        }
    }
    """
    return dict([(x["InstanceId"], x["Tags"]) for x
        in get_instances_by_autoscaling_group(asg, region)])
