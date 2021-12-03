# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class EventHall(models.Model):
    _name = 'event.hall'
    _description = 'Event Hall'

    name = fields.Char()
    active = fields.Boolean('Active')
    state = fields.Selection([
        ('available', 'Available'),
        ('in_use', 'In Use')],
        string='State', default='available', copy=False, tracking=True, group_expand='_expand_groups')

    @api.model
    def _expand_groups(self, states, domain, order):
        return ['available', 'in_use']

