import frappe
import json

@frappe.whitelist(allow_guest=True)
def get_user_login_data():
	data = get_request_form_data()
	user = frappe.get_doc("User", data.email)
	user_role = user.roles[0].role

	if user_role == "Industry":
		role = "Industry"
		industry = frappe.get_doc("Industry", {'email': data.email})
		return json.dumps({
			"first_name": industry.first_name, 
			"last_name": industry.last_name, 
			"email": data.email, 
			"role": role,
			"job_title": industry.job_title,
			"account_status": industry.account_status,
			"type": industry.sector,
			"bio": industry.bio
			})
	elif user_role == "Academia":
		role = "Academia"
		academia = frappe.get_doc("Academia", {'email': data.email})
		return json.dumps({
			"first_name": academia.first_name, 
			"last_name": academia.last_name, 
			"email": academia.email, 
			"role": role,
			"account_status": academia.account_status,
			"type": "Academia",
			"job_title": academia.designation,
			"bio": academia.bio
			})
	frappe.local.response.http_status_code = 404
	frappe.local.response.message = "Not Found"
	
def get_request_form_data():
	if frappe.local.form_dict.data is None:
		data = frappe.safe_decode(frappe.local.request.get_data())
	else:
		data = frappe.local.form_dict.data

	try:
		return frappe.parse_json(data)
	except ValueError:
		return frappe.local.form_dict

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
	elif "Academia" in roles:
		academia = frappe.get_doc("Academia", {"email": user})
		user = frappe.get_doc("User",user)
		user.first_name = first_name
		user.last_name = last_name
		user.save()

		academia.first_name = first_name
		academia.last_name = last_name
		academia.bio = bio
		academia.designation = title
		academia.save()
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

@frappe.whitelist(allow_guest=True)
def save_signup_data():
	# Check if email already exisits
	data = get_request_form_data()
	if frappe.db.exists('Industry', {'email': data.email}):
		return json.dumps({'Error': 'Email already registered'})
	elif frappe.db.exists('User', {'email': data.email}):
		return json.dumps({'Error': 'Email already registered'})
	else:
		frappe.get_doc(dict(
		doctype = 'User',
		email = data.email,
		name = data.first_name,
		send_welcome_email=1,
		first_name = data.first_name,
		last_name = data.last_name,
		new_password = "micromerger" 
		)).insert(ignore_permissions=True)

		user = frappe.get_doc("User", data.email)
		user.append('roles',{
					"doctype": "Has Role",
					"role":"Industry"
					})
		user.save(ignore_permissions=True)

		frappe.get_doc(dict(
			doctype = 'Industry',
			account_status = "Pending",
			first_name = data.first_name,
			last_name = data.last_name,
			email = data.email,
			company_name = data.company,
			job_title = data.job_title,
			thematic_area = data.thematic_area,
			thematic_sub_area = data.thematic_sub_area,
			sector = data.sector,
			owner = data.email
		)).insert(ignore_permissions=True)
		frappe.db.set_value("Industry", data.email, "owner", data.email)
		frappe.db.commit()

		if not frappe.db.exists('User Permission', {'user': data.email, 'allow': 'Industry', 'for_value': data.email}):
			frappe.get_doc({
					"doctype": "User Permission",
					"user": data.email,
					"allow": "Industry",
					"for_value": data.email,
					"apply_to_all_doctypes": 1
				}).insert(ignore_permissions=True)
		# industry = frappe.get_doc("Industry", {"email": email})
		return json.dumps({'Success': 'Registration compeleted. Please check your email!'})

def get_request_form_data():
	if frappe.local.form_dict.data is None:
		data = frappe.safe_decode(frappe.local.request.get_data())
	else:
		data = frappe.local.form_dict.data

	try:
		return frappe.parse_json(data)
	except ValueError:
		return frappe.local.form_dict