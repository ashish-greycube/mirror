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
        handle_gov_site_error(response, out, docname)


def handle_gov_site_error(response, payload, docname):
    try:
        error = response.json()
    except ValueError:
        error = {"raw_response": response.text}

    messages = get_server_messages(error)

    # ensure_ascii=False keeps Arabic text readable instead of م...
    log_message = "\n\n".join([
        f"Status Code: {response.status_code}",
        f"Error Type: {error.get('exc_type', '')}",
        "Messages:\n" + "\n".join(f"{i}. {m}" for i, m in enumerate(messages, 1)),
        "Exception:\n" + str(error.get("exception") or error.get("exc") or ""),
        "Payload Sent:\n" + json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        "Full Response:\n" + json.dumps(error, indent=2, ensure_ascii=False, default=str),
    ])
    log = frappe.log_error(
        title=f"GOV Sync Failed: {docname}",
        message=log_message,
        reference_doctype="Sales Invoice",
        reference_name=docname,
    )
    # Keep the log even though frappe.throw rolls back
    frappe.db.commit()

    if not messages:
        messages = [f"GOV site error {response.status_code}"]
    frappe.throw(
        "<br>".join(f"{i}. {m}" for i, m in enumerate(messages, 1))
        + f"<br><br>Error Log: {log.name}",
        title="GOV Site Sync Failed",
    )


def get_server_messages(error):
    messages = []
    for raw in frappe.parse_json(error.get("_server_messages") or "[]"):
        msg = frappe.parse_json(raw)
        messages.append(msg.get("message") if isinstance(msg, dict) else str(msg))
    return messages