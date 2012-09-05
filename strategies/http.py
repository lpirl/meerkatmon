#!/usr/bin/env python
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from meerkatmon import (	Strategy,
							debug,
							KNOWLEDGE_ALIVE,
							KNOWLEDGE_NONE,
							COLOR_LIGHT,
							COLOR_STD )

class Http(Strategy):

	def target_knowledge(self):
		if self.target.scheme.lower() in ("http", "https", ):
			return KNOWLEDGE_ALIVE
		return KNOWLEDGE_NONE

	def do_check(self):
		try:
			try:
				response = urlopen(
					self.target.geturl(),
					timeout = int(self.options.get('timeout', '5'))
				)
			except HTTPError as e:
				response = e

			self.output = response.msg
			self.success = response.code == 200

		except URLError as e:
			self.success = False
			self.output = str(e.reason)

		debug("  had %ssuccess \n\n'%s'\n" % (
			'NO ' if not self.success else '',
			''.join([COLOR_LIGHT, self.output, COLOR_STD])
		))

	def get_mail_message(self):
		return '\n'.join([
			self.get_mail_subject(),
			"",
			" Output ".center(30, '-'),
			self.output,
			"".center(30, '-')
		])

	def get_mail_subject(self):
		return "%s getting '%s'!" % (
			'Success' if self.success else 'Error',
			self.target.netloc
		)

	def get_last_check_success(self):
		try:
			return self.success
		except AttributeError:
			raise RuntimeError(
				"strategy asked for success prior callind do_check()"
			)
