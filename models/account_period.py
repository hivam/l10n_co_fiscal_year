# -*- coding: utf-8 -*-
##############################################################################
# Hereda el modulo res.parner y se agregan los campo para la localizacion colombiana
# Inherits res.parner module and add the field to the Colombian location
##############################################################################
import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp
import json
import logging

import datetime
import calendar
from datetime import datetime, timedelta, date
from openerp.http import request
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)

class account_period(models.Model):
	_name = "account.period"
	_description = "Account period"
	_order = "date_start, special desc"

	name = fields.Char('Period Name', required=True)
	code = fields.Char('Code', size=12)
	special = fields.Boolean('Opening/Closing Period',help="These periods can overlap.")
	date_start = fields.Date('Start of Period', required=True, states={'done':[('readonly',True)]})
	date_stop = fields.Date('End of Period', required=True, states={'done':[('readonly',True)]})
	fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal Year', required=True)
	state = fields.Selection([('draft','Abierto'), ('done','Cerrado')], 'Status', default='draft')
	company_id = fields.Many2one('res.company', 'Company', required=True, default = lambda self: self.env.user.company_id.id)

   
  
	def find(self, dt=None, exception=True, context=None):
		res = self.finds(dt, exception, context=context)
		return res and res[0] or False

	def finds(self,dt=None, exception=True, context=None):
		if context is None: context = {}
		if not dt:			
			dt = fields.Date.context_today(self)

			
		args = [('date_start', '<=' ,dt), ('date_stop', '>=', dt)]
		if context.get('company_id', False):
			company_id = context['company_id']
		else:
			company_id = self.env['res.users'].browse(self.env.uid).company_id.id
		args.append(('company_id', '=', company_id))

		_logger.info("args")
		_logger.info(args)

		ids = self.search(args)
		if not ids:
			if exception:
				raise ValidationError(_('No esta definido el año fiscal para esta fecha.\nPor favor cree uno desde la configuración del menú contabilidad.'))
			else:
				return []  
		return ids  
	"""_sql_constraints = [
		('name_company_uniq', 'unique(name, company_id)', 'The name of the period must be unique per company!'),
	]

	def _check_duration(self,cr,uid,ids,context=None):
		obj_period = self.browse(cr, uid, ids[0], context=context)
		if obj_period.date_stop < obj_period.date_start:
			return False
		return True

	def _check_year_limit(self,cr,uid,ids,context=None):
		for obj_period in self.browse(cr, uid, ids, context=context):
			if obj_period.special:
				continue

			if obj_period.fiscalyear_id.date_stop < obj_period.date_stop or \
			   obj_period.fiscalyear_id.date_stop < obj_period.date_start or \
			   obj_period.fiscalyear_id.date_start > obj_period.date_start or \
			   obj_period.fiscalyear_id.date_start > obj_period.date_stop:
				return False

			pids = self.search(cr, uid, [('date_stop','>=',obj_period.date_start),('date_start','<=',obj_period.date_stop),('special','=',False),('id','<>',obj_period.id)])
			for period in self.browse(cr, uid, pids):
				if period.fiscalyear_id.company_id.id==obj_period.fiscalyear_id.company_id.id:
					return False
		return True

	_constraints = [
		(_check_duration, 'Error!\nThe duration of the Period(s) is/are invalid.', ['date_stop']),
		(_check_year_limit, 'Error!\nThe period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the fiscal year.', ['date_stop'])
	]

	@api.returns('self')
	def next(self, cr, uid, period, step, context=None):
		ids = self.search(cr, uid, [('date_start','>',period.date_start)])
		if len(ids)>=step:
			return ids[step-1]
		return False

	@api.returns('self')
	def find(self, cr, uid, dt=None, context=None):
		if context is None: context = {}
		if not dt:
			dt = fields.date.context_today(self, cr, uid, context=context)
		args = [('date_start', '<=' ,dt), ('date_stop', '>=', dt)]
		if context.get('company_id', False):
			args.append(('company_id', '=', context['company_id']))
		else:
			company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
			args.append(('company_id', '=', company_id))
		result = []
		if context.get('account_period_prefer_normal', True):
			# look for non-special periods first, and fallback to all if no result is found
			result = self.search(cr, uid, args + [('special', '=', False)], context=context)
		if not result:
			result = self.search(cr, uid, args, context=context)
		if not result:
			model, action_id = self.pool['ir.model.data'].get_object_reference(cr, uid, 'account', 'action_account_period')
			msg = _('There is no period defined for this date: %s.\nPlease go to Configuration/Periods.') % dt
			raise openerp.exceptions.RedirectWarning(msg, action_id, _('Go to the configuration panel'))
		return result

	def action_draft(self, cr, uid, ids, context=None):
		mode = 'draft'
		for period in self.browse(cr, uid, ids):
			if period.fiscalyear_id.state == 'done':
				raise osv.except_osv(_('Warning!'), _('You can not re-open a period which belongs to closed fiscal year'))
		cr.execute('update account_journal_period set state=%s where period_id in %s', (mode, tuple(ids),))
		cr.execute('update account_period set state=%s where id in %s', (mode, tuple(ids),))
		self.invalidate_cache(cr, uid, context=context)
		return True

	def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
		if args is None:
			args = []
		if operator in expression.NEGATIVE_TERM_OPERATORS:
			domain = [('code', operator, name), ('name', operator, name)]
		else:
			domain = ['|', ('code', operator, name), ('name', operator, name)]
		ids = self.search(cr, user, expression.AND([domain, args]), limit=limit, context=context)
		return self.name_get(cr, user, ids, context=context)

	def write(self, cr, uid, ids, vals, context=None):
		if 'company_id' in vals:
			move_lines = self.pool.get('account.move.line').search(cr, uid, [('period_id', 'in', ids)])
			if move_lines:
				raise osv.except_osv(_('Warning!'), _('This journal already contains items for this period, therefore you cannot modify its company field.'))
		return super(account_period, self).write(cr, uid, ids, vals, context=context)

	def build_ctx_periods(self, cr, uid, period_from_id, period_to_id):
		if period_from_id == period_to_id:
			return [period_from_id]
		period_from = self.browse(cr, uid, period_from_id)
		period_date_start = period_from.date_start
		company1_id = period_from.company_id.id
		period_to = self.browse(cr, uid, period_to_id)
		period_date_stop = period_to.date_stop
		company2_id = period_to.company_id.id
		if company1_id != company2_id:
			raise osv.except_osv(_('Error!'), _('You should choose the periods that belong to the same company.'))
		if period_date_start > period_date_stop:
			raise osv.except_osv(_('Error!'), _('Start period should precede then end period.'))

		# /!\ We do not include a criterion on the company_id field below, to allow producing consolidated reports
		# on multiple companies. It will only work when start/end periods are selected and no fiscal year is chosen.

		#for period from = january, we want to exclude the opening period (but it has same date_from, so we have to check if period_from is special or not to include that clause or not in the search).
		if period_from.special:
			return self.search(cr, uid, [('date_start', '>=', period_date_start), ('date_stop', '<=', period_date_stop)])
		return self.search(cr, uid, [('date_start', '>=', period_date_start), ('date_stop', '<=', period_date_stop), ('special', '=', False)])"""