# -*- coding: utf-8 -*-
"""
.. _boto3: https://boto3.readthedocs.io/en/latest/

Get instance lists and tags by different means
==============================================

Module :mod:`ec2helper.get_instances` provides functions for use inside the
:mod:`ec2helper` module to retrieve lists of EC2 instances and their tags.
However these utilities get exposed via :mod:`ec2helper` since they may also be
useful for the user.

.. code-block:: python
    
    from ec2helper import get_instances_by_tag
    
    print(get_instances_by_tag('OS', 'Redhat'))
"""
from __future__ import unicode_literals, absolute_import
import boto3
from ec2helper.utils import IS_EC2, metadata, tags_to_dict


def get_instances_by_tag(key, value=None, region=metadata("region")):
    """
    Get a list of instance data from any tag key or tag key-value combination.
    
    :param string key: The tag key to find EC2 instances with.
    :param string value: If this is not :code:`None` EC2 instances are selected
        by tag key and value combination.
    :param string region: The region to search in, on an EC2 instance it
        defaults to its region.
    :return: EC2 instances as returned by boto3_'s :func:`describe_instances`,
        only that the list is flattened, removing the reservation level and tags
        are converted to dict.
    :rtype: list[dict[string, \*]]
    
    .. code-block:: json
        :caption: Example return value

        [
            {
                "AmiLaunchIndex": 0,
                "Architecture": "x86_64", 
                "BlockDeviceMappings": [
                    { "…": "…" }
                ],
                "…": "…",
                "Tags": {
                    "Name": "my-server1", 
                    "OS": "Amazon Linux 2", 
                    "Stage": "test"
                }, 
                "…": "…",
            },
        ]
    
    .. code-block:: none
        :caption: AWS API permissions
    
        ec2:DescribeInstances
    
    .. seealso::
    
        Function :func:`ec2helper.utils.tags_to_dict`
            For details about tag value conversion.
    """
    client = boto3.client("ec2", region_name=region)
    if value is None:
        tag_filter = {"Name": "tag-key", "Values": [key]}
    else:
        tag_filter = {"Name": "tag:" + key, "Values": [value]}
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
    Get instances and their tags from any tag key or tag key-value combination.
    
    :param string key: The tag key to find EC2 instances with.
    :param string value: If this is not :code:`None` EC2 instances are selected
        by tag key and value combination.
    :param string region: The region to search in, on an EC2 instance it
        defaults to its region.
    :return: A dict of instance ids and their tags as a dict.
    :rtype: dict[string, dict[string, string or None or bool or int or float or 
        datetime]]
    
    .. code-block:: json
        :caption: Example return value

        {
            "i-0a36bbb38a85877f0": {
                "Name": "my-server1",
                "OS": "Amazon Linux 2",
                "Stage": "test",
            },
        }
    
    .. code-block:: none
        :caption: AWS API permissions
    
        ec2:DescribeInstances
    
    .. seealso::
    
        Function :func:`ec2helper.utils.tags_to_dict`
            For details about tag value conversion.
    """
    return dict([(x["InstanceId"], x["Tags"]) for x
                 in get_instances_by_tag(key, value, region)])


def get_instance_status_by_autoscaling_group(asg, region=metadata("region")):
    """
    Get a list of instance status data from a given autoscaling group name.
    
    :param string asg: The name of the autoscaling group.
    :param string region: The region to search in, on an EC2 instance it
        defaults to its region.
    :return: EC2 instance's status data from the given autoscaling group.
    :rtype: list[dict[string, string or bool]]
    
    .. code-block:: json
        :caption: Example return value

        [
            {
                "AvailabilityZone": "eu-central-1a",
                "HealthStatus": "Healthy",
                "InstanceId": "i-0a36bbb38a85877f0",
                "LaunchConfigurationName": "my-lc",
                "LifecycleState": "InService",
                "ProtectedFromScaleIn": false
            },
        ]
    
    .. code-block:: none
        :caption: AWS API permissions
            
        autoscaling:DescribeAutoScalingGroups
    """
    client = boto3.client("autoscaling", region_name=region)
    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asg]
    )
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    return response["AutoScalingGroups"][0]["Instances"]


def get_instances_by_autoscaling_group(asg, region=metadata("region")):
    """
    Get a list of instance data from an autoscaling group.
    
    :param string asg: The name of the autoscaling group.
    :param string region: The region to search in, on an EC2 instance it
        defaults to its region.
    :return: EC2 instances as returned by boto3_'s :func:`describe_instances`,
        only that the list is flattened, removing the reservation level and tags
        are converted to dict.
    :rtype: list[dict[string, \*]]
    
    .. code-block:: json
        :caption: Example return value

        [
            {
                "AmiLaunchIndex": 0,
                "Architecture": "x86_64", 
                "BlockDeviceMappings": [
                    { "…": "…" }
                ],
                "…": "…",
                "Tags": {
                    "Name": "my-server1", 
                    "OS": "Amazon Linux 2", 
                    "Stage": "test"
                }, 
                "…": "…",
            },
        ]
    
    .. code-block:: none
        :caption: AWS API permissions
            
        autoscaling:DescribeAutoScalingGroups
        ec2:DescribeInstances
    
    .. seealso::
    
        Function :func:`ec2helper.utils.tags_to_dict`
            For details about tag value conversion.
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
    Get instances and their tags from an autoscaling group.
    
    :param string asg: The name of the autoscaling group.
    :param string region: The region to search in, on an EC2 instance it
        defaults to its region.
    :return: A dict of instance ids and their tags as a dict.
    :rtype: dict[string, dict[string, string or None or bool or int or float or 
        datetime]]
    
    .. code-block:: json
        :caption: Example return value

        {
            "i-0a36bbb38a85877f0": {
                "Name": "my-asg",
                "OS": "Amazon Linux 2",
                "Stage": "test",
                "aws:autoscaling:groupName": "my-asg"
            },
        }
    
    .. code-block:: none
        :caption: AWS API permissions
            
        autoscaling:DescribeAutoScalingGroups
        ec2:DescribeInstances
    
    .. seealso::
    
        Function :func:`ec2helper.utils.tags_to_dict`
            For details about tag value conversion.
    """
    return dict([(x["InstanceId"], x["Tags"]) for x
                 in get_instances_by_autoscaling_group(asg, region)])
