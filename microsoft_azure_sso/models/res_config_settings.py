# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    azure_sso_enabled = fields.Boolean(
        string='Enable Microsoft SSO',
        config_parameter='microsoft_azure_sso.enabled',
        help='Show the "Login with Microsoft" button on the login page and '
             'allow authentication through Microsoft Azure AD (Entra ID).',
    )
    azure_client_id = fields.Char(
        string='Application (Client) ID',
        config_parameter='microsoft_azure_sso.client_id',
    )
    azure_client_secret = fields.Char(
        string='Client Secret',
        config_parameter='microsoft_azure_sso.client_secret',
    )
    azure_tenant_id = fields.Char(
        string='Directory (Tenant) ID',
        config_parameter='microsoft_azure_sso.tenant_id',
        help='Use "common" to allow any Microsoft account, or your Azure AD '
             'tenant ID / domain to restrict login to your organization.',
    )
    azure_auto_create_user = fields.Boolean(
        string='Auto-create Users',
        config_parameter='microsoft_azure_sso.auto_create_user',
        help='Automatically create an internal Odoo user the first time '
             'someone signs in with a Microsoft account that matches no '
             'existing user.',
    )
    azure_notify_user_on_login = fields.Boolean(
        string='Notify User on Successful Login',
        config_parameter='microsoft_azure_sso.notify_user_on_login',
        default=True,
    )
    azure_notify_admin_on_failure = fields.Boolean(
        string='Notify Administrators on Failed Login',
        config_parameter='microsoft_azure_sso.notify_admin_on_failure',
        default=True,
    )
    azure_redirect_uri = fields.Char(
        string='Redirect URI',
        compute='_compute_azure_redirect_uri',
        help='Register this exact URL as a "Redirect URI" (Web platform) '
             'on your Azure AD App Registration.',
    )

    @api.depends('azure_client_id')
    def _compute_azure_redirect_uri(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        for rec in self:
            rec.azure_redirect_uri = f'{base_url}/microsoft_sso/callback'
