/** @odoo-module **/
/* Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { ControlPanel } from "@web/search/control_panel/control_panel";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(ControlPanel.prototype, {
    setup() {
        super.setup && super.setup();
        onMounted(() => {
            const model = this.env.searchModel && this.env.searchModel.resModel;
            if (model === "powerbi.connector.dashboard") {
                const searchBar = this.root.el.querySelector(".o_cp_searchview");
                const pager = this.root.el.querySelector(".o_cp_pager");
                if (searchBar) {
                    searchBar.remove();
                }
                if (pager) {
                    pager.remove();
                }
            }
        });
    },
});
