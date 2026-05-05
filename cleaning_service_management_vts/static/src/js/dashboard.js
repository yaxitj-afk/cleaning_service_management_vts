/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class BookingDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        // ✅ SINGLE STATE (FIXED)
        this.state = useState({
            title: "Booking Dashboard",

            period: "month",
            serviceStats: [],

            data: {
                draft: 0,
                under_review: 0,
                approved: 0,
                rejected: 0,
            },
        });

        onWillStart(async () => {
            await this.loadDashboard();
        });
    }

    async loadDashboard() {
        try {
            this.state.data = await this.orm.call(
                "booking.request",
                "get_dashboard_data"
            );

            this.state.serviceStats = await this.orm.call(
                "booking.request",
                "get_service_analysis",
                [this.state.period]
            );

        } catch (err) {
            console.error("Dashboard load error:", err);
        }
    }

    openBookings(status) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Bookings",
            res_model: "booking.request",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "=", status]],
            target: "current",
        });
    }

    async onChangePeriod(ev) {
        this.state.period = ev.target.value;
        await this.loadDashboard();
    }
}

BookingDashboard.template =
    "cleaning_service_management_vts.booking_dashboard_template";

registry.category("actions").add("booking_dashboard", BookingDashboard);