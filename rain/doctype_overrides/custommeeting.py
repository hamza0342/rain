import frappe
from meeting.meeting.doctype.meeting.meeting import Meeting

class CustomMeeting(Meeting):
    def before_insert(self):
        roles = frappe.get_roles(frappe.session.user)
        user = frappe.session.user
        if "Industry" in roles:
            self.industry = user
        elif "Academia" in roles:
            self.academia = user

        # frappe.get_doc({
        #         "doctype": "User Permission",
        #         "user": user,
        #         "allow": "Meeting",
        #         "for_value": user,
        #         "apply_to_all_doctypes": 1
        #     }).insert(ignore_permissions=True)