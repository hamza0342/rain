# Copyright (c) 2022, MicroMerger and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Proposal(Document):
	def before_insert(self):
		roles = frappe.get_roles(frappe.session.user)
		user = frappe.session.user
		if not self.campaign:
			frappe.throw('You can only create a proposal through Campaign detail page.')
		if "Academia" in roles:
			if frappe.db.exists("Proposal",{"submitted_by": user, "campaign": self.campaign}):
				frappe.throw("You have already submitted a proposal for this campaign")
			campaign = frappe.get_doc('Campaign', self.campaign)
			if campaign:
				if campaign.industry:
					self.industry = campaign.industry
			self.submitted_by = user 

		else:
			frappe.throw('Only Academia user can submit a proposal')

	def after_insert(self):
		proposal = frappe.get_doc('Proposal', self.name)
		proposal.status = "Submitted"
		proposal.save(ignore_permissions=True)
