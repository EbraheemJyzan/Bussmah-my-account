/** @odoo-module **/
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { CheckBox } from "@web/core/checkbox/checkbox";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component , useState, onWillStart } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";

const userMenuRegistry = registry.category("user_menuitems");

export class UserMenu extends Component {
    setup() {
        this.user = user;
        this.actionService = useService("action");
        this.orm = useService("orm");
        this.actionService = this.env.services.action;
        this.orm = this.env.services.orm;
        const { origin } = browser.location;
        const { userId } = this.user.userId;
        const { lang } = this.user;
        const { langs } = this.user.settings;
        const matched = langs.find(item => item.code === lang);
        console.log("111:", this.user.context);
        console.log("lang: ", lang);
        // const  activeLang  = ;
        this.state = useState(
        {
            langs: user.settings.langs,
            activeLang: matched ? matched.iso_code : 'en',
            activeCode: ''
            
         });
         onWillStart(async () => {
            this.state.activeCode = await rpc('/api/flag_image_url', {
                lang: lang,
            })
        })
        this.source = `${origin}/web/image?model=res.users&field=avatar_128&id=${userId}`;
    }

    getElements() {
        const sortedItems = userMenuRegistry
            .getAll()
            .map((element) => element(this.env))
            .sort((x, y) => {
                const xSeq = x.sequence ? x.sequence : 100;
                const ySeq = y.sequence ? y.sequence : 100;
                return xSeq - ySeq;
            });
        return sortedItems;
    }

    async onSelectLang(activeLang){
        await this.orm.write('res.users', [user.userId], { lang: activeLang});
        return this.actionService.doAction({
            type: "ir.actions.client",
            tag: "reload_context",
        })
    }
}
UserMenu.template = "web.LangMenu";
UserMenu.components = { Dropdown, DropdownItem, CheckBox };
UserMenu.props = {};

export const systrayItem = {
    Component: UserMenu,
};
registry.category("systray").add("web.lang_menu", systrayItem, { sequence: 5 });
