# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import models, fields, api
#import suds
import suds.client

from odoo.exceptions import ValidationError


class E2yunCsutomerExtends(models.Model):
    _inherit = 'res.partner'

    app_code = fields.Char(string='', copy=False, readonly=True, default=lambda self: _('New'))
    shop_code = fields.Char(string='')
    shop_name = fields.Char(string='')
    referrer = fields.Many2one('res.users', string='')
    occupation = fields.Char(string='')
    car_brand = fields.Char(string='')
    user_nick_name = fields.Char(string='')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ], string='')
    customer_source = fields.Selection([
        ('barcode', 'Barcode'),
        ('manual', 'Manual'),
    ], string='', default='manual')
    pos_state = fields.Boolean(String='Sync Pos State',default=False)


    @api.model
    def create(self, vals):
        if vals.get('app_code', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['app_code'] = self.env['ir.sequence'].with_context(force_company=vals['company_id'])\
                                   .next_by_code('app.code') or _('New')
            else:
                vals['app_code'] = self.env['ir.sequence'].next_by_code('app.code') or _('New')

        result = super(E2yunCsutomerExtends, self).create(vals)
        return result

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100

class resPartnerBatch(models.TransientModel):
    _name = 'res.partner.extends.batch'

    # def sync_customer_to_pos(self):
    #     ctx = self._context.copy()
    #
    #     active_model = ctx.get('active_model')
    #     active_ids = ctx.get('active_ids', [])
    #
    #     rep = self.env['res.partner'].browse(active_ids)
    #     sync_list = []
    #     cart_items = suds.client.factory.create('ArrayOfCartItem')
    #     for r in rep:
    #         cart_item = suds.client.factory.create('CartItem')
    #
    #         cart_item.provice = r.state_id.name#省
    #         cart_item.city = r.city
    #         cart_item.area = r.street
    #         cart_item.detailaddress = r.street2
    #         cart_item.name1 = r.name
    #         cart_item.name2 = r.user_nick_name
    #         cart_item.mendian = r.shop_code
    #         cart_item.telf1 = r.phone
    #         cart_item.vtext = r.shop_name
    #         cart_item.remark = r.occupation
    #         cart_item.posid = r.app_code
    #         cart_item.pernam = r.create_uid.name
    #
    #
    #         sync_list.append(cart_item)
    #
    #         # sync_list.append({
    #         #     'provice':r.state_id.name,#省
    #         #     'city':r.city,#城市
    #         #     'area':r.street,#县区
    #         #     'detailaddress':r.street2,#地址
    #         #     'name1':r.name,#名称
    #         #     'name2':r.user_nick_name,#昵称
    #         #     'mendian':r.shop_code,#门店编码
    #         #     'telf1':r.phone,#电话
    #         #     'vtext':r.shop_name,#门店名称
    #         #     'remark':r.occupation,#职业
    #         #     'posid':r.app_code,#app编码
    #         #     'pernam':r.create_uid.name,#创建人
    #         # })
    #         cart_items.CartItem = cart_items
    #     if cart_items:
    #         ICPSudo = self.env['ir.config_parameter'].sudo()
    #
    #         url = ICPSudo.get_param('e2yun.sync_pos_member_webservice_url')  # webservice调用地址
    #         client = suds.client.Client(url)
    #
    #         result = client.service.createMember(sync_list)# 调用方法所需要的参数
    #         print(result)
    def sync_customer_to_pos(self):
        ctx = self._context.copy()

        #active_model = ctx.get('active_model')
        active_ids = ctx.get('active_ids', [])

        rep = self.env['res.partner'].browse(active_ids)
        for r in rep:
            ICPSudo = self.env['ir.config_parameter'].sudo()

            url = ICPSudo.get_param('e2yun.sync_pos_member_webservice_url')  # webservice调用地址
            client = suds.client.Client(url)

            result = client.service.createMember(r.state_id.name or '',     #省
                                                 r.city or '',              #城市
                                                 r.street or '',            #县区
                                                 r.street2 or '',           #地址
                                                 r.name or '',              #名称
                                                 r.user_nick_name or '',    #昵称
                                                 r.shop_code or '',         #门店编码
                                                 r.mobile or '',             #手机号码
                                                 r.phone or '',             #电话号码
                                                 r.email or '',             #邮箱
                                                 r.shop_name or '',         #门店名称
                                                 r.occupation or '',        #职业
                                                 r.app_code or '',          #app编码
                                                 r.create_uid.name)          #创建人

            if result != 'S':
                raise ValidationError(result)
            else:
                r.pos_state = True

        return {
            'warning': {
                'title': 'Tips',
                'message': '同步成功'
            }
        }