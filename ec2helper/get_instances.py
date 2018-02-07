# -*- coding: utf-8 -*-
"""
Common utils.
"""
from __future__ import unicode_literals, absolute_import
import boto3
from ec2_metadata import ec2_metadata
from ec2helper.utils import tags_to_dict


def get_instances_by_tag(key, value=None, region=ec2_metadata.region):
    """
    Get a list of instance data from any tag-key or tag-key-value combination
    and return the whole data as returned by the API, only that the list is
    flattened, removing the reservation level and tags are converted to dict.
    """
    client = boto3.client("ec2", region_name=region)
    if value is None:
        tag_filter = {"Name": "tag-key", "Values": [key]}
    else:
        tag_filter = {"Name": "tag:"+key, "Values": [value]}
    response = client.describe_instances(
        Filters=[tag_filter]
    )
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    instances = [i for r in response["Reservations"] for i in r["Instances"]]
    for i in instances:
        i["Tags"] = tags_to_dict(i["Tags"])
    return instances


def get_instance_tags_by_tag(key, value=None, region=ec2_metadata.region):
    """
    Like get_instances_by_tag, but only returns a dict of instance IDs and
    their tags as dict.
    """
    return dict([(x["InstanceId"], x["Tags"]) for x
        in get_instances_by_tag(key, value, region)])
