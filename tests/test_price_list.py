# -*- coding: utf-8 -*-
"""
    Tests price list

    :copyright: (c) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from decimal import Decimal

import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, USER, DB_NAME, CONTEXT
from trytond.transaction import Transaction
from trytond.exceptions import UserError


class TestPriceList(unittest.TestCase):

    def setUp(self):

        trytond.tests.test_tryton.install_module('product_category_price_list')

    def test_0010_check_product_and_category(self):
        """
        Checks that product and category both are not allowed together
        """
        PriceListLine = POOL.get('product.price_list.line')
        ProductTemplate = POOL.get('product.template')
        Uom = POOL.get('product.uom')
        Category = POOL.get('product.category')
        PriceList = POOL.get('product.price_list')
        Currency = POOL.get('currency.currency')
        Party = POOL.get('party.party')
        Company = POOL.get('company.company')
        User = POOL.get('res.user')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            usd, = Currency.create([{
                'name': 'US Dollar',
                'code': 'USD',
                'symbol': '$',
            }])
            party, = Party.create([{
                'name': 'Openlabs',
            }])
            company, = Company.create([{
                'party': party.id,
                'currency': usd
            }])
            User.write([User(USER)], {
                'company': company,
                'main_company': company,
            })

            template, = ProductTemplate.create([{
                'name': 'Test Template',
                'list_price': Decimal('20'),
                'cost_price': Decimal('30'),
                'default_uom': Uom.search([('name', '=', 'Unit')], limit=1)[0]
            }])

            category, = Category.create([{
                'name': 'Test Category'
            }])

            with Transaction().set_context({'company': company.id}):
                price_list, = PriceList.create([{
                    'name': 'Test Price List'
                }])

                # Create price list with product
                PriceListLine.create([{
                    'price_list': price_list.id,
                    'product': template.products[0].id,
                }])

                # Create price list with category
                PriceListLine.create([{
                    'price_list': price_list.id,
                    'category': category.id,
                }])

                # Create price list with both product and category
                with self.assertRaises(UserError):
                    PriceListLine.create([{
                        'price_list': price_list.id,
                        'product': template.products[0].id,
                        'category': category.id,
                    }])

    def test_0020_rules(self):
        """
        Ensure that rules work
        """
        PriceListLine = POOL.get('product.price_list.line')
        ProductTemplate = POOL.get('product.template')
        Uom = POOL.get('product.uom')
        Category = POOL.get('product.category')
        PriceList = POOL.get('product.price_list')
        Currency = POOL.get('currency.currency')
        Party = POOL.get('party.party')
        Company = POOL.get('company.company')
        User = POOL.get('res.user')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            usd, = Currency.create([{
                'name': 'US Dollar',
                'code': 'USD',
                'symbol': '$',
            }])
            party, = Party.create([{
                'name': 'Openlabs',
            }])
            company, = Company.create([{
                'party': party.id,
                'currency': usd
            }])
            User.write([User(USER)], {
                'company': company,
                'main_company': company,
            })

            category, category2 = Category.create([{
                'name': 'Test Category'
            }, {
                'name': 'Test Category 2'
            }])
            template, template2 = ProductTemplate.create([{
                'name': 'Test Template',
                'list_price': Decimal('20'),
                'cost_price': Decimal('30'),
                'default_uom': Uom.search([('name', '=', 'Unit')], limit=1)[0],
                'category': category.id,
            }, {
                'name': 'Test Template 2',
                'list_price': Decimal('40'),
                'cost_price': Decimal('50'),
                'default_uom': Uom.search([('name', '=', 'Unit')], limit=1)[0],
                'category': category2.id,
            }])

            with Transaction().set_context({'company': company.id}):
                price_list, = PriceList.create([{
                    'name': 'Test Price List'
                }])

                # Without any rules unit price should be in effect
                self.assertEqual(
                    price_list.compute(
                        party, template.products[0],
                        template.list_price, 1, template.default_uom,
                        pattern=None
                    ),
                    Decimal('20')
                )
                self.assertEqual(
                    price_list.compute(
                        party, template2.products[0],
                        template2.list_price, 1, template2.default_uom,
                        pattern=None
                    ),
                    Decimal('40')
                )

                # Rule for a product alone
                PriceListLine.create([{
                    'price_list': price_list.id,
                    'product': template.products[0].id,
                    'formula': 'unit_price * 1.1',
                    'sequence': 100,
                }])
                self.assertEqual(
                    price_list.compute(
                        party, template.products[0],
                        template.list_price, 1, template.default_uom,
                        pattern=None
                    ),
                    Decimal('20') * Decimal('1.1')
                )
                self.assertEqual(
                    price_list.compute(
                        party, template2.products[0],
                        template2.list_price, 1, template2.default_uom,
                        pattern=None
                    ),
                    Decimal('40')
                )

                # Rule for the category with higher priority
                PriceListLine.create([{
                    'price_list': price_list.id,
                    'category': category.id,
                    'formula': 'unit_price * 1.2',
                    'sequence': 50,
                }])
                self.assertEqual(
                    price_list.compute(
                        party, template.products[0],
                        template.list_price, 1, template.default_uom,
                        pattern=None
                    ),
                    Decimal('20') * Decimal('1.2')
                )
                self.assertEqual(
                    price_list.compute(
                        party, template2.products[0],
                        template2.list_price, 1, template2.default_uom,
                        pattern=None
                    ),
                    Decimal('40')
                )

                # Match all rule with higher priority
                PriceListLine.create([{
                    'price_list': price_list.id,
                    'formula': 'unit_price * 1.3',
                    'sequence': 30,
                }])
                self.assertEqual(
                    price_list.compute(
                        party, template.products[0],
                        template.list_price, 1, template.default_uom,
                        pattern=None
                    ),
                    Decimal('20') * Decimal('1.3')
                )
                self.assertEqual(
                    price_list.compute(
                        party, template2.products[0],
                        template2.list_price, 1, template2.default_uom,
                        pattern=None
                    ),
                    Decimal('40') * Decimal('1.3')
                )


def suite():
    "Cart test suite"
    suite = unittest.TestSuite()
    suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestPriceList),
    ])
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
