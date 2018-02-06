# -*- coding: utf-8 -*-
"""
"""
from __future__ import unicode_literals, absolute_import
import boto3
from ec2_metadata import ec2_metadata
from ec2helper.utils import tags_to_dict, dict_to_tags

class Instance(object):
    """
    """

    def __init__(self, instance_id=ec2_metadata.instance_id,
        region=ec2_metadata.region):
        """
        Constructor
        """
        self.id = instance_id
        self.region = region

    @property
    def tags(self):
        """                                                                     
        Get this instance's tags from API (as dict).
        """                                    
        client = boto3.client("ec2", region_name=self.region)
        response = client.describe_tags(
            Filters=[{
                "Name": "resource-id",
                "Values": [self.id]
            }]
        )                                 
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        return tags_to_dict(response["Tags"])

    @tags.setter                                                         
    def tags(self, value):                                               
        """
        Same as update_tags.
        """
        self.update_tags(**value)

    def update_tags(self, **kwargs):
        """                                                                     
        Update this instance's tags via API (from dict).
        """                                                                     
        client = boto3.client("ec2", region_name=self.region)
        response = client.create_tags(
            Resources=[self.id],
            Tags=dict_to_tags(kwargs)
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def delete_tags(self, *args):
        """
        Remove the given or all tags.
        """
        client = boto3.client("ec2", region_name=self.region)
        response = client.delete_tags(
            Resources=[self.id],
            Tags=[{"Key": k} for k in args]
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
