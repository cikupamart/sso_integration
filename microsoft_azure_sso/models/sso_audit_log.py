# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SsoAuditLog(models.Model):
    _name = 'sso.audit.log'
    _description = 'Microsoft SSO Audit Log'
    _order = 'login_date desc'
    _rec_name = 'azure_email'

    user_id = fields.Many2one('res.users', string='Odoo User', ondelete='set null', index=True)
    azure_email = fields.Char(string='Microsoft Account Email', index=True)
    azure_ad_oid = fields.Char(string='Azure AD Object ID')
    login_date = fields.Datetime(string='Date/Time', default=fields.Datetime.now, required=True, index=True)
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Status', required=True, default='success', index=True)
    error_message = fields.Text(string='Error Message')
    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Char(string='User Agent')
    company_id = fields.Many2one('res.company', string='Company',
                                  default=lambda self: self.env.company)

    @api.model
    def log_event(self, user=None, azure_email=None, azure_ad_oid=None,
                   status='success', error_message=None, request=None):
        """Convenience helper to create an audit log entry from the
        controller. ``request`` is the Odoo http request object, used to
        capture the caller's IP address and user agent.
        """
        ip_address = user_agent = False
        if request is not None:
            try:
                ip_address = request.httprequest.remote_addr
                user_agent = request.httprequest.user_agent and str(request.httprequest.user_agent)
            except Exception:
                pass
        vals = {
            'user_id': user.id if user else False,
            'azure_email': azure_email,
            'azure_ad_oid': azure_ad_oid,
            'status': status,
            'error_message': error_message,
            'ip_address': ip_address,
            'user_agent': user_agent,
        }
        return self.sudo().create(vals)
