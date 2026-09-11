# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import models, fields, api

PRESETS = {
    'midnight': dict(background_type='gradient', gradient_start='#0f1631', gradient_end='#2a3a7a',
                      gradient_angle=135, card_background_color='#ffffff', primary_color='#3b5bdb',
                      text_color='#0f1631'),
    'ocean': dict(background_type='gradient', gradient_start='#005c97', gradient_end='#363795',
                   gradient_angle=120, card_background_color='#ffffff', primary_color='#0090ff',
                   text_color='#0b2545'),
    'sunset': dict(background_type='gradient', gradient_start='#ff512f', gradient_end='#dd2476',
                    gradient_angle=135, card_background_color='#ffffff', primary_color='#ff512f',
                    text_color='#3a0d15'),
    'corporate': dict(background_type='solid', background_color='#f4f6fa', card_background_color='#ffffff',
                       primary_color='#2b3a67', text_color='#2b3a67'),
    'dark': dict(background_type='solid', background_color='#111318', card_background_color='#1c1f26',
                  primary_color='#7c8cff', text_color='#f2f3f7'),
}


class SsoLoginTheme(models.Model):
    _name = 'sso.login.theme'
    _description = 'Microsoft SSO Login Page Theme'

    name = fields.Char(default='Default Theme', required=True)
    active = fields.Boolean(default=True, help='Only the first active theme found is applied to the login page.')

    preset = fields.Selection([
        ('midnight', 'Midnight Blue'),
        ('ocean', 'Ocean'),
        ('sunset', 'Sunset'),
        ('corporate', 'Corporate Light'),
        ('dark', 'Dark Mode'),
    ], string='Quick Preset', help='Pick a preset to instantly fill in the colors below, then fine-tune as needed.')

    # ------------------------------------------------------------------
    # Background
    # ------------------------------------------------------------------
    background_type = fields.Selection([
        ('solid', 'Solid Color'),
        ('gradient', 'Gradient'),
        ('image', 'Image'),
    ], string='Background Type', default='gradient', required=True)
    background_color = fields.Char(string='Background Color', default='#1a2242')
    gradient_start = fields.Char(string='Gradient Start', default='#1a2242')
    gradient_end = fields.Char(string='Gradient End', default='#3a4a8f')
    gradient_angle = fields.Integer(string='Gradient Angle (deg)', default=135)
    background_image = fields.Binary(string='Background Image', attachment=True)
    background_image_filename = fields.Char(string='Background Image Filename')

    # ------------------------------------------------------------------
    # Card
    # ------------------------------------------------------------------
    card_background_color = fields.Char(string='Card Background', default='#ffffff')
    card_radius = fields.Integer(string='Card Corner Radius (px)', default=16)
    card_shadow = fields.Boolean(string='Card Shadow', default=True)

    # ------------------------------------------------------------------
    # Typography / accent
    # ------------------------------------------------------------------
    primary_color = fields.Char(string='Accent / Button Color', default='#0b5ed7')
    text_color = fields.Char(string='Heading Text Color', default='#1a2242')
    font_family = fields.Char(string='Font Family (CSS)', default="'Helvetica Neue', Arial, sans-serif")

    # ------------------------------------------------------------------
    # Copy
    # ------------------------------------------------------------------
    welcome_title = fields.Char(string='Welcome Title', default='Welcome back')
    welcome_subtitle = fields.Char(string='Welcome Subtitle', default='Sign in to continue to your workspace')
    hide_odoo_footer = fields.Boolean(string='Hide "Powered by Odoo" Footer', default=False)

    # ------------------------------------------------------------------
    # Advanced
    # ------------------------------------------------------------------
    custom_css = fields.Text(string='Custom CSS', help='Advanced: raw CSS appended after the generated theme styles.')

    @api.onchange('preset')
    def _onchange_preset(self):
        if self.preset and self.preset in PRESETS:
            self.update(PRESETS[self.preset])

    def action_preview_login(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/login',
            'target': 'new',
        }

    @api.model
    def _get_active_theme(self):
        return self.sudo().search([('active', '=', True)], limit=1)

    @staticmethod
    def _esc_css_string(value):
        """Escape a value so it can be safely embedded inside a CSS
        string literal (content: "...")."""
        if not value:
            return ''
        return str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')

    def _background_css(self):
        self.ensure_one()
        if self.background_type == 'solid':
            return f'background: {self.background_color or "#1a2242"};'
        if self.background_type == 'image' and self.background_image:
            url = '/microsoft_sso/theme_background_image'
            return (f"background-image: url('{url}'); "
                    f"background-size: cover; background-position: center; background-repeat: no-repeat;")
        return (f'background: linear-gradient({self.gradient_angle or 135}deg, '
                f'{self.gradient_start or "#1a2242"} 0%, {self.gradient_end or "#3a4a8f"} 100%);')

    def get_login_css(self):
        """Build the CSS for the login page from the active theme.
        Returns a Markup instance so it can be output un-escaped in QWeb.
        """
        theme = self._get_active_theme()
        if not theme:
            return Markup('')

        radius = theme.card_radius or 16
        input_radius = max(radius // 2, 6)
        title = self._esc_css_string(theme.welcome_title)
        subtitle = self._esc_css_string(theme.welcome_subtitle)

        css = f"""
/* Microsoft SSO Login Theme: {theme.name} */
body.login {{
    {theme._background_css()}
    min-height: 100vh;
}}
body.login .oe_login_form,
body.login .card,
body.login .o_login_card {{
    background: {theme.card_background_color or '#ffffff'} !important;
    border-radius: {radius}px !important;
    border: none !important;
    {'box-shadow: 0 12px 40px rgba(0,0,0,0.25) !important;' if theme.card_shadow else 'box-shadow: none !important;'}
    font-family: {theme.font_family or "inherit"};
    overflow: hidden;
}}
body.login h1, body.login h2, body.login h3, body.login label {{
    color: {theme.text_color or '#1a2242'};
}}
body.login .btn-primary,
body.login input[type='submit'] {{
    background-color: {theme.primary_color or '#0b5ed7'} !important;
    border-color: {theme.primary_color or '#0b5ed7'} !important;
    border-radius: {input_radius}px !important;
}}
body.login a {{
    color: {theme.primary_color or '#0b5ed7'};
}}
body.login input.form-control {{
    border-radius: {input_radius}px;
}}
body.login .oe_login_buttons {{
    margin-top: 8px;
}}
body.login .oe_login_buttons::before {{
    content: "{title}";
    display: {"block" if title else "none"};
    font-size: 20px;
    font-weight: 700;
    color: {theme.text_color or '#1a2242'};
    margin-bottom: 4px;
}}
body.login .oe_login_buttons::after {{
    content: "{subtitle}";
    display: {"block" if subtitle else "none"};
    font-size: 13px;
    color: #8a90a0;
    margin-bottom: 14px;
}}
"""
        if theme.hide_odoo_footer:
            css += """
body.login .o_footer_copyright,
body.login footer {
    display: none !important;
}
"""
        if theme.custom_css:
            css += "\n/* Custom CSS */\n" + theme.custom_css

        return Markup(css)
