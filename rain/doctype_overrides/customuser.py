import frappe
from frappe.core.doctype.user.user import User
from urllib.parse import urlparse
from urllib.parse import parse_qs

class CustomUser(User):
    def send_welcome_mail_to_user(self):
        from frappe.utils import get_url

        link = self.reset_password()
        subject = None
        method = frappe.get_hooks("welcome_email")
        if method:
            subject = frappe.get_attr(method[-1])()
        if not subject:
            site_name = frappe.db.get_default("site_name") or frappe.get_conf().get("site_name")
            if site_name:
                subject = ("Welcome to {0}").format(site_name)
            else:
                subject = ("Complete Registration")

        self.send_login_mail(
            subject,
            "new_user",
            dict(
                link=link,
                site_url=get_url(),
            ),
        )