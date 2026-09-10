/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const { Component, onWillStart, useState } = owl;

export class SsoDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            total: 0,
            success: 0,
            failed: 0,
            uniqueUsers: 0,
            recentLogs: [],
            loading: true,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.state.loading = true;

        const statusGroups = await this.orm.readGroup(
            "sso.audit.log",
            [],
            ["status"],
            ["status"]
        );
        let total = 0, success = 0, failed = 0;
        for (const grp of statusGroups) {
            total += grp.status_count || grp.__count || 0;
            const count = grp.status_count || grp.__count || 0;
            if (grp.status === "success") {
                success = count;
            } else if (grp.status === "failed") {
                failed = count;
            }
        }

        const userGroups = await this.orm.readGroup(
            "sso.audit.log",
            [["user_id", "!=", false]],
            ["user_id"],
            ["user_id"]
        );

        const recentLogs = await this.orm.searchRead(
            "sso.audit.log",
            [],
            ["login_date", "azure_email", "user_id", "status", "ip_address"],
            { limit: 10, order: "login_date desc" }
        );

        this.state.total = total;
        this.state.success = success;
        this.state.failed = failed;
        this.state.uniqueUsers = userGroups.length;
        this.state.recentLogs = recentLogs;
        this.state.loading = false;
    }

    openAuditLogs(domain = []) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Microsoft SSO Audit Logs",
            res_model: "sso.audit.log",
            view_mode: "list,form,pivot,graph",
            views: [
                [false, "list"],
                [false, "form"],
                [false, "pivot"],
                [false, "graph"],
            ],
            domain,
        });
    }
}

SsoDashboard.template = "microsoft_azure_sso.SsoDashboard";

registry.category("actions").add("sso_dashboard_action", SsoDashboard);
