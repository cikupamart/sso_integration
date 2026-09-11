# -*- coding: utf-8 -*-
import base64
import logging
import secrets
import urllib.parse

import requests
import werkzeug

from odoo import http, fields, SUPERUSER_ID
from odoo.http import request

_logger = logging.getLogger(__name__)

AUTHORIZE_URL = 'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize'
TOKEN_URL = 'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token'
GRAPH_ME_URL = 'https://graph.microsoft.com/v1.0/me'
DEFAULT_SCOPE = 'openid profile email User.Read'


class MicrosoftSsoController(http.Controller):

    def _get_param(self, key, default=False):
        return request.env['ir.config_parameter'].sudo().get_param(key, default)

    # ------------------------------------------------------------------
    # Login theme background image (served publicly, bypassing ACL,
    # since this must be visible on the login page before authentication)
    # ------------------------------------------------------------------
    @http.route('/microsoft_sso/theme_background_image', type='http', auth='public', csrf=False)
    def theme_background_image(self, **kw):
        theme = request.env['sso.login.theme'].sudo()._get_active_theme()
        if not theme or not theme.background_image:
            return request.not_found()
        try:
            data = base64.b64decode(theme.background_image)
        except Exception:
            return request.not_found()
        headers = [
            ('Content-Type', 'image/png'),
            ('Cache-Control', 'public, max-age=3600'),
        ]
        return request.make_response(data, headers=headers)

    def _sso_settings(self):
        get = self._get_param
        return {
            'enabled': get('microsoft_azure_sso.enabled') in ('True', '1', 'true'),
            'client_id': get('microsoft_azure_sso.client_id'),
            'client_secret': get('microsoft_azure_sso.client_secret'),
            'tenant_id': get('microsoft_azure_sso.tenant_id') or 'common',
            'auto_create_user': get('microsoft_azure_sso.auto_create_user') in ('True', '1', 'true'),
            'notify_user_on_login': get('microsoft_azure_sso.notify_user_on_login', 'True') in ('True', '1', 'true'),
            'notify_admin_on_failure': get('microsoft_azure_sso.notify_admin_on_failure', 'True') in ('True', '1', 'true'),
        }

    def _redirect_uri(self):
        base_url = self._get_param('web.base.url')
        return f'{base_url}/microsoft_sso/callback'

    # ------------------------------------------------------------------
    # Step 1: redirect the browser to Microsoft's login page
    # ------------------------------------------------------------------
    @http.route('/microsoft_sso/login', type='http', auth='public', csrf=False)
    def microsoft_sso_login(self, redirect='/web', **kw):
        settings = self._sso_settings()
        if not settings['enabled'] or not settings['client_id']:
            return request.redirect('/web/login?sso_error=Microsoft SSO is not configured')

        state = secrets.token_urlsafe(24)
        request.session['microsoft_sso_state'] = state
        request.session['microsoft_sso_redirect'] = redirect or '/web'

        params = {
            'client_id': settings['client_id'],
            'response_type': 'code',
            'redirect_uri': self._redirect_uri(),
            'response_mode': 'query',
            'scope': DEFAULT_SCOPE,
            'state': state,
        }
        url = AUTHORIZE_URL.format(tenant=settings['tenant_id']) + '?' + urllib.parse.urlencode(params)
        return request.redirect(url, local=False)

    # ------------------------------------------------------------------
    # Step 2: Microsoft redirects back here with an authorization code
    # ------------------------------------------------------------------
    @http.route('/microsoft_sso/callback', type='http', auth='public', csrf=False)
    def microsoft_sso_callback(self, code=None, state=None, error=None,
                                error_description=None, **kw):
        AuditLog = request.env['sso.audit.log']
        settings = self._sso_settings()
        expected_state = request.session.pop('microsoft_sso_state', None)
        redirect_to = request.session.pop('microsoft_sso_redirect', '/web')

        if error:
            AuditLog.log_event(status='failed', error_message=error_description or error,
                                request=request)
            self._notify_admins_on_failure(settings, error_description or error)
            return request.redirect(
                '/web/login?sso_error=' + urllib.parse.quote(error_description or error))

        if not code or not state or state != expected_state:
            AuditLog.log_event(status='failed', error_message='Invalid or missing OAuth state/code',
                                request=request)
            self._notify_admins_on_failure(settings, 'Invalid or missing OAuth state/code')
            return request.redirect('/web/login?sso_error=Invalid authentication response')

        try:
            token_resp = requests.post(
                TOKEN_URL.format(tenant=settings['tenant_id']),
                data={
                    'client_id': settings['client_id'],
                    'client_secret': settings['client_secret'],
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': self._redirect_uri(),
                    'scope': DEFAULT_SCOPE,
                },
                timeout=15,
            )
            token_resp.raise_for_status()
            token_data = token_resp.json()
            access_token = token_data['access_token']

            profile_resp = requests.get(
                GRAPH_ME_URL,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=15,
            )
            profile_resp.raise_for_status()
            profile = profile_resp.json()
        except Exception as exc:  # noqa: BLE001
            _logger.exception('Microsoft SSO: error during token exchange / profile fetch')
            AuditLog.log_event(status='failed', error_message=str(exc), request=request)
            self._notify_admins_on_failure(settings, str(exc))
            return request.redirect('/web/login?sso_error=Could not reach Microsoft. Please try again.')

        azure_oid = profile.get('id')
        email = (profile.get('mail') or profile.get('userPrincipalName') or '').lower()

        if not email:
            AuditLog.log_event(status='failed', azure_ad_oid=azure_oid,
                                error_message='Microsoft account has no email/UPN', request=request)
            self._notify_admins_on_failure(settings, 'Microsoft account has no email/UPN')
            return request.redirect('/web/login?sso_error=Your Microsoft account has no email address')

        env = request.env(user=SUPERUSER_ID)
        user = env['res.users'].sudo().search([('login', '=', email)], limit=1)
        if not user:
            user = env['res.users'].sudo().search([('azure_email', '=', email)], limit=1)

        if not user and settings['auto_create_user']:
            user = env['res.users'].sudo().create({
                'name': profile.get('displayName') or email,
                'login': email,
                'email': email,
                'azure_email': email,
                'azure_ad_oid': azure_oid,
                'groups_id': [(4, env.ref('base.group_user').id)],
            })

        if not user:
            AuditLog.log_event(azure_email=email, azure_ad_oid=azure_oid, status='failed',
                                error_message='No matching Odoo user and auto-create is disabled',
                                request=request)
            self._notify_admins_on_failure(settings, f'No matching Odoo user for {email}')
            return request.redirect('/web/login?sso_error=No Odoo account is associated with your Microsoft account')

        if not user.active or not user.sso_login_enabled:
            AuditLog.log_event(user=user, azure_email=email, azure_ad_oid=azure_oid, status='failed',
                                error_message='User inactive or SSO disabled for this user',
                                request=request)
            self._notify_admins_on_failure(settings, f'Blocked SSO login attempt for {email}')
            return request.redirect('/web/login?sso_error=This account is not allowed to use Microsoft SSO')

        # Keep the Azure identity in sync and complete the Odoo session.
        user.sudo().write({
            'azure_ad_oid': azure_oid,
            'azure_email': email,
            'sso_last_login': fields.Datetime.now(),
            'sso_login_count': user.sso_login_count + 1,
        })
        token = user.sudo()._generate_sso_token()

        try:
            credential = {'login': user.login, 'password': token, 'type': 'password'}
            request.session.authenticate(request.db, credential)
        except Exception as exc:  # noqa: BLE001
            _logger.exception('Microsoft SSO: failed to open Odoo session')
            AuditLog.log_event(user=user, azure_email=email, azure_ad_oid=azure_oid, status='failed',
                                error_message=f'Session authentication failed: {exc}', request=request)
            self._notify_admins_on_failure(settings, str(exc))
            return request.redirect('/web/login?sso_error=Login failed while opening your session')

        AuditLog.log_event(user=user, azure_email=email, azure_ad_oid=azure_oid, status='success',
                            request=request)
        self._notify_user_on_success(settings, user)

        return request.redirect(redirect_to or '/web')

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------
    def _notify_user_on_success(self, settings, user):
        if not settings.get('notify_user_on_login'):
            return
        try:
            request.env['bus.bus']._sendone(
                user.partner_id,
                'simple_notification',
                {
                    'title': 'Microsoft SSO Login',
                    'message': 'You have successfully signed in with your Microsoft account.',
                    'type': 'success',
                    'sticky': False,
                },
            )
        except Exception:  # noqa: BLE001
            _logger.warning('Microsoft SSO: could not send login notification', exc_info=True)

    def _notify_admins_on_failure(self, settings, error_message):
        if not settings.get('notify_admin_on_failure'):
            return
        try:
            env = request.env(user=SUPERUSER_ID)
            admin_group = env.ref('microsoft_azure_sso.group_sso_admin', raise_if_not_found=False)
            partners = admin_group.users.mapped('partner_id') if admin_group else env['res.partner']
            if not partners:
                return
            env['mail.mail'].sudo().create({
                'subject': 'Microsoft SSO: Failed login attempt',
                'body_html': f'<p>A Microsoft SSO login attempt failed.</p><p><b>Reason:</b> {werkzeug.utils.escape(error_message)}</p>',
                'recipient_ids': [(6, 0, partners.ids)],
            }).send()
        except Exception:  # noqa: BLE001
            _logger.warning('Microsoft SSO: could not send admin failure notification', exc_info=True)
