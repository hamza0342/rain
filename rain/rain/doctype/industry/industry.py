# Copyright (c) 2022, MicroMerger and contributors 
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint
from frappe.utils.password import update_password as _update_password
from frappe.auth import LoginManager
import json

class Industry(Document):
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
						"role":"Industry"
						})
			user.save(ignore_permissions=True)

	def after_insert(self):
		if not frappe.db.exists('User Permission', {'user': self.email, 'allow': 'Industry', 'for_value': self.email}):
			frappe.get_doc({
					"doctype": "User Permission",
					"user": self.email,
					"allow": "Industry",
					"for_value": self.email,
					"apply_to_all_doctypes": 1
				}).insert(ignore_permissions=True)

	def on_trash(self):
		if frappe.db.exists('User', self.email):
			frappe.get_doc('User', self.email).delete(ignore_permissions=True)
		if frappe.db.exists('Campaign', {'industry': self.email}):
			for campaign in frappe.get_list('Campaign', {'industry': self.email}):
				current_camp = frappe.get_doc('Campaign', campaign.name)
				current_camp.delete(ignore_permissions=True)


@frappe.whitelist(allow_guest=True)
def save_signup_data(first_name=None, last_name=None, email=None, company=None, job_title=None, thematic_area=None, thematic_sub_area=None, sector=None):
	# Check if email already exisits
	if frappe.db.exists('Industry', {'email': email}):
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
					"role":"Industry"
					})
		user.save(ignore_permissions=True)

		frappe.get_doc(dict(
			doctype = 'Industry',
			account_status = "Pending",
			first_name = first_name,
			last_name = last_name,
			email = email,
			company_name = company,
			job_title = job_title,
			thematic_area = thematic_area,
			thematic_sub_area = thematic_sub_area,
			sector = sector,
			owner = email
		)).insert(ignore_permissions=True)
		frappe.db.set_value("Industry", email, "owner", email)
		frappe.db.commit()

		if not frappe.db.exists('User Permission', {'user': email, 'allow': 'Industry', 'for_value': email}):
			frappe.get_doc({
					"doctype": "User Permission",
					"user": email,
					"allow": "Industry",
					"for_value": email,
					"apply_to_all_doctypes": 1
				}).insert(ignore_permissions=True)
		# industry = frappe.get_doc("Industry", {"email": email})
		return json.dumps({'Success': 'Registration compeleted. Please check your email!'})

@frappe.whitelist(allow_guest=True)
def verify_account(key=None):
	result = frappe._dict()
	if key:
		result.user = frappe.db.get_value("User", {"reset_password_key": key})
		if not result.user:
			return json.dumps({'Error': 'The Link specified has either been used before or Invalid'})
		else:
			return json.dumps({'Success': 'Key found'})
	else:
		return json.dumps({'Error': 'Key Missing!'})


@frappe.whitelist(allow_guest=True)
def set_new_password(key=None, new_password=None):
	logout_all_sessions=0
	result = frappe._dict()
	if key:
		user = frappe.db.get_value("User", {"reset_password_key": key})
		if not user:
			return json.dumps({'Error': 'The Link specified has either been used before or Invalid'})
		else:
			# update-password
			logout_all_sessions = cint(logout_all_sessions) or frappe.db.get_single_value("System Settings", "logout_on_password_reset")
			_update_password(user, new_password, logout_all_sessions=cint(logout_all_sessions))
			doc = frappe.get_doc('User', {"reset_password_key": key})
			doc.db_set('reset_password_key', '')
			return json.dumps({'Success': 'Password successfully set!'})
	else:
		return json.dumps({'Error': 'Key Missing!'})

@frappe.whitelist(allow_guest=True)
def authenticate(usr=None, pwd=None):
	login_manager = LoginManager()
	login_manager.authenticate(usr,pwd)
	login_manager.post_login()
	if frappe.response['message'] == 'Logged In' or frappe.response['message'] == 'No App':
		user = frappe.get_doc("User",usr)
		if user.last_name:
			user_name = user.first_name + ' ' + user.last_name
		else:
			user_name = user.first_name
		email = user.email
		roles = frappe.get_roles(usr)
		if "Industry" in roles:
			role = "Industry"
			user_status = frappe.get_doc("Industry", {"email": usr})
			user_type = user_status.sector
			job_title = user_status.job_title
		elif "Academia" in roles:
			role = "Academia"
			user_status = frappe.get_doc("Academia", {"email": usr})
			user_type = ""
			job_title = ""
		if user_status.account_status == "Pending" or user_status.account_status == "Approved":
			return json.dumps({'Success': 'Success', 'role': role, 'type': user_type, 'title': job_title, 'user': email, 'name': user_name, 'pwd': pwd, 'bio': user_status.bio, 'account_status': user_status.account_status, 'first_name': user.first_name, 'last_name': user.last_name})
		else:
			return json.dumps({'Error': 'Your account has been rejected!'})
	else:
		return json.dumps({'Error': frappe.response['message']}) 

@frappe.whitelist(allow_guest=True)
def update_profile(first_name=None, last_name=None, title=None, bio=None):
	roles = frappe.get_roles(frappe.session.user)
	user = frappe.session.user
	if "Industry" in roles:
		industry = frappe.get_doc("Industry", {"email": user})
		user = frappe.get_doc("User",user)
		user.first_name = first_name
		user.last_name = last_name
		user.save()

		industry.first_name = first_name
		industry.last_name = last_name
		industry.bio = bio
		industry.job_title = title
		industry.save()
		return json.dumps({'Success': 'Profile information updated!'}) 
	else:
		frappe.local.response.http_status_code = 400
		frappe.local.response.message = "Nothing"

@frappe.whitelist(allow_guest=True)
def get_thematic_areas():
	thematic_areas = frappe.get_all("Thematic Area")
	index = 0
	for thematic_area in thematic_areas:
		thematic_sub_areas = frappe.get_all("Sub Thematic Table",fields=["*"], filters={'parent': thematic_area.name})
		thematic_areas[index].thematic_sub_areas = thematic_sub_areas
		index += 1
	return thematic_areas