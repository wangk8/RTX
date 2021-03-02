# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model_ import Model
from openapi_server import util


class NodeBinding(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, id=None):  # noqa: E501
        """NodeBinding - a model defined in OpenAPI

        :param id: The id of this NodeBinding.  # noqa: E501
        :type id: str
        """
        self.openapi_types = {
            'id': str
        }

        self.attribute_map = {
            'id': 'id'
        }

        self._id = id

    @classmethod
    def from_dict(cls, dikt) -> 'NodeBinding':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The NodeBinding of this NodeBinding.  # noqa: E501
        :rtype: NodeBinding
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this NodeBinding.

        An instance of NodeBinding is a single KnowledgeGraph Node mapping, identified by the corresponding 'id' object key identifier of the Node within the Knowledge Graph. Instances of NodeBinding may include extra annotation (such annotation is not yet fully standardized).  # noqa: E501

        :return: The id of this NodeBinding.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this NodeBinding.

        An instance of NodeBinding is a single KnowledgeGraph Node mapping, identified by the corresponding 'id' object key identifier of the Node within the Knowledge Graph. Instances of NodeBinding may include extra annotation (such annotation is not yet fully standardized).  # noqa: E501

        :param id: The id of this NodeBinding.
        :type id: str
        """
        if id is None:
            raise ValueError("Invalid value for `id`, must not be `None`")  # noqa: E501

        self._id = id