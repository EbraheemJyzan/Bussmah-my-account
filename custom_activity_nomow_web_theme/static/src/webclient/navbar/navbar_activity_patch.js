/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import { registry } from "@web/core/registry";
import { useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

function applyActivityPatch(componentClass) {
    if (!componentClass || !componentClass.prototype) return;
    patch(componentClass.prototype, {
        setup() {
            super.setup();
            this.orm = useService("orm");
            this.activityState = useState({ count: 0, menuCounts: {} });

            try {
                this.mailStore = useState(useService("mail.store"));
            } catch (e) {
                this.mailStore = null;
            }

            onWillStart(async () => {
                await this.fetchActivityCount();
            });

            onMounted(() => {
                this._activityInterval = setInterval(() => {
                    this.fetchActivityCount();
                }, 10000);
                // Also inject after a short delay for initial render
                setTimeout(() => this._injectSubMenuBadges(), 500);
            });

            onWillUnmount(() => {
                if (this._activityInterval) {
                    clearInterval(this._activityInterval);
                }
            });
        },

        async fetchActivityCount() {
            try {
                const counts = await this.orm.call("res.users", "get_entries_activity_counts");
                if (counts && typeof counts === "object") {
                    this.activityState.menuCounts = counts;
                    this.activityState.count = counts["bussma_system.rout_menu_commercial_sector"] || 0;
                } else {
                    this.activityState.menuCounts = {};
                    this.activityState.count = 0;
                }
                // Inject after OWL re-render settles
                setTimeout(() => this._injectSubMenuBadges(), 100);
            } catch (err) {
                // Handle temporary errors silently
            }
        },

        _injectSubMenuBadges() {
            const menuCounts = this.activityState.menuCounts || {};

            // Remove all previously injected DOM badges
            document.querySelectorAll(".custom-activity-badge-dom").forEach(el => el.remove());

            // Inject badges into all elements that have data-menu-xmlid attribute
            document.querySelectorAll("[data-menu-xmlid]").forEach(el => {
                const xmlid = el.getAttribute("data-menu-xmlid");
                if (!xmlid) return;
                const count = menuCounts[xmlid];
                if (!count || count <= 0) return;

                // The root menu icon badge is handled by OWL template – skip it here
                if (xmlid === "bussma_system.rout_menu_commercial_sector") return;
                if (xmlid === "sales_and_auction_management.menu_employee_guide_root") return;
                if (xmlid === "marketing_opportunity_management.menu_marketing_root") return;
                if (xmlid === "financial_management.menu_financial_management_root") return;
                if (xmlid === "marketing_opportunity_management.menu_opportunity_root") return;

                // Skip if badge already injected
                if (el.querySelector(".custom-activity-badge-dom")) return;

                const badge = document.createElement("span");
                badge.className = "badge rounded-circle custom-activity-badge custom-submenu-badge custom-activity-badge-dom";
                badge.setAttribute("title", count + " Activity Notifications");
                badge.textContent = count;

                el.style.position = "relative";
                el.appendChild(badge);
            });
        },

        getMenuActivityCount(xmlidOrId) {
            if (!this.activityState.menuCounts) {
                return 0;
            }
            if (xmlidOrId === "sales_and_auction_management.menu_employee_guide_root") {
                return 0;
            }
            if (xmlidOrId && this.activityState.menuCounts[xmlidOrId]) {
                return this.activityState.menuCounts[xmlidOrId];
            }
            return 0;
        },

        get activityCount() {
            return this.getMenuActivityCount("bussma_system.rout_menu_commercial_sector");
        }
    });
}

// Always patch NavBar
applyActivityPatch(NavBar);

// Safely patch AppsMenu if registered in actions category
const actionRegistry = registry.category("actions");
const AppsMenuClass = actionRegistry.get("apps_menu_tag");
if (AppsMenuClass) {
    applyActivityPatch(AppsMenuClass);
}
