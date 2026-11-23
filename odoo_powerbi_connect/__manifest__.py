# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
##########################################################################

{
    "name": "Odoo Power BI Connector",
    "version": "8.4.2",
    "category": "Marketing",
    "author": "Webkul Software Pvt. Ltd.",
    "website": "https://store.webkul.com/odoo-powerbi-connector.html",
    "live_test_url": "https://odoodemo.webkul.in/?module=odoo_powerbi_connect",
    "sequence": 1,
    "license": "Other proprietary",
    "summary": "Odoo Power BI Connector allows integration of Odoo with Microsoft Power BI. powerbi connector, powerbi dashboard, power bi dashboard, power bi reports, big data, data studio, data alnalytics, microsoft power bi.",
    "description": """

Odoo Power BI Connector
=======================

This module allows you to integrate your PowerBI with Odoo and then you can start synchronizing data between Odoo and PowerBI.
--------------------------------------------------------------------------


Some of the salient features of the connector are:-
--------------------------------------------

    1. Import/Export Workspaces

    2. Export newly created datasets.

    3. Export newly created eventhouses.

    4. Create and Export KQL Databases inside Eventhouse.

    5. Export/Update/Delete any model's data in tables.

    6. Manage relations between tables.

    7. Import power BI reports and view on odoo.

    8. Import power BI dashboards and view on odoo.

    9. Create dynamic server actions for any model.

    10. Configure cron to auto sync data for any model.

This module works very well with latest version of Odoo 18.0
------------------------------------------------------------------------------
    """,
    "depends": [
        "mail"
    ],
    "data": [
        "security/powerbi_connector_security.xml",
        "security/ir.model.access.csv",

        "data/powerbi_sequence.xml",
        "data/powerbi_server_actions.xml",
        "data/powerbi_cron.xml",

        "wizard/powerbi_message_wizard_view.xml",
        "wizard/powerbi_wizard_view.xml",
        "wizard/powerbi_credentials_wizard_view.xml",
        "wizard/unpublish_message_wizard_view.xml",

        "views/powerbi_connection_view.xml",
        "views/powerbi_dataset_view.xml",
        "views/powerbi_table_view.xml",
        "views/powerbi_workspace_view.xml",
        "views/powerbi_dashboards_view.xml",
        "views/powerbi_reports_view.xml",
        "views/powerbi_eventhouse_view.xml",
        "views/powerbi_database_view.xml",
        "views/powerbi_connector_dashboard.xml",
        "views/res_config_setting.xml",
        "views/powerbi_menus.xml",

        "security/powerbi_record_rules.xml",

        "data/demo/powerbi_demo_data.xml",
    ],

    "assets": {
        "web.assets_backend": [
            "/odoo_powerbi_connect/static/src/js/report.js",
            "/odoo_powerbi_connect/static/src/js/dashboard.js",
            "/odoo_powerbi_connect/static/src/js/search_hide.js",
            "https://cdnjs.cloudflare.com/ajax/libs/powerbi-client/2.19.1/powerbi.min.js"
        ]
    },

    "external_dependencies": {"python": ["msal", "pandas", "azure-kusto-ingest"]},
    "images": ["static/description/banner.gif"],
    "application": True,
    "installable": True,
    "auto_install": False,
    "price": 399,
    "currency": "USD",
    "pre_init_hook": "pre_init_check",
}
