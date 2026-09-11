# -*- coding: utf-8 -*-
{
    'name': 'Microsoft Azure SSO Integration',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Login to Odoo with Microsoft Azure AD (Single Sign-On)',
        'price': 29.99,
    'currency': 'EUR',

    'description': """
Microsoft Azure SSO Integration
================================
Adds Microsoft Azure Active Directory (Entra ID) Single Sign-On to Odoo.

Features
--------
* Microsoft Single Sign-On (SSO) Login (OAuth2 / Authorization Code flow)
* No need to remember new credentials - users log in with their Microsoft account
* Microsoft SSO Login Notifications (toast on success, email alert to admins on failure)
* Microsoft SSO Audit Logs & Audit Log Tracking (who, when, from where, success/failure)
* Microsoft SSO Dashboard with login statistics
* Custom Login Theme - modern, flexible login page styling (background color/gradient/image,
  accent color, card radius & shadow, custom welcome text, quick presets, and raw CSS override)
* Configurable from Settings > General Settings
""",
    'author': 'Custom Development',
    'website': '',
    'license': 'LGPL-3',
    'images': [
        'images/main_screenshot.png',
        'images/dashboard_screenshot.png',
    ],
    'depends': ['base', 'web', 'mail', 'base_setup'],
    'data': [
        'security/sso_security.xml',
        'security/ir.model.access.csv',
        'data/sso_login_theme_data.xml',
        'views/res_config_settings_views.xml',
        'views/sso_audit_log_views.xml',
        'views/sso_dashboard_views.xml',
        'views/sso_login_theme_views.xml',
        'views/menu_views.xml',
        'views/login_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'microsoft_azure_sso/static/src/js/sso_dashboard.js',
            'microsoft_azure_sso/static/src/js/sso_help.js',
            'microsoft_azure_sso/static/src/xml/sso_dashboard_templates.xml',
            'microsoft_azure_sso/static/src/xml/sso_help_templates.xml',
            'microsoft_azure_sso/static/src/scss/sso_dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
