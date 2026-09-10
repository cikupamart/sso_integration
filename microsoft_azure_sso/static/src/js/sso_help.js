/** @odoo-module **/

import { registry } from "@web/core/registry";

const { Component } = owl;

export class SsoHelp extends Component {}
SsoHelp.template = "microsoft_azure_sso.SsoHelp";

registry.category("actions").add("sso_help_action", SsoHelp);
