# -*- coding: utf-8 -*-
# Copyright 2015 error.d
# by error.d@gmail.com
# 2015-04-23

#
# Nop PA Plugin
#

from leobase.pa.pa_plugin import PaPlugin

VERSION_TUPLE = (0, 0, 1)
VERSION = '.'.join(map(str, VERSION_TUPLE))

class NopPaPlugin(PaPlugin):

    _plugin_name = 'NopPaPlugin'

    def initialize(self, pa, pa_cfg, plugin_cfg, pa_resource):
        pass

    def match(self, product):
        return True

    def nop_handler(self, product, dataset, **kwargs):
        product['msg'] = 'nop'

