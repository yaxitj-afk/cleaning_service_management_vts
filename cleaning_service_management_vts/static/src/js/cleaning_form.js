/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CleaningForm = publicWidget.Widget.extend({
    selector: '.cleaning-form-card',

    start() {
        const checkbox = this.el.querySelector('#is_recurring');
        const recurringFields = this.el.querySelector('#recurring_fields');

        if (!checkbox || !recurringFields) {
            return;
        }

        const toggleFields = () => {
            recurringFields.style.display = checkbox.checked ? 'block' : 'none';
        };

        checkbox.addEventListener('change', toggleFields);

        toggleFields();

        return this._super(...arguments);
    },
});