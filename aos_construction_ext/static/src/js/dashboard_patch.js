/** @odoo-module **/

import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

const ConstructionDashboard = registry.category("actions").get("construction_dashboard");

patch(ConstructionDashboard.prototype, {
    async loadData() {
        await super.loadData();
        // Certificates to the client and certificates to subcontractors run in
        // opposite directions. The base added them into one figure, so the
        // headline read as revenue while a third of it was money going out.
        const customerCertificates = await this.orm.searchRead(
            "construction.ra.billing",
            [["state", "=", "approved"], ["billing_type", "=", "customer"]],
            ["total_amount"]
        );
        this.state.total_billed = customerCertificates.reduce(
            (total, record) => total + (record.total_amount || 0), 0
        );
    },

    // The base builds these action dictionaries with bare strings, so every
    // breadcrumb opened from a card read English.
    openProjects(state) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Projects"),
            res_model: "construction.project",
            view_mode: "list,kanban,form",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            domain: state ? [["state", "=", state]] : [],
        });
    },

    openWorkOrders(pending) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Work Orders"),
            res_model: "construction.work.order",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: pending
                ? [["state", "in", ["draft", "confirmed", "in_progress"]]]
                : [],
        });
    },

    openRequisitions(pending) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Material Requisitions"),
            res_model: "construction.material.requisition",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: pending ? [["state", "in", ["draft", "submitted"]]] : [],
        });
    },

    openQualityChecks(open) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Quality Checks"),
            res_model: "construction.quality.check",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: open ? [["state", "in", ["draft", "in_progress"]]] : [],
        });
    },
});
