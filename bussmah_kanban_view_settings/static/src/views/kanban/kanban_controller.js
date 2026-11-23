/** @odoo-module **/

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { patch } from "@web/core/utils/patch";

patch(KanbanController.prototype, {
    async openRecord(record, mode) {
        // If the view disables opening records (can_open = false / 0), prevent opening immediately
        if (this.props.archInfo && this.props.archInfo.canOpenRecords === false) {
            return;
        }
        return super.openRecord(record, mode);
    },
});
