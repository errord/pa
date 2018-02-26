# -*- coding: utf-8 -*-
# Copyright 2015 error.d
# by error.d@gmail.com
# 2015-04-23
#

#
# TongCheng Sight PA Plugin
#

from pprint import pprint
from leobase.pa.pa_plugin import PaPlugin
import requests
import json
import time
from leobase.pa.util import to_utf8
from leobase.pa.remote import RemoteCall
from leobase.aml import AML, AMLMap as AMap, AMLAction as Action

VERSION_TUPLE = (0, 1, 1)
VERSION = '.'.join(map(str, VERSION_TUPLE))

SIGHT_CATE_ID = 17
TCSIGHT_BIZ_ID = 3981

CFG_RTC_BASE_URL = 'rtc_base_url'

def string(s):
    if isinstance(s, (int, long, float)):
        return str(s)
    return s.encode('utf8')

class TCSightPaPlugin(PaPlugin):

    _plugin_name = 'TCSightPaPlugin'

    policy_props_template = {
        "tc_policy_name"      : AMap(key="policyName", type=string),
        "remarks"             : AMap(key="remark", type=string),
        "sell_price"          : AMap(key="tcPrice", type=string),
        "min_price"           : AMap(key="tcPrice", type=string),
        "price_info"          : AMap(key="tcPrice", type=string),
        #"quoted_price"        : AMap(key="amount", type=string),
        "tc_ticket_id"        : AMap(key="ticketId", type=string),
        "pay_mode"            : AMap(action=Action('if_key', 'pMode', '==', '0',
                                                   block_template="2",
                                                   else_template="1")),        
        "min_num_per_oneshot" : AMap(key="minT", type=string),      # "最小购票数",
        "max_num_per_oneshot" : AMap(key="maxT", type=string),    
        "tc_policy_id"        : AMap(key="policyId", type=string),  # 策略id（票型id）
        "tc_ticket_name"      : AMap(key="ticketName", type=string),
        "contain_items"       : AMap(key="containItems", type=string),  # 包含项目
        "on_sale_end_time"    : AMap(key="eDate", type=string),
        "on_sale_start_time"  : AMap(key="bDate", type=string)
    }

    """
    data format:
    [{u'bDate': u'2015-03-28',
    u'containItems': u'xxx',
    u'eDate': u'2015-12-31',
    u'is_need_mail': u'0',
    u'maxT': u'99',
    u'minT': u'1',
    u'pMode': u'0',
    u'policyId': u'173238',
    u'policyName': u'xxx',
    u'price': u'220',
    u'realName': u'1',
    u'remark': u'xxx',
    u'tcPrice': u'180',
    u'ticketId': u'60301',
    u'ticketName': u'\u6210\u4eba\u7968',
    u'useCard': u'0'}]
    
    """

    default_sku_representiation = {
        "represent_type": "list",
        "represent_data": []
        }
    
    tc_sight_aml_template = {
        "represent_type": "list",
        "represent_data": [
            AMap(action=Action('for_list', template={
                "sku_id"              : AMap(key='sku_id', type=string),
                "title"               : AMap(key='policyName', type=string),
                "ticket_description"  : AMap(key='remark', type=string),
                "price"               : AMap(key='tcPrice', type=string),
                "sell_status"         : 2,
                "pay_type"            : AMap(action=Action('if_key', 'pMode', '==', '0',
                                                           block_template=2,
                                                           else_template=1)),
                "price_info"          : AMap(key='tcPrice', type=string),
                "min_price"           : AMap(key='tcPrice', type=string),
                "origin_price"        : AMap(key='price', type=string),
                "max_num_per_oneshot" : AMap(key='maxT', type=int),
                "min_num_per_oneshot" : AMap(key='minT', type=int),
                "real_name"           : AMap(key='realName', type=string),
                "ticketId"            : AMap(key='ticketId', type=string),
                "ticketName"          : AMap(key='ticketName', type=string),
                "trans_params": {
                    "contacter_info": {
                        "phone": {
                            "restriction": "",
                            "type": "fill",
                            "value": ""
                        },
                        "contactor_name": {
                            "restriction": "",
                            "type": "fill",
                            "value": ""
                        },
                        "card": AMap(action=Action('if_key', 'useCard', '==', u'1',
                                                   block_template={"restriction": "",
                                                                   "type": "fill",
                                                                   "value": ""}))
                    },
                },
                "quantity": {
                    "restriction": "",
                    "type": "fill",
                    "value": ""
                },
            }, ), ),
      ]
    }

    ### Plugin Method

    def initialize(self, pa, pa_cfg, plugin_cfg, pa_resource):
        warehouse_client = pa_resource.get_resource('warehouse_client')
        if not warehouse_client:
            self.error('NO warehouse_client resource, it is setting resource need!!!')
            return False
        if not plugin_cfg or CFG_RTC_BASE_URL not in plugin_cfg:
            self.error('Not has "%s" on config', CFG_RTC_BASE_URL)
            return False

        self._rtc_base_url = plugin_cfg[CFG_RTC_BASE_URL]
        self._warehouse_client = warehouse_client
        self.remote = RemoteCall(warehouse_client,
                                 operator='tc_sight', channel='leo_api',
                                 channel_info='pa')

    def match(self, product):
        leo = product
        if int(leo.category_id) == SIGHT_CATE_ID and \
               int(leo.biz_id) == TCSIGHT_BIZ_ID:
            return True
        else:
            return False

    # action
    def detail_handler(self, product, dataset, **kwargs):
        """
        product: leo dict object
        """
        self.info("detail_handler leo:%s args:%s", product, kwargs)
        
        if 'sight_result' not in kwargs:
            self.error('Not sight_result argument')
            return

        sight_result = kwargs['sight_result']
        self._tc_sight_detail(product, sight_result)

        # compatibility codes
        self.__sight_20150501(product, sight_result)

    # action
    def price_calendar_handler(self, product, dataset, **kwargs):
        """
        product: leo
        """
        sku_id = kwargs.get('sku_id', 0)
        self.info("price_calendar_handler sku_id:%s", sku_id)
        if not sku_id:
            self.error('sku id is 0 product:%s kwargs:%s', product, kwargs)
            return

        if 'price_calendar' not in kwargs:
            self.error('Not price_calendar argument product:%s kwargs:%s', product, kwargs)
            return

        self._tc_sight_calendar(product, sku_id, kwargs['price_calendar'])

    ### Compatibility Old Version

    def __sight_20150501(self, leo, sight_result):
        """
        2015-5-1 sight hard-code
        """
        if int(leo.participate_status) == 101:
            del sight_result['resources']
        else:
            self.error('participate_status not 101 ps:%s leo_id:%s', leo.participate_status, leo.id)
        sight_result["price_info"] = leo.price_info
        sight_result["origin_price"] = ''
        # fixbug: sight stop sell
        sight_result["sell_restriction"] = {
            "sell_status": 2,
            "max_num_per_oneshot": 99,
            "min_num_per_oneshot": 1
            }

    ### Business Logic

    def _tc_sight_detail(self, leo, sight_result):
        aml = AML(debug=self.plugin_cfg().get('aml_debug', False))
        policy_list = self._get_tc_policy_list_from_rtc(leo.tc_scenery_id)
        if policy_list is None:
            sight_result['sku_representation'] = self.default_sku_representiation
            return
        policy_list = self._append_sku(leo, policy_list)
        sight_result['sku_representation'] = aml.run(self.tc_sight_aml_template,
                                                     policy_list)

    def _tc_sight_calendar(self, leo, sku_id, price_calendar):
        sku = None
        for resource in leo.resources:
            if int(resource.id) == sku_id:
                sku = resource
        if not sku:
            self.error('no sku sku_id:%s leo_id:%s', sku_id, leo.id)
            return

        start_time = time.localtime(time.time())
        start_time = time.strftime("%Y-%m-%d %H:%M:%S", start_time)

        price_calendar_list = self._get_tc_price_calendar_from_rtc(
            sku.tc_scenery_id,
            sku.tc_policy_id,
            start_time=start_time,
            end_time='')

        if price_calendar_list is None:
            return

        del price_calendar[:]
        for calendar in price_calendar_list:
            calendar['sku_id'] = sku_id
            price_calendar.append(calendar)

    def _request_rtc(self, url):
        try:
            time_s = time.time()
            r = requests.get(url)
        except Exception as e:
            self.error('request rtc failed url:%s time: %sms msg:%s',
                       url, int((time.time() - time_s) * 1000), e)
            return None
        self.info('rtc request: %s time: %sms', url,
                  int((time.time() - time_s) * 1000))
        try:
            response_json = json.loads(r.text)
        except Exception as e:
            self.error('request_rtc json load failed url:%s response:%s msg:%s',
                       url, r.text, e)
            response_json = None
        return response_json

    def _get_tc_policy_list_from_rtc(self, scenery_id):
        url = self._rtc_base_url + '/index?service=tcsight&scenery_id=%s&interface=' \
              'policy_list' % scenery_id
        return self._request_rtc(url)

    def _get_tc_price_calendar_from_rtc(self, scenery_id, policy_id,
                                        start_time, end_time):
        url = self._rtc_base_url + '/index?service=tcsight&policy_id=%s&scenery_id=%s'\
              '&interface=calendar&start_time=%s&end_time=%s' % (policy_id, scenery_id,
                                                                 start_time, end_time)
        return self._request_rtc(url)

    def _append_sku(self, leo, policy_list):
        # {policy_id: sku_id}
        live_id_list = {l.tc_policy_id: l.id for l in leo.resources}
        self.info('live id list: %s', live_id_list)
        result_policy = []
        is_add_sku = False
        is_remove_sku = False
        for policy in policy_list:
            policy_id = int(policy['policyId'])
            # exists or add new sku
            if policy_id in live_id_list:
                sku_id = live_id_list.pop(policy_id)
            else:
                is_add_sku = True
                sku_id = self._add_new_sku(leo, policy)

            if sku_id:
                policy['sku_id'] = sku_id
                result_policy.append(policy)
        # remove old sku
        is_remove_sku = self._remove_old_sku(leo, live_id_list.values())
        if is_add_sku or is_remove_sku:
            self.info('is_add_sku:%s is_remove_sku:%s', is_add_sku, is_remove_sku)
            self._warehouse_client.updateLeoIndexAndCache(int(leo.id),
                                                          update_mongodb=False)
        return result_policy

    def _add_new_sku(self, leo, policy):
        self.info('add new sku leo:%s policy:%s', leo, policy)
        aml = AML(debug=self.plugin_cfg().get('aml_debug', False))
        sku_props = aml.run(self.policy_props_template, policy)
        unique_name = '_'.join([policy['policyName'], policy['policyId']])

        # find exists sku
        sku_id = self.remote.find_sku(leo.goods_id, unique_name)
        if not sku_id:
            # no exists, add new sku
            sku_props['total_stocks'] = '10000'
            sku_props['stocks'] = '10000'
            sku_props['quoted_price'] = '0'
            sku_id = self.remote.add_sku(leo.goods_id, unique_name,
                                         policy['policyName'], sku_props)
        if not sku_id:
            return 0
        if not self.remote.attach_sku(sku_id, leo.id):
            return 0
        if not self.remote.update_leo_multisku(leo.id, leo.spu_id, leo.status):
            return 0
        return sku_id

    def _remove_old_sku(self, leo, sku_ids):
        if sku_ids:
            self.info('remove old sku leo:%s sku_ids:%s', leo, sku_ids)
            self.remote.detach_sku(sku_ids, leo.id)
            return True
        return False
