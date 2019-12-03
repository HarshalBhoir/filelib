from datetime import datetime

from odoo import api, fields, models, exceptions, tools


class TargetCompletion(models.Model):
    _inherit = 'outbound.final'
    _description = '目标完成占比情况'

    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        res = super(TargetCompletion, self).search_read(domain, fields, offset, limit, order)
        ctx = self._context.copy()
        if ctx['new_view'] == 1:
            res = [{'target_year': ctx['target_year'], 'target_month': ctx['target_month'], 'werks': ctx['werks'],
                    'vkorgtext':ctx['vkorgtext'], 'vtweg': ctx['vtweg'], 'kunnr': ctx['kunnr'], 'ywy': ctx['ywy'],
                    'jiesuan_amount': ctx['jiesuan_amount'], 'target_amount': ctx['target_amount']}]
        return res

    def default_target_year(self):
        ctx = self._context.copy()
        if ctx.get('target_year', False):
            return ctx.get('target_year')

    def default_target_month(self):
        ctx = self._context.copy()
        if ctx.get('target_month', False):
            return ctx.get('target_month')

    target_year = fields.Selection([(num, str(num)) for num in range(datetime.now().year - 5, datetime.now().year + 30)],
                                    string='年份', default=default_target_year)
    target_month = fields.Selection(
        [('1', '一月'), ('2', '二月'), ('3', '三月'), ('4', '四月'), ('5', '五月'), ('6', '六月'), ('7', '七月'), ('8', '八月'),
         ('9', '九月'), ('10', '十月'), ('11', '十一月'), ('12', '十二月')], string='月份', default=default_target_month)
    target_amount = fields.Integer('门店目标')
    jiesuan_amount = fields.Integer('结算小计')

    @api.depends('target_year', 'target_month', 'kunnr', 'ywy')
    def _compute_jiesuan_amount(self):
        for rec in self:
            if rec.kunnr:
                kunnr_sql = "and kunnr = %s" % rec.kunnr.id
            else:
                kunnr_sql = ''
            if rec.ywy:
                ywy_sql = "and ywy = '%s'" % rec.ywy.id
            else:
                ywy_sql = ""
            if rec.target_month:
                month = '%02d' % int(rec.target_month)
                time_sql = "TO_CHAR(\"LFADT\", 'YYYYMM') = '%s'" % (str(rec.target_year) + str(month))
                sql_str = "select * from outbound_final where %s %s %s" % (time_sql, kunnr_sql, ywy_sql)
            else:
                time_sql = "TO_CHAR(\"LFADT\", 'YYYY') = '%s'" % (str(rec.target_year))
                sql_str = "select * from outbound_final where %s %s %s" % (time_sql, kunnr_sql, ywy_sql)
            rec._cr.execute(sql_str)
            res_amount = rec._cr.dictfetchall()
            jiesuan_amount = 0
            if res_amount:
                for res in res_amount:
                    jiesuan_amount += res['jiesuanjine']
            rec.jiesuan_amount = jiesuan_amount
    # 获取查询视图的view_id,在js中访问该方法获取指定该视图id
    @api.model
    def get_view_id(self):
        query_view = self.env.ref('outbound_report.view_target_completion_query_report')
        query_view_id = query_view.id
        return query_view_id

    def get_jiesuan_amount(self, ctx):
        kunnr_sql = "and kunnr = %s" % str(ctx['kunnr'][0])
        if ctx['ywy']:
            ywy_sql = "and ywy = %s" % ctx['ywy'][0]
        else:
            ywy_sql = ""
        if ctx['target_month']:
            month = '%02d' % int(ctx['target_month'])
            time_sql = "TO_CHAR(\"LFADT\", 'YYYYMM') = '%s'" % (str(ctx['target_year'])+str(month))
            sql_str = "select * from outbound_final where %s %s %s" % (time_sql, kunnr_sql, ywy_sql)
        else:
            time_sql = "TO_CHAR(\"LFADT\", 'YYYY') = '%s'" % (str(ctx['target_year']))
            sql_str = "select * from outbound_final where %s %s %s" % (time_sql, kunnr_sql, ywy_sql)
        self._cr.execute(sql_str)
        res_amount = self._cr.dictfetchall()
        jiesuan_amount = 0
        if res_amount:
            for res in res_amount:
                jiesuan_amount += res['jiesuanjine']
        ctx['jiesuan_amount'] = jiesuan_amount
        return ctx['jiesuan_amount']

    def open_target_table(self):
        data = self.read()[0]
        ctx = self._context.copy()
        # 获取视图的id,return时返回指定视图
        tree_view = self.env.ref('outbound_report.target_completion_report_tree_view')
        graph_view = self.env.ref('outbound_report.target_completion_report_graph_view')

        ctx['target_year'] = data['target_year']
        ctx['target_month'] = data['target_month']
        ctx['kunnr'] = data['kunnr']
        ctx['ywy'] = data['ywy']
        ctx['werks'] = data['werks']
        ctx['vtweg'] = data['vtweg']
        ctx['vkorgtext'] = data['vkorgtext']
        # 获取门店目标数据
        if ctx['ywy']:
            ywy = ctx['ywy'][0]
        else:
            ywy = ctx['ywy']
        target_detail = self.env['team.target.detail'].search([('detail_year', '=', ctx['target_year']),
                                                               ('target_month', '=?', ctx['target_month']),
                                                               ('current_team_id', '=', ctx['kunnr'][0]),
                                                               ('sales_member.id', '=?', ywy)])
        target_amount = 0
        if target_detail:
            for detail in target_detail:
                target_amount += detail.team_target_monthly
        ctx['target_amount'] = target_amount
        ctx['new_view'] = 1
        # 获取销售金额数据
        self.get_jiesuan_amount(ctx)

        return {
            'name': '目标完成占比报表',
            # 'view_type': 'dashboard',
            'view_type': 'form',
            # 'view_mode': 'dashboard',
            'view_mode': 'tree,graph',
            'res_model': 'outbound.final',
            'type': 'ir.actions.act_window',
            'context': ctx,
            # 实现视图重定向
            'views': [[tree_view.id, 'tree'],
                      [graph_view.id, 'graph']],
        }

    def open_target_table2(self):
        data = self.read()[0]
        ctx = self._context.copy()
        tree_view = self.env.ref('outbound_report.target_completion_report_tree_view')
        graph_view = self.env.ref('outbound_report.target_completion_report_graph_view')
        ctx['werks'] = data['werks']
        ctx['vtweg'] = data['vtweg']
        ctx['vkorgtext'] = data['vkorgtext']
        ctx['kunnr'] = data['kunnr']
        ctx['ywy'] = data['ywy']
        domain_list = []
        if ctx['werks'] and ctx['werks'] != '0000':
            werks_query = ('werks', '=', ctx['werks'])
            domain_list.append(werks_query)
        if ctx['kunnr']:
            kunnr_query = ('kunnr', '=', ctx['kunnr'][0])
            domain_list.append(kunnr_query)
        if ctx['ywy']:
            ywy_query = ('ywy', '=', ctx['ywy'][0])
            domain_list.append(ywy_query)
        return {
            'name': '目标完成占比报表',
            # 'view_type': 'dashboard',
            'view_type': 'form',
            # 'view_mode': 'dashboard',
            'view_mode': 'tree,graph',
            'res_model': 'outbound.final',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'domain': domain_list,
            # 实现视图重定向
            'views': [[tree_view.id, 'tree'],
                      [graph_view.id, 'graph']],
                }