# -*- coding: utf-8 -*-
"""
    __init__.py

    :copyright: (c) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import Pool
from price_list import PriceList, PriceListLine


def register():
    Pool.register(
        PriceList,
        PriceListLine,
        module='product_category_price_list', type_='model'
    )
