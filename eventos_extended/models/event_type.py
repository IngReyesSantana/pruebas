# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class EventType(models.Model):
    _name = 'event.type'
    _description = 'Event Type'

    name = fields.Char('Name')
    active = fields.Boolean('Active')


