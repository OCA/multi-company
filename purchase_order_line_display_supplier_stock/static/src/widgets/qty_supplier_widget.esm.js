/** @odoo-module **/

import {registry} from "@web/core/registry";
import {usePopover} from "@web/core/popover/popover_hook";
import {Component} from "@odoo/owl";
import {standardWidgetProps} from "@web/views/widgets/standard_widget_props";

export class QtySupplierPopover extends Component {
    static template = "purchase_order_line_display_supplier_stock.QtySupplierPopover";
    static props = {
        record: Object,
        close: Function,
    };
}

export class QtySupplierWidget extends Component {
    static components = {Popover: QtySupplierPopover};
    static template = "purchase_order_line_display_supplier_stock.QtySupplier";
    static props = {...standardWidgetProps};
    setup() {
        this.popover = usePopover(this.constructor.components.Popover, {
            position: "top",
        });
    }
    async showPopup(ev) {
        const target = ev.currentTarget;
        this.popover.open(target, {
            record: this.props.record,
        });
    }
}

export const qtySupplierWidget = {
    component: QtySupplierWidget,
    fieldDependencies: [
        {name: "display_qty_supplier_widget", type: "boolean"},
        {name: "qty_supplier_issue", type: "boolean"},
        {name: "qty_supplier_widget_data", type: "binary"},
    ],
};
registry.category("view_widgets").add("qty_supplier_widget", qtySupplierWidget);
