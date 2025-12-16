frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        if (frm.doc.docstatus == 1 && frm.doc.custom_gov_sales_invoice_reference == undefined) {
            frm.add_custom_button("Sync With Gov Site", function (frm) {
                frappe.call({
                    method: "mirror.api.synchronize_sales_invoice_to_government_site",
                    args: {
                        "doc": cur_frm.doc,
                        "docname": cur_frm.doc.name
                    },
                    callback: function (res) {
                        cur_frm.reload_doc()
                    }
                })
            });
        }
    }
});