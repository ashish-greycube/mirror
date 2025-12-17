import json
import frappe
import requests

@frappe.whitelist()
def synchronize_sales_invoice_to_government_site(doc, docname):
    # Final Output
    out = {}

    # Sales Invoice Document In JSON
    doc_json = frappe.parse_json(doc)

    # API Credentials From Settings Doctype
    settings = frappe.get_doc("PureClean Settings")
    URL = settings.government_site_link
    API_KEY = settings.api_key
    API_SECRET = settings.api_secret

    # Fields To Include In API Body
    sales_invoice_parent_fields = ["custom_payment_type","customer","company","posting_date","debit_to","taxes_and_charges"]
    sales_invoice_item_fields = ["item_code","rate","uom","qty","conversion_factor","tax_rate"]
    sales_invoice_tax_fields = ["charge_type","account_head","cost_center","rate","description"]

    # For Loops To Collect Required Data From Doc JSON
    for field in sales_invoice_parent_fields:
        for key, value in doc_json.items():
            if key==field:
                out[key] = value
                break

    items_list = []
    item_dict = {}
    for item in doc_json['items']:
        for field in sales_invoice_item_fields: 
            for key, value in item.items():
                if key==field:
                    item_dict[key] = value
                    break
        items_list.append(item_dict)
        item_dict = {}
    out['items'] = items_list

    taxes_list = []
    tax_dict = {}
    for item in doc_json['taxes']:
        for field in sales_invoice_tax_fields: 
            for key, value in item.items():
                if key==field:
                    tax_dict[key] = value
                    break
        taxes_list.append(tax_dict)
        tax_dict = {}
    out['taxes'] = taxes_list
    print(out, "=========================")
    # API Call To Create Sales Invoice On Government Site
    url = f"{URL}api/resource/Sales Invoice"
    payload = out
    headers = {
        "authorization": f"token {API_KEY}:{API_SECRET}",
        "content-type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)

    # If Req Completed Than Set It's Reference No Else Give Error Message
    if response.status_code == 200 or response.status_code == 201:
        result = response.json()
        frappe.db.set_value("Sales Invoice", docname, "custom_gov_sales_invoice_reference", result['data']['name'])
        frappe.msgprint(f"Sales Invoice Created On GOV Site: {response.json()['data']['name']}", alert=True)
    else:
        error = frappe.parse_json(response.json())
        if "_server_messages" in error:
            exception = frappe.parse_json(error['_server_messages'])
            message = frappe.parse_json(exception[0]).message
            frappe.throw(message)
        else:
            message = str(error)
            frappe.throw(message)