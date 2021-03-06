# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import json
import logging

import requests
import suds.client
from bs4 import BeautifulSoup
from odoo.addons.website_helpdesk_form.controller.main import WebsiteForm
from odoo.addons.utils_tools.iptools.IpAddress import IpAddress

from odoo import http
from odoo.http import request
from ..models import myjsondateencode

# from odoo.addons.website_form.controllers.main import WebsiteForm

_logger = logging.getLogger(__name__)


class E2yunWebsiteForm(WebsiteForm):

    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        request.params['userip'] = request.httprequest.access_route[0]
        if request.params.get('order_datetime'):
            paraorder_datetime = request.params['order_datetime']
            order_datetime = datetime.datetime.strptime(request.params['order_datetime'], "%Y-%m-%d")
            lang = request.env['ir.qweb.field'].user_lang()
            strftime_format = (u"%s %s" % (lang.date_format, lang.time_format))
            request.params['order_datetime'] = datetime.datetime.strftime(order_datetime, strftime_format)
        if request.params.get('u_address') or request.params.get('j_address'):
            request.params['address'] = request.params['u_address'] + request.params['j_address']
        reponse_website = super(E2yunWebsiteForm, self).website_form(model_name, **kwargs)
        return reponse_website

    @http.route('''/helpdesk/<model("helpdesk.team", "[('use_website_helpdesk_form','=',True)]"):team>/submit''', type='http', auth="public", website=True)
    def website_helpdesk_form(self, team, **kwargs):
        _logger.info("e2yun_website_helpdesk_form:")
        website_helpdesk_form = super(E2yunWebsiteForm, self).website_helpdesk_form(team, **kwargs)
        # teams = request.env['helpdesk.team'].sudo().search([])
        teams = request.env['helpdesk.team'].sudo(request.env.user).search([])
        street = request.env.user.partner_id._display_address()
        ticket_type = request.env['helpdesk.ticket.type'].sudo().search([('name', '=', '网页')], limit=1) or request.env['helpdesk.ticket.type'].sudo().search([], limit=1)
        brandtype = request.env['helpdesk.ticket.brandtype'].sudo().search([])
        user_agent = request.httprequest.headers.get('user-agent').lower()
        is_wx_client = '1' if 'micromessenger' in user_agent else '0'
        website_helpdesk_form.qcontext['default_values'].update({
            'phone': request.env.user.partner_id.phone,
            'mobile': request.env.user.partner_id.mobile,
            'street': request.env.user.partner_id.street,
            'area_id': request.env.user.partner_id.area_id.name,
            'city_id': request.env.user.partner_id.city_id.name,
            'state_id': request.env.user.partner_id.state_id.name,
            'userip': request.httprequest.access_route[0],
            'partner_id': request.env.user.partner_id.id,
            'teams': teams,
            'ticket_type_id': ticket_type,
            'brandtype': brandtype,
            'is_wx_client':is_wx_client
        })
        # 更新JSDK以备使用定位功能,获取当前用户地址报修。
        url_ = request.httprequest.url;
        _logger.info("参数打印:%s" % url_)
        _logger.info(website_helpdesk_form.qcontext['default_values'])
        try:
            website_helpdesk_form.qcontext.update(request.env.user.get_jsapi_ticket(url_))
        except Exception as e:

            _logger.error("加载微信jsapi_ticket错误。%s" % e)
        website_helpdesk_form.qcontext['title'] = '客户报修'
        _logger.info(website_helpdesk_form.qcontext)
        return website_helpdesk_form

    @http.route('/website_form/common_problems', type='http', auth="public", methods=['GET', 'POST'], website=True)
    def website_common_problems(self, **kwargs):
        return request.render("e2yun_website_helpdesk_form.common_problems")

    @http.route('/website_form/userhelpdesk', type='http', auth="public", methods=['GET', 'POST'], website=True)
    def website_userhelpdesk(self, **kwargs):
        # 用户实际IP地址 userip
        userip = request.httprequest.access_route[0]
        ipinfo = IpAddress.getregion(userip)
        team_id = None
        # print(r.request.url)
        if ipinfo:
            userregion = ipinfo['region']
            if userregion and userregion == '广东':
                region_user = '深圳'
            else:
                region_user = '北京'
            team_id = request.env['helpdesk.team'].search([('name', 'like', region_user)], limit=1).id
            _logger.info("地区：%s:%s" % (userip, region_user))
        if not team_id:
            _logger.info("获取IP地址，地区失败。")
            team_id = request.env['helpdesk.team'].search([], limit=1, order='id asc').id
        helpdeskurl = '/helpdesk/' + str(team_id) + '/submit'
        _logger.info("访问地址：%s" % helpdeskurl)
        # return http.local_redirect('/web/login?redirect=%s' % helpdeskurl)
        return http.local_redirect(helpdeskurl)

    @http.route(['/helpdesk/searchusermatnr'], type='json', auth='public')
    def searchusermatnr(self, **kwargs):
        url = request.env['ir.config_parameter'].sudo().get_param('e2yun.pos_url') + "/esb/webservice/Serviceorder?wsdl"  # webservice调用地址
        client = suds.client.Client(url)
        datajsonstring = dict()
        datajsonstring['telephone'] =  kwargs.get('telephone')
        result = client.service.searchUserMatnr(json.dumps(datajsonstring, cls=myjsondateencode.MyJsonEncode))
        resultjson = json.loads(result)
        _logger.info("参数打印:%s" % resultjson)
        return resultjson

    def getuserip(self, request):
        userip = request.httprequest.remote_addr
        print(userip)
        if userip == '127.0.0.1':
            userip = request.httprequest.headers.get('X-Forwarded-For')
        return userip
