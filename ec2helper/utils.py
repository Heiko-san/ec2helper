# -*- coding: utf-8 -*-
"""
.. _boto3: https://boto3.readthedocs.io/en/latest/
.. _ec2_metadata: https://github.com/adamchainz/ec2-metadata

Common helper utilities
=======================

Module :mod:`ec2helper.utils` provides functions for use inside the
:mod:`ec2helper` module.
However these utilities get exposed via :mod:`ec2helper` since they may also be
useful for the user.

.. code-block:: python
    
    from ec2helper import IS_EC2, metadata
    
    if IS_EC2:
        print(metadata('ami_id'))
"""
from __future__ import unicode_literals, absolute_import
import six
import re
import json
import requests
from ec2_metadata import ec2_metadata
from datetime import datetime, date
from dateutil import parser

INTEGER = re.compile(r"^-?\d+$")
FLOAT = re.compile(r"^-?\d+(\.\d+)?$")
ISOTIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{6})?([+-]\d{2}:\d{2})?$")

try:
    # This request still succeeded with a timeout of 0.001, so 0.5 should be a
    # good compromise between stability and load time on none EC2 instances.
    requests.get("http://169.254.169.254/latest/meta-data/reservation-id",
                 timeout=0.5)
except requests.exceptions.ConnectTimeout:
    IS_EC2 = False
else:
    #: This variable indicates if calling the EC2 metadata API succeeded, thus
    #: if we're on an EC2 instance.
    IS_EC2 = True


def metadata(attribute):
    """
    Get EC2 metadata from local EC2 metadata API via ec2_metadata_.
    But check if we are actually running on an EC2 instance (using
    :attr:`~ec2helper.utils.IS_EC2`) and return :code:`None` otherwise.
    
    :param string attribute: The attribute to get from ec2_metadata_.
    :return: The value from ec2_metadata_ if running on an EC2 instance,
        :code:`None` otherwise.
    :rtype: None or string or any other data returned by ec2_metadata
    """
    if IS_EC2:
        return getattr(ec2_metadata, attribute)
    return None


def json_dump(data):
    """
    Convenience helper for printing human readable JSON data to the console
    for debugging and testing purpose.
    This will actually just :code:`print(json.dumps(data, indent=4, sort_keys
    ...))` but adds basic serialization support for any object type,
    especially for :py:mod:`datetime` since it often is included in boto3_
    responses.
    
    :param data: Any data structure you want to json.dump.
    """

    def json_serial(obj):
        if isinstance(obj, (datetime, date)):
            return "{0} ({1})".format(obj.isoformat(), type(obj))
        else:
            return "{0} ({1})".format(str(obj), type(obj))

    print(json.dumps(
        data,
        indent=4,
        sort_keys=True,
        default=json_serial
    ))


def _parse_value(value):
    """
    Convert string tag value to data types.
    
    .. seealso::
    
        Function :func:`ec2helper.utils.tags_to_dict`
            Uses this function for conversion.
    """
    if value == "": return None
    if value == "True": return True
    if value == "False": return False
    if INTEGER.match(value): return int(value)
    if FLOAT.match(value): return float(value)
    if ISOTIME.match(value): return parser.parse(value)
    return value


def _string_value(value):
    """
    Convert data types to string tag value.
    
    .. seealso::
    
        Function :func:`ec2helper.utils.dict_to_tags`
            Uses this function for conversion.
    """
    if value is None: return ""
    if isinstance(value, datetime): return value.isoformat()
    return six.text_type(value)


def tags_to_dict(tags):
    """
    Convert AWS style tags as supplied by AWS API to a flat dict.
    Values will also be converted to native data types if possible:
    
    * Empty string will convert to :code:`None`.
    * "True" and "False" will be converted to bool, but only with that exact 
      case because :code:`True` and :code:`False` stringify that way (we don't
      want to change a value if we just load and save tags).
    * :code:`int` values will be parsed (:code:`^-?\d+$`).
    * :code:`float` values will be parsed (:code:`^-?\d+\.\d+$`).
    * ISO time strings will convert to :py:mod:`datetime` (e.g. 
      "2018-02-10T16:07:48+00:00").
    
    :param list tags: AWS style tags. :code:`[{"Key": …, "Value": …}, …]`
    :return: Tags as a flat dict of the Key-Value pairs.
    :rtype: dict[string, string or None or bool or int or float or datetime]
    
    .. code-block:: json
        :caption: Example return value
    
        {
            "Name": "my-server1",
            "OS": "Amazon Linux 2",
            "Stage": "prod",
            "Backup": true,
            "RetentionDays": 30
        }
    
    .. seealso::
    
        Function :func:`~ec2helper.utils.dict_to_tags`
            Reverse conversion.
    """
    return dict([(x["Key"], _parse_value(x["Value"])) for x in tags])


def dict_to_tags(tags):
    """
    Convert flat tags dict to AWS style tags as supplied by AWS API.
    Values will be stringified.
    
    * :code:`None` will convert to empty string.
    * :py:mod:`datetime` will convert to ISO time strings (e.g.
      "2018-02-10T16:07:48+00:00").
    
    :param dict tags: Tags as a flat dict of the Key-Value pairs.
    :return: AWS style tags. :code:`[{"Key": …, "Value": …}, …]`
    :rtype: list[dict[string, string]]
    
    .. seealso::
    
        Function :func:`~ec2helper.utils.tags_to_dict`
            Reverse conversion.
    """
    return [{"Key": k, "Value": _string_value(v)} for k, v in
            six.iteritems(tags)]
