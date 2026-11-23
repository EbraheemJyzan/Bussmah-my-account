/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";

patch(ListController.prototype, {
    async openRecord(record, force = false) {
        // If the view disables opening records (no_open = 1 / true), prevent opening
        if (this.archInfo && this.archInfo.noOpen && !force) {
            return;
        }
        return super.openRecord(record, force);
    },
});
