{
    'name': 'Hijri & Gregorian Date Widget (Odoo 18)',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Professional OWL widget to select and display Hijri or Gregorian dates, saving as Gregorian in the database.',
    'description': """
Hijri Date Widget for Odoo 18
=============================
This module introduces a highly custom, modern, and timezone-safe OWL widget (`hijri_date`) 
for both standard Date and DateTime fields.

Key Features:
-------------
* **Dual Calendar Interface:** Switch between Hijri (Umm al-Qura) and Gregorian calendars instantly.
* **Instant Conversions:** Shows the real-time Gregorian counterpart when in Hijri mode and vice-versa.
* **OWL 18 Support:** Engineered using native Odoo 18 OWL component paradigms and Luxon integration.
* **Database Accuracy:** Saves the date natively as a Gregorian value in the database, ensuring compatibility with all reports, search queries, and backend calculations.
* **Premium Design:** Clean, native-looking UI with responsive dropdown inputs, slide-up panels on mobile, and smooth hover micro-animations.
* **Readonly formatting:** Displays both Gregorian and Hijri values side-by-side (e.g. 2026-05-24 | 11/07/1447) in readonly mode for enhanced corporate readability.
    """,
    'author': 'bst-inn, Amro00743',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'assets': {
        'web.assets_backend': [
            'bussmah_hijri_date/static/src/scss/hijri_date_widget.scss',
            'bussmah_hijri_date/static/src/js/hijri_date_widget.js',
            'bussmah_hijri_date/static/src/xml/hijri_date_widget.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
