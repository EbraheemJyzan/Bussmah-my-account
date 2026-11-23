/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
import { onMounted, onPatched } from "@odoo/owl";

patch(ListRenderer.prototype, {
    setup() {
        super.setup();
        const applyBussmahSettings = () => {
            if (!this.rootRef.el || !this.props.archInfo) {
                return;
            }
            const xmlDoc = this.props.archInfo.xmlDoc;
            if (!xmlDoc) {
                return;
            }
            // Group headers styling
            const groupBg = xmlDoc.getAttribute("bussmah_group_bg");
            if (groupBg) {
                this.rootRef.el.classList.add("o_bussmah_grouped_header");
                this.rootRef.el.style.setProperty("--bussmah-group-bg", groupBg);
                const groupColor = xmlDoc.getAttribute("bussmah_group_color");
                if (groupColor) {
                    this.rootRef.el.style.setProperty("--bussmah-group-color", groupColor);
                }
                const groupSize = xmlDoc.getAttribute("bussmah_group_size");
                if (groupSize) {
                    this.rootRef.el.style.setProperty("--bussmah-group-size", groupSize);
                }
                const groupBold = xmlDoc.getAttribute("bussmah_group_bold");
                if (groupBold) {
                    this.rootRef.el.style.setProperty("--bussmah-group-weight", groupBold === "bold" ? "700" : "400");
                }
                const hoverBg = xmlDoc.getAttribute("bussmah_group_hover_bg");
                if (hoverBg) {
                    this.rootRef.el.style.setProperty("--bussmah-group-hover-bg", hoverBg);
                }
                const groupFont = xmlDoc.getAttribute("bussmah_group_font");
                if (groupFont) {
                    this.rootRef.el.style.setProperty("--bussmah-group-font", groupFont);
                }
            }

            // Column (table) headers styling
            const colHeaderBg = xmlDoc.getAttribute("bussmah_col_header_bg");
            const colHeaderColor = xmlDoc.getAttribute("bussmah_col_header_color");
            const colHeaderSize = xmlDoc.getAttribute("bussmah_col_header_size");
            const colHeaderBold = xmlDoc.getAttribute("bussmah_col_header_bold");
            const colHoverBg = xmlDoc.getAttribute("bussmah_col_header_hover_bg");
            const colHeaderFont = xmlDoc.getAttribute("bussmah_col_header_font");

            if (colHeaderBg || colHeaderColor || colHeaderSize || colHeaderBold || colHeaderFont) {
                this.rootRef.el.classList.add("o_bussmah_col_header");
                if (colHeaderBg) {
                    this.rootRef.el.style.setProperty("--bussmah-col-header-bg", colHeaderBg);
                }
                if (colHeaderColor) {
                    this.rootRef.el.style.setProperty("--bussmah-col-header-color", colHeaderColor);
                }
                if (colHeaderSize) {
                    this.rootRef.el.style.setProperty("--bussmah-col-header-size", colHeaderSize);
                }
                if (colHeaderBold) {
                    this.rootRef.el.style.setProperty("--bussmah-col-header-weight", colHeaderBold === "bold" ? "700" : "400");
                }
                if (colHoverBg) {
                    this.rootRef.el.style.setProperty("--bussmah-col-header-hover-bg", colHoverBg);
                }
                if (colHeaderFont) {
                    this.rootRef.el.style.setProperty("--bussmah-col-header-font", colHeaderFont);
                }
            }
        };

        onMounted(applyBussmahSettings);
        onPatched(applyBussmahSettings);
    },

    getRowClass(record) {
        const classNames = super.getRowClass(record);
        if (this.props.archInfo && this.props.archInfo.noOpen) {
            return `${classNames} o_list_no_open`;
        }
        return classNames;
    },
});
