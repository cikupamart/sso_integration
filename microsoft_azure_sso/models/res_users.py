# -*- coding: utf-8 -*-
import random
import string

from odoo import models, fields, api
from odoo.exceptions import AccessDenied

SSO_TOKEN_VALIDITY_SECONDS = 60


class ResUsers(models.Model):
    _inherit = 'res.users'

    azure_ad_oid = fields.Char(
        string='Azure AD Object ID', copy=False, readonly=True,
        help='Unique identifier of this user in Microsoft Azure Active Directory.',
    )
    azure_email = fields.Char(
        string='Azure AD Email', copy=False, readonly=True,
    )
    sso_login_enabled = fields.Boolean(
        string='Allow Microsoft SSO Login', default=True,
        help='Untick to prevent this user from logging in with Microsoft SSO, '
             'even if the feature is enabled globally.',
    )
    sso_temp_token = fields.Char(string='SSO Temporary Token', copy=False)
    sso_temp_token_expiry = fields.Datetime(string='SSO Token Expiry', copy=False)
    sso_last_login = fields.Datetime(string='Last Microsoft SSO Login', copy=False)
    sso_login_count = fields.Integer(string='Microsoft SSO Login Count', default=0, copy=False)

    def _generate_sso_token(self):
        """Generate a short-lived, single-use token used to complete the
        Odoo web session authentication after a successful Microsoft
        Azure AD login. The token is consumed (and destroyed) the first
        time it is checked, whether it succeeds or not.
        """
        self.ensure_one()
        token = ''.join(
            random.SystemRandom().choice(string.ascii_letters + string.digits)
            for _ in range(40)
        )
        self.sudo().write({
            'sso_temp_token': token,
            'sso_temp_token_expiry': fields.Datetime.now() + fields.Timedelta(
                seconds=SSO_TOKEN_VALIDITY_SECONDS),
        })
        return token

    def _check_credentials(self, credential, env):
        """Extend password check so a valid, non-expired one-time SSO
        token is accepted in place of the real password. This lets the
        Microsoft SSO controller complete a normal Odoo web session
        without ever knowing (or setting) the user's real password.
        """
        try:
            return super()._check_credentials(credential, env)
        except AccessDenied:
            password = credential.get('password') if isinstance(credential, dict) else credential
            self.env.cr.execute(
                'SELECT id, sso_temp_token, sso_temp_token_expiry FROM res_users WHERE id = %s',
                (self.env.uid,),
            )
            row = self.env.cr.dictfetchone()
            if (
                row and password and row.get('sso_temp_token')
                and password == row['sso_temp_token']
                and row.get('sso_temp_token_expiry')
                and row['sso_temp_token_expiry'] >= fields.Datetime.now()
            ):
                self.sudo().browse(row['id']).write({
                    'sso_temp_token': False,
                    'sso_temp_token_expiry': False,
                })
                return
            raise
