# kopano4ucsRole UDM hook
#
# Copyright 2012-2016 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

from univention.admin.hook import simpleHook
from univention.admin.localization import translation
from univention.config_registry import ConfigRegistry
ucr = ConfigRegistry()

translation = univention.admin.localization.translation('kopano4ucs')
_ = translation.translate


class kopano4ucsRole(simpleHook):

	type = 'kopano4ucsRole'

	def __isUsersUser(self, module):
		return 'username' in module.descriptions

	def __kopanoRoles(self, module, ml):
		# if role has changed and module is not "settings/usertemplate"
		if self.__isUsersUser(module) and module.hasChanged("kopano-role"):

			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
				'kopano4ucsRole: role has changed %s' % module["kopano-role"])

			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
				'kopano4ucsRole: original modlist %s' % ml)

			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
				'kopano4ucsRole: oldattr %s' % module.oldattr)

			kopanoAccount = 0
			kopanoAdmin = 0
			kopanoSharedStoreOnly = 0
			kopanoContact = 0

			if module["kopano-role"] == "user":
				kopanoAccount = 1
			elif module["kopano-role"] == "admin":
				kopanoAccount = 1
				kopanoAdmin = 1
			elif module["kopano-role"] == "store":
				kopanoSharedStoreOnly = 1
				kopanoAccount = 1
			elif module["kopano-role"] == "contact":
				kopanoContact = 1
				kopanoAccount = 1
			else:
				pass

			# add/remove kopano role
			ml.append((
				"kopanoAccount",
				module.oldattr.get("kopanoAccount", [""])[0],
				"%s" % kopanoAccount))
			ml.append((
				"kopanoAdmin",
				module.oldattr.get("kopanoAdmin", [""])[0],
				"%s" % kopanoAdmin))
			ml.append((
				"kopanoSharedStoreOnly",
				module.oldattr.get("kopanoSharedStoreOnly", [""])[0],
				"%s" % kopanoSharedStoreOnly))

			# add/remove objectClass kopano-contact
			if kopanoContact:
				if not "kopano-contact" in module.oldattr.get("objectClass", []):
					ml.append(("objectClass", "", "kopano-contact"))
			else:
				if "kopano-contact" in module.oldattr.get("objectClass", []):
					ml.append(("objectClass", "kopano-contact", ""))

			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
				'kopano4ucsRole: changed modlist %s' % ml)

		return ml

	def hook_ldap_post_modify(self, module):
		pass

	def hook_open(self, module):
		pass

	def hook_ldap_pre_create(self, module):
		if "mailPrimaryAddress" in module and not module.get("mailPrimaryAddress"):
			module["kopano-role"] = "none"

		if "mailPrimaryAddress" in module and module.get("mailPrimaryAddress") and module["kopano-role"] == "none":
			module["kopano-role"] = "user"
		pass

	def hook_ldap_addlist(self, module, al=[]):
		al = self.__kopanoRoles(module, al)
		return al

	def hook_ldap_post_create(self, module):
		pass

	def hook_ldap_pre_modify(self, module):
		# kopano-role not 'none' and no mailPrimaryAddress specified
		if "mailPrimaryAddress" in module and not module.get("mailPrimaryAddress") and module["kopano-role"] and not module["kopano-role"] in ["none", "contact"]:
			raise univention.admin.uexceptions.valueError, _("Kopano users must have a primary e-mail address specified.")
		pass

	def hook_ldap_modlist(self, module, ml=[]):
		ucr.load()
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "hook_ldap_modlist: ml: %s" % ml)

		# email address added, but kopano-role unchanged and "none": user probably wants that user to be a kopano-user
		if module.hasChanged('mailPrimaryAddress') and not module.oldattr.get("mailPrimaryAddress", [""])[0] and not module.hasChanged('kopano-role') and module.get("kopano-role") == "none" and ucr.is_true('kopano/createkopanouserswithvalidemail', True):
			module["kopano-role"] = "user"
			ml.append(("kopano4ucsRole", "none", "user"))

		# set kopano role flags
		ml = self.__kopanoRoles(module, ml)

		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "hook_ldap_modlist: ml after modification: %s" % ml)
		return ml

	def hook_ldap_pre_remove(self, module):
		pass

	def hook_ldap_post_remove(self, module):
		pass