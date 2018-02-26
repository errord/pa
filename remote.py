#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from py_util.string import to_utf8
from py_util.md5 import md5
import copy
import logging

# OPS_INFO = {'operator':'leo', 'channel': 'leo', 'channel_info': 'leo'}

class RemoteCall(object):
    def __init__(self, warehouse_client,
                 operator='', channel='', channel_info=''):
        self.warehouse_client = warehouse_client
        self._save_ops_info = None
        self._ops_info = dict(operator=operator, channel=channel,
                              channel_info=channel_info)

    def begin_call(self):
        self._save_ops_info = self.warehouse_client.getOpsInfo()
        self.warehouse_client.setOpsInfo(self._ops_info)

    def end_call(self):
        assert self._save_ops_info, 'call end_call, but no call begin_call'
        self.warehouse_client.setOpsInfo(self._save_ops_info)

    def detach_sku(self, sku_id, leo_id):
        """删除某个sku"""
        self.begin_call()
        leo_id = int(leo_id)
        if not isinstance(sku_id, list):
            sku_id = [sku_id]
        sku_id = map(int, sku_id)
        ret = None
        try:
            ret = self.warehouse_client.detachSkusFromLeo(leo_id, sku_id)
        except Exception as e:
            logging.error('detach sku except leo_id:%s sku_id:%s e:%s',
                          leo_id, sku_id, e)
            ret = False
        self.end_call()
        return ret

    def add_sku(self, goods_id, unique_name, cn_name, sku_info):
        """增加某个sku"""
        self.begin_call()
        cn_name = to_utf8(cn_name)
        name = md5(unique_name)
        goods_id = int(goods_id)
        sku_id = 0
        try:
            sku_id = self.warehouse_client.addSku(goods_id=goods_id,
                                                  name=name,
                                                  cn_name=cn_name,
                                                  dict_properties=sku_info)
        except Exception as e:
            logging.error('add new sku except, goods_id:%s cn_name:%s sku_prop:%s' \
                          ' e:%s', goods_id, cn_name, sku_info, e)
            sku_id = 0
        if not sku_id:
            logging.error('add new sku failed, goods_id:%s cn_name:%s sku_prop:%s',
                          goods_id, cn_name, sku_info)
            sku_id = 0
        self.end_call()
        return sku_id

    def attach_sku(self, sku_id, leo_id):
        self.begin_call()
        sku_id = int(sku_id)
        leo_id = int(leo_id)
        ret = False
        try:
            ret = self.warehouse_client.attachSkusToLeo(leo_id=leo_id,
                                                         sku_ids=[sku_id])
        except Exception as e:
            logging.error('attach sku except leo_id:%s sku_id:%s e:%s',
                          leo_id, sku_id, e)
            ret = False
        self.end_call()
        return ret

    def update_leo_multisku(self, leo_id, spu_id, leo_status):
        from leobase.base_ctrl import get_now_datetime
        self.begin_call()
        leo_id = int(leo_id)
        spu_id = int(spu_id)
        ret = False
        try:
            ret = self.warehouse_client.updateLeo(leo_id=leo_id, target_id=0,
                                                  status=leo_status,
                                                  target_type='refers')
            if ret:
                properties = {'version': get_now_datetime()}
                ret = self.warehouse_client.updateSpu(spu_id=spu_id,
                                                      dict_properties=properties)
        except Exception as e:
            logging.error('update leo multisku failed leo_id:%s e:%s', leo_id, e)
        self.end_call()
        return ret

    def find_sku(self, goods_id, name):
        self.begin_call()
        goods_id = int(goods_id)
        name = md5(name)
        try:
            sku_id = self.warehouse_client.getSkuIdByGoodAndName(goods_id, name)
        except Exception as e:
            logging.error('get sku failed goods_id:%s name:%s e:%s',
                          goods_id, name, e)
            sku_id = 0
        self.end_call()
        return sku_id
