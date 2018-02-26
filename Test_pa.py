#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# by error.d@gmail.com
# 2014-11-21
#

import sys
sys.path.insert(0, '../')

from pa.pa import ProductAssembly

class Leo(object):
    def __init__(self, category_id, biz_id):
        self.category_id = category_id
        self.biz_id = biz_id

cfg = {
    
    }

def setUp():
    ProductAssembly.global_initialize(cfg)

def tearDown():
    pass

def TestPa():
    leo = Leo(15, 20)
    pa = ProductAssembly(None)
    pa.assembly('detail', leo)

    leo = Leo(17, 3981)
    pa.assembly('detail', leo)

def TestPa__load_plugin():
    pa = ProductAssembly(None)
    assert ProductAssembly.has_plugin('NopPaPlugin'), "load_plugin failed"
    assert ProductAssembly.plugin_has_action('NopPaPlugin', 'nop'), \
           "plugin_has_action failed"    
    product = {}
    pa.assembly('nop', product)
    assert product.get('msg', None) is 'nop', "nop run failed"

    

def TestPa__short_interface():
    pa = ProductAssembly(None)
    r = {}
    pa.nop(r)
    assert r['msg'] == 'nop', 'short_interface faield'

#
# End Test unload
#

def TestPa__unload_plugin():
    ProductAssembly.unload_plugin('NopPaPlugin')
    assert not ProductAssembly.has_plugin('NopPaPlugin'), "unload_plugin failed"
