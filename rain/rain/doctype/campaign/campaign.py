# Copyright (c) 2022, MicroMerger and contributors 
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.auth import LoginManager
import json
import datetime

class Campaign(Document):
	def before_insert(self):
		self.campaign_status = "Open for Proposals"
		
	# def before_save(self):
	# 	thematic_area = frappe.get_doc('Thematic Area', self.thematic_area)
	# 	self.color = thematic_area.color

@frappe.whitelist(allow_guest=True)
def get_campaigns(usr=None, role=None):
	campaigns = []
	if usr:
		# result.campaigns = frappe.get_all("Campaign", filters={"industry": usr}, 
		# fields="`tabCampaign`.*, `tabDeliverable`.*")
		if role == "Industry":
			data = frappe.db.sql(
				f"""
				SELECT table1.*
				FROM `tabCampaign`table1
				WHERE table1.industry = "{usr}"
				""", 
				as_dict=1
			)
		elif role == "Academia":
			data = frappe.db.sql(
				f"""
				SELECT table1.*
				FROM `tabCampaign`table1
				WHERE table1.academia_user = "{usr}"
				""", 
				as_dict=1
			)
		if not data:
			return json.dumps({'Error': 'No Campaign Found'})
		else: 
			for row in data:
				current_row = frappe.db.sql(
					f"""
					SELECT * 
					FROM `tabDeliverable` 
					WHERE parent = "{row.name}"
					""",
					as_dict=1
				)
				row["deliverables"] = current_row
				campaigns.append(row)
			return frappe.as_json(campaigns)
	return json.dumps({'Error': 'User not Found'})

@frappe.whitelist(allow_guest=True)
def save_campaign_data(title=None, last_date=None, research_area=None, description=None, user=None, pwd=None, thematic_area=None, thematic_sub_area=None, files=None):
	# return frappe.request.files.message.campaign_attachment_0
	login_manager = LoginManager()
	login_manager.authenticate(user,pwd)
	login_manager.post_login()
	if frappe.response['message'] == 'Logged In' or frappe.response['message'] == 'No App':
		if last_date and last_date != 'null': 
			last_date = datetime.datetime.strptime(last_date, '%Y-%m-%d').strftime('%d-%m-%y')
		else: 
			last_date = ""
		Campaign = frappe.get_doc({
			'doctype': 'Campaign',
			'campaign_title': title,
			'campaign_status': 'Open for Proposals',
			'last_date': last_date,
			'industry': user,
			'research_area': research_area,
			'campaign_description': description,
			'thematic_area': thematic_area,
			'thematic_sub_area': thematic_sub_area
		})

		Campaign.insert(ignore_permissions=True)
		return json.dumps({'Success': 'New Campaign Created', 'name': Campaign.name, 'last_date': last_date})
	else:
		return json.dumps({'Error': 'Failed to Authenticate'})


@frappe.whitelist(allow_guest=True)
def save_deliverable_data(campaign_id=None, title=None, start_date=None, description=None, user=None, pwd=None, files=None):
	# return frappe.request.files.message.campaign_attachment_0
	login_manager = LoginManager()
	login_manager.authenticate(user,pwd)
	login_manager.post_login()
	if frappe.response['message'] == 'Logged In' or frappe.response['message'] == 'No App':
		if start_date:
			start_date = datetime.datetime.strptime(start_date, '%d-%m-%Y').strftime('%Y-%m-%d')
		if frappe.db.exists('Campaign', {'name': campaign_id}):
			current_camp = frappe.get_doc('Campaign', {'name': campaign_id})
			row = current_camp.append("deliverables",{
				"title": title,
				"start_date": start_date,
				"description": description,
				"status": "In Progress"
			})
			current_camp.save(ignore_permissions=True)
			return json.dumps({'Success': 'New deliverable added', 'name': row.name, 'title': title, 'start_date': start_date, 'description': description})
		else:
			return json.dumps({'Error': 'Campaign not found'})
	else:
		return json.dumps({'Error': 'Failed to Authenticate'})

@frappe.whitelist(allow_guest=True)
def update_deliverable_status(campaign_id=None, deliverable_id=None, new_status=None, user=None, pwd=None, files=None):
	# return frappe.request.files.message.campaign_attachment_0
	login_manager = LoginManager()
	login_manager.authenticate(user,pwd)
	login_manager.post_login()
	if frappe.response['message'] == 'Logged In' or frappe.response['message'] == 'No App':
		if frappe.db.exists('Campaign', {'name': campaign_id}):
			result = frappe.db.sql(
						f"""
						UPDATE `tabDeliverable`
						SET status='{new_status}'
						WHERE `parent` = '{campaign_id}' AND name = '{deliverable_id}'
						""", as_dict=1
					)
			return json.dumps({'Success': 'Status Updated!'})
		else:
			return json.dumps({'Error': 'Campaign not found'})
	else:
		return json.dumps({'Error': 'Failed to Authenticate'})

@frappe.whitelist(allow_guest=True)
def get_campaigns_list(search=None):
	campaigns = []
	data = frappe.db.sql(
		f"""
		SELECT table1.*
		FROM `tabCampaign`table1
		WHERE table1.campaign_status = "Open for Proposals" AND table1.campaign_title LIKE '%{search}%'
		""", 
		as_dict=1
	)
	if not data:
		return json.dumps({'Error': 'No Campaign Found'})
	else: 
		for row in data:
			current_row = frappe.db.sql(
				f"""
				SELECT * 
				FROM `tabDeliverable` 
				WHERE parent = "{row.name}"
				""",
				as_dict=1
			)
			row["deliverables"] = current_row
			campaigns.append(row)
		return frappe.as_json(campaigns)
