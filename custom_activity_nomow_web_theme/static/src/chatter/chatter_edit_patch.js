/** @odoo-module **/

import { Message } from "@mail/core/common/message_model";
import { messageActionsRegistry } from "@mail/core/common/message_actions";
import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";

function isChatterModel(model) {
    return Boolean(model && model !== "discuss.channel" && model !== "mail.box");
}

// 1. Patch allowsEdition on Message prototype
patch(Message.prototype, {
    get allowsEdition() {
        const model = this.thread?.model || this.model;
        if (isChatterModel(model)) {
            return Boolean(session.is_record_editor);
        }
        return super.allowsEdition;
    },
});

// 2. Patch edit action in messageActionsRegistry
const editAction = messageActionsRegistry.get("edit");
if (editAction) {
    patch(editAction, {
        condition(component) {
            const thread = component.props.thread || component.props.message?.thread;
            const model = thread?.model || component.props.message?.model;
            if (isChatterModel(model)) {
                if (!session.is_record_editor) {
                    return false;
                }
                return component.props.message?.message_type === "comment";
            }
            return super.condition(component);
        },
    });
}

