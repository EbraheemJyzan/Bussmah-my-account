# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    background_image = fields.Binary(string="Background image",
                                     attachment=True,
                                     help="Add Background image")
    background_login = fields.Image(string="Background Login")
    image_login = fields.Image(string="Image Login")
    image_theam = fields.Image(string="Image Theam")
