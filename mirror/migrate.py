import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.desk.page.setup_wizard.setup_wizard import make_records

def after_migrate():
    custom_fields = {
        "Sales Invoice" : [
            dict(
                fieldname = "custom_gov_sales_invoice_reference",
                fieldtype = "Data",
                label = "Goverment Sales Invoice Reference",
                is_custom_field = 1,
                is_system_generated_field = 0,
                read_only = 1,
                insert_after = "is_debit_note"
            )
        ]
    }

    print("Adding Custom Fields In SI.....")
    for dt, fields in custom_fields.items():
        print("*******\n %s: " % dt, [d.get("fieldname") for d in fields])
    create_custom_fields(custom_fields)