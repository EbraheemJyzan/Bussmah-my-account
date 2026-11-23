# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home

try:
    from odoo.addons.auth_signup.controllers.main import AuthSignupHome
except ImportError:
    AuthSignupHome = Home


def _set_company_language():
    # 1. Do not override if user explicitly selected language via URL params or session
    if 'lang' in request.params or 'lang' in request.session:
        return

    # 2. If Website module is installed and active, respect URL language prefixes (e.g. /en/web/login) stored in context
    is_website_installed = hasattr(request, 'website') and bool(request.website)
    if is_website_installed and request.context.get('lang'):
        return

    # 3. Otherwise, set company / website company language
    if is_website_installed and request.website.company_id:
        company = request.website.company_id.sudo()
    else:
        company = request.env.company.sudo() if request.env.company else request.env['res.company'].sudo().search([], limit=1)

    company_lang = company.partner_id.lang if company and company.partner_id else False
    if company_lang:
        request.update_context(lang=company_lang)


def _set_logo_context(response):
    """Pass logo_company to qcontext for template rendering."""
    if response.status_code == 200 and hasattr(response, 'qcontext'):
        company = request.env['res.company'].sudo().search([], limit=1)
        response.qcontext['logo_company'] = company


class WebLogin(Home):

    @http.route([])
    def web_login(self, redirect=None, **kw):
        _set_company_language()
        response = super().web_login(redirect=redirect, **kw)
        _set_logo_context(response)
        return response


class CustomAuthSignupHome(AuthSignupHome):

    @http.route([])
    def web_auth_signup(self, *args, **kw):
        _set_company_language()
        response = super().web_auth_signup(*args, **kw)
        _set_logo_context(response)
        return response

    @http.route([])
    def web_auth_reset_password(self, *args, **kw):
        _set_company_language()
        response = super().web_auth_reset_password(*args, **kw)
        _set_logo_context(response)
        return response