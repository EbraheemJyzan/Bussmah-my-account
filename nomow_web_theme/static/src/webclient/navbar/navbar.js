/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { NavBar } from '@web/webclient/navbar/navbar';
import { useState } from "@odoo/owl";
import { session } from "@web/session";

patch(NavBar.prototype, {

    setup() {
        super.setup();
        this.state = useState({ company: session.company });
    },

    changeSidebar() {
        let sidebar_panel = document.querySelector('.sidebar_panel');
        let o_action_manager = document.querySelector('.o_action_manager');
        let o_main_navbar = document.querySelector('.o_main_navbar');
        o_main_navbar.classList.toggle('close_o_main_navbar');
        sidebar_panel.classList.toggle('close_sidebar');
        o_action_manager.classList.toggle('close_o_action_manager');
    }
})