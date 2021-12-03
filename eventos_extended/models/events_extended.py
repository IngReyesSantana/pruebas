# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime


class EventsExtended(models.Model):
    _name = 'events.extended'
    _description = 'Events Extended'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Event', required=True, readonly=True, default='New', copy=False)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    date_begin = fields.Datetime('Date Begin')
    date_end = fields.Datetime('Date End')
    catering = fields.Boolean('Catering')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    move = fields.Integer(string='Move', default='')
    time = fields.Char(string='Time', compute='_compute_time')
    user_id = fields.Many2one('res.users', 'Responsible', required=True)
    hall_id = fields.Many2one('event.hall', 'Hall', required=True)
    type_id = fields.Many2one('event.type', 'Type', required=True)
    description = fields.Char('Description')
    qty_chair = fields.Integer()
    qty_desk = fields.Integer()
    events_extended_ids = fields.One2many(comodel_name='events.extended.line', inverse_name='events_extended_id',
                                          string='Events')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete', 'Complete'),
        ('done', 'Invoiced'),
        ('cancel', 'Cancel')],
        string='State', default='draft', copy=False, tracking=True, group_expand='_expand_groups')

    @api.model
    def _expand_groups(self, states, domain, order):
        return ['draft', 'complete', 'done', 'cancel']

    @api.onchange('date_begin', 'date_end')
    def _compute_time(self):
        if self.date_begin and self.date_end:
            begin = datetime.time(self.date_begin)
            end = self.date_end - timedelta(hours=begin.hour)
            end = end - timedelta(minutes=begin.minute)
            self.update({
                'time': end.strftime("%H:%M"),
            })

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('events.extended') or '/'
        return super(EventsExtended, self).create(vals)

    def action_view_move(self):
        action = self.env.ref('account.action_move_out_invoice_type').sudo()
        result = action.read()[0]
        if self.state == 'done':
            result['domain'] = [('id', '=', self.move)]
        return result

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_post(self):
        if self.env.user.has_group('eventos_extended.group_approved'):
            move = self._create_invoices()
            self.write({
                'state': 'done',
                'move': move.id,
            })
        else:
            raise ValidationError(
                _("You do not have permissions to carry out this process"))

    def _prepare_invoice(self):
        self.ensure_one()
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise ValidationError(
                _('Please define an accounting sales journal for the company %s (%s).') % (
                    self.company_id.name, self.company_id.id))
        invoice_vals = {
            'ref': self.name or '',
            'move_type': 'out_invoice',
            'payment_reference': self.name or '',
            'currency_id': self.company_id.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'partner_id': self.partner_id.id,
            'journal_id': journal.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [(0, 0, {
                'price_unit': self.events_extended_ids.product_id.list_price,
                'quantity': 1.0,
                'product_id': self.events_extended_ids.product_id.id,
            })],
            'company_id': self.company_id.id,
        }
        return invoice_vals

    def _get_invoiceable_lines(self, final=False):
        invoiceable_line_ids = []
        for line in self.events_extended_ids:
            if line.product_id:
                invoiceable_line_ids.append(line.id)
                continue
        return self.env['events.extended.line'].browse(invoiceable_line_ids)

    def _create_invoices(self, grouped=False, final=False, date=None):
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except:
                return self.env['account.move']
        invoice_vals_list = []
        for order in self:
            order = order.with_company(order.company_id)
            invoice_vals = order._prepare_invoice()
            invoice_line_vals = []
            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)
        if not invoice_vals_list:
            raise self._nothing_to_invoice_error()

        # 3) Create invoices.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['events.extended.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence,
                                                                                   old=line[2]['sequence'])
                    sequence += 1
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        return moves

    def action_complete(self):
        self.write({
            'state': 'complete',
        })

    def action_done(self):
        self.write({
            'state': 'done',
        })

    def action_cancel(self):
        self.write({'state': 'cancel'})


class EventsExtendedLine(models.Model):
    _name = 'events.extended.line'
    _description = 'Events Extended Line'

    product_id = fields.Many2one('product.template', string='Product', domain="[('type', '=', 'service')]")
    product_amount = fields.Float(string='Amount')
    events_extended_id = fields.Many2one('events.extended', string='Events Line')
    invoice_lines = fields.Many2many('account.move.line', string='Invoice Lines', copy=False)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.update({
                'product_amount': self.product_id.list_price,
            })

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        res = {
            'product_id': self.product_id.id,
        }
        if optional_values:
            res.update(optional_values)
        return res
