/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SearchArchParser } from "@web/search/search_arch_parser";
import { SearchPanel } from "@web/search/search_panel/search_panel";

patch(SearchArchParser.prototype, {
    visitSearchPanel(searchPanelNode) {
        super.visitSearchPanel(...arguments);
        for (const node of searchPanelNode.children) {
            if (node.nodeType === 1 && node.tagName === "field") {
                const fieldName = node.getAttribute("name");
                const filterBussma = node.getAttribute("filter_bussma");
                if (filterBussma === "1" || filterBussma === "true") {
                    for (const tuple of this.sections) {
                        const section = Array.isArray(tuple) ? tuple[1] : tuple;
                        if (section && section.fieldName === fieldName) {
                            section.filterBussma = true;
                        }
                    }
                }
            }
        }
    },
});

patch(SearchPanel.prototype, {
    get sections() {
        const originalSections = super.sections;
        return originalSections.map((section) => {
            if (!section.filterBussma) {
                return section;
            }
            const secCopy = Object.assign({}, section);

            if (secCopy.type === "category") {
                const activeId = secCopy.activeValueId;
                if (activeId) {
                    const activeVal = secCopy.values.get(activeId);
                    if (activeVal) {
                        const newValues = new Map();
                        const allVal = secCopy.values.get(false);
                        if (allVal) {
                            newValues.set(false, allVal);
                        }
                        newValues.set(activeId, activeVal);
                        secCopy.values = newValues;
                        if (Array.isArray(secCopy.rootIds)) {
                            secCopy.rootIds = [false, activeId].filter((id) => secCopy.values.has(id));
                        }
                    }
                }
            } else if (secCopy.type === "filter") {
                const hasChecked = Array.from(secCopy.values.values()).some((v) => v.checked);
                if (hasChecked) {
                    const newValues = new Map();
                    for (const [valId, valObj] of secCopy.values) {
                        if (valObj.checked) {
                            newValues.set(valId, valObj);
                        }
                    }
                    secCopy.values = newValues;
                }
            }
            return secCopy;
        });
    },
});
