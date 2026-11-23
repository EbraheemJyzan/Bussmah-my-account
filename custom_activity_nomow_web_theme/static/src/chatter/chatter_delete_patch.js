/** @odoo-module **/

import { messageActionsRegistry } from "@mail/core/common/message_actions";
import { Activity } from "@mail/core/web/activity";
import { AttachmentList } from "@mail/core/common/attachment_list";
import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";

// 1. Hide delete action on chatter messages for users without record delete permission
const deleteAction = messageActionsRegistry.get("delete");
if (deleteAction) {
    patch(deleteAction, {
        condition(component) {
            if (!session.is_record_deleter) {
                return false;
            }
            return super.condition(component);
        },
    });
}

// 2. Prevent activity cancellation for users without record delete permission
patch(Activity.prototype, {
    get canCancelActivity() {
        return Boolean(session.is_record_deleter);
    },
    async unlink() {
        if (!session.is_record_deleter) {
            return;
        }
        return super.unlink();
    },
});

// 3. Hide delete button on chatter attachments for users without record delete permission
patch(AttachmentList.prototype, {
    get showDelete() {
        if (this.env && this.env.inComposer) {
            return super.showDelete;
        }
        if (!session.is_record_deleter) {
            return false;
        }
        return super.showDelete;
    },
});

