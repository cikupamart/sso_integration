# -*- coding: utf-8 -*-
{
    'name': 'Microsoft Azure SSO Integration',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Login to Odoo with Microsoft Azure AD (Single Sign-On)',
    'price': 20.99,
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
* Configurable from Settings > General Settings
<<<<<<< HEAD
=======
Login ke Odoo menggunakan akun Microsoft (Azure AD / Entra ID) via OAuth2, lengkap dengan
audit log, notifikasi, dan dashboard.

## Fitur
- **Microsoft SSO Login** – tombol "Login with Microsoft" di halaman login Odoo.
- **No need to remember new credentials** – user cukup login dengan akun Microsoft mereka.
- **Microsoft SSO Login Notifications** – toast notification ke user saat login berhasil,
  dan email ke admin saat percobaan login gagal (bisa diaktif/nonaktifkan).
- **Microsoft SSO Audit Logs & Tracking** – setiap percobaan login (sukses/gagal) dicatat:
  waktu, email Azure, user Odoo, IP address, user agent, pesan error.
- **Microsoft SSO Dashboard** – ringkasan statistik login (total, sukses, gagal, unique user)
  plus daftar login terbaru.

## Instalasi
1. Copy folder `microsoft_azure_sso` ke direktori addons Odoo 18 Anda.
2. Update Apps List, lalu install module **Microsoft Azure SSO Integration**.
3. `pip install requests` (biasanya sudah tersedia di environment Odoo).

## Konfigurasi Azure App Registration
1. Buka [Azure Portal](https://portal.azure.com) → **Azure Active Directory (Entra ID)** →
   **App registrations** → **New registration**.
2. Isi nama app, pilih *supported account types* sesuai kebutuhan (single tenant / multitenant).
3. Pada **Redirect URI**, pilih platform **Web** dan isi:
   `https://<domain-odoo-anda>/microsoft_sso/callback`
   (nilai ini juga ditampilkan otomatis di Settings Odoo setelah client ID diisi).
4. Setelah app dibuat, catat **Application (client) ID** dan **Directory (tenant) ID**.
5. Ke **Certificates & secrets** → **New client secret**, catat nilainya (hanya tampil sekali).
6. Ke **API permissions**, pastikan ada `User.Read` (Microsoft Graph, delegated) — biasanya
   sudah ada secara default.

## Konfigurasi di Odoo
1. Buka **Settings → General Settings**, scroll ke bagian **Microsoft SSO**
   (atau menu **Microsoft SSO → Configuration → Settings**).
2. Aktifkan **Enable Microsoft SSO**.
3. Isi **Application (Client) ID**, **Client Secret**, dan **Directory (Tenant) ID**
   (gunakan `common` untuk mengizinkan akun Microsoft apapun, atau tenant ID Anda untuk
   membatasi hanya organisasi Anda).
4. (Opsional) Aktifkan **Auto-create Users** agar user baru otomatis dibuat saat pertama
   kali login dengan akun Microsoft yang belum terdaftar.
5. Atur notifikasi sesuai kebutuhan.
6. Simpan. Redirect URI yang tampil harus **persis sama** dengan yang didaftarkan di Azure.

## Cara Kerja Login
1. User klik **Login with Microsoft** di halaman login.
2. Odoo redirect ke halaman login Microsoft (`/microsoft_sso/login` → Microsoft authorize URL).
3. Setelah sukses, Microsoft redirect kembali ke `/microsoft_sso/callback` dengan authorization code.
4. Odoo menukar code tersebut dengan access token, mengambil profil user dari Microsoft Graph
   (`/me`), mencocokkan dengan user Odoo (berdasarkan email/login), lalu membuka session Odoo
   secara aman menggunakan token sekali-pakai berumur 60 detik (tidak pernah menyimpan/
   mengetahui password asli user).
5. Setiap percobaan dicatat di **Microsoft SSO → Audit Logs**.

## Catatan Keamanan & Produksi
- Wajib menggunakan HTTPS di production (`web.base.url` harus HTTPS) karena OAuth2
  mengharuskan redirect URI aman.
- Simpan **Client Secret** dengan hati-hati; field ini disimpan sebagai `ir.config_parameter`.
  Untuk keamanan lebih tinggi, pertimbangkan menyimpan secret di environment variable/vault
  dan menyesuaikan `res_config_settings.py`.
- Sebelum go-live, uji ulang pada versi Odoo 18 point-release Anda, khususnya method
  `_check_credentials` dan `request.session.authenticate`, karena API internal Odoo dapat
  sedikit berbeda antar minor release.
- Group **Microsoft SSO Administrator** mengontrol siapa yang bisa mengubah konfigurasi dan
  melihat seluruh audit log; user biasa hanya bisa melihat audit log miliknya sendiri.

>>>>>>> 8bebfabb9aaa9adf8af311cb97565afce2f6ba9c

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
        'views/res_config_settings_views.xml',
        'views/sso_audit_log_views.xml',
        'views/sso_dashboard_views.xml',
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
