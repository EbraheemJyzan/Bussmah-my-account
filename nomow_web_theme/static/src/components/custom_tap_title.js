/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(WebClient.prototype, {
    async setup() {
        const orm = useService("orm");
        const title = useService("title");

        await super.setup();

        const data = await orm.searchRead("res.company", [], ["name"]);
        const name = (data.length && data[data.length - 1].name) || "";
        title.setParts({ zopenerp: name });
    },
});
