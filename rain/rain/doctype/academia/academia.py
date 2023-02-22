# Copyright (c) 2022, MicroMerger and contributors 
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint
from frappe.utils.password import update_password as _update_password
from frappe.auth import LoginManager
import json

class Academia(Document):
	def before_insert(self):
		if not frappe.db.exists('User', {'email': self.email}):
			frappe.get_doc(dict(
			doctype = 'User',
			email = self.email,
			name = self.first_name,
			send_welcome_email=1,
			first_name = self.first_name,
			last_name = self.last_name,
			new_password = "micromerger" 
			)).insert(ignore_permissions=True)

			user = frappe.get_doc("User", self.email)
			user.append('roles',{
						"doctype": "Has Role",
						"role":"Academia"
						})
			user.save(ignore_permissions=True)

	def after_insert(self):
		if not frappe.db.exists('User Permission', {'user': self.email, 'allow': 'Academia', 'for_value': self.email}):
			frappe.get_doc({
					"doctype": "User Permission",
					"user": self.email,
					"allow": "Academia",
					"for_value": self.email, 
					"apply_to_all_doctypes": 1
				}).insert(ignore_permissions=True)

	def on_trash(self):
		if frappe.db.exists('User', self.email):
			frappe.get_doc('User', self.email).delete(ignore_permissions=True)

@frappe.whitelist(allow_guest=True)
def save_signup_data(first_name=None, last_name=None, email=None, institute=None, designation=None, thematic_area=None, thematic_sub_area=None):
	# Check if email already exisits
	if frappe.db.exists('Academia', {'email': email}):
		return json.dumps({'Error': 'Email already registered'})
	elif frappe.db.exists('User', {'email': email}):
		return json.dumps({'Error': 'Email already registered'})
	else:
		frappe.get_doc(dict(
		doctype = 'User',
		email = email,
		name = first_name,
		send_welcome_email=1,
		first_name = first_name,
		last_name = last_name,
		new_password = "micromerger" 
		)).insert(ignore_permissions=True)

		user = frappe.get_doc("User", email)
		user.append('roles',{
					"doctype": "Has Role",
					"role":"Academia"
					})
		user.save(ignore_permissions=True)

		frappe.get_doc(dict(
			doctype = 'Academia',
			account_status = "Pending",
			first_name = first_name,
			last_name = last_name,
			email = email,
			institute = institute,
			designation = designation,
			thematic_area = thematic_area,
			thematic_sub_area = thematic_sub_area,
			owner = email
		)).insert(ignore_permissions=True)

		frappe.db.set_value("Academia", email, "owner", email)
		frappe.db.commit()
		if not frappe.db.exists('User Permission', {'user': email, 'allow': 'Academia', 'for_value': email}):
			frappe.get_doc({
					"doctype": "User Permission",
					"user": email,
					"allow": "Academia",
					"for_value": email,
					"apply_to_all_doctypes": 1
				}).insert(ignore_permissions=True)

		return json.dumps({'Success': 'Registration compeleted. Please check your email!'})
