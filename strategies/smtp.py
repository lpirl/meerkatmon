#!/usr/bin/env python
from smtplib import SMTP, SMTP_SSL, SMTPException
from urllib.error import URLError
from socket import error as SocketError
from lib.strategies import (	BaseStrategy,
								KNOWLEDGE_ALIVE,
								KNOWLEDGE_NONE )
from lib.util import (	debug,
						COLOR_LIGHT,
						COLOR_STD )

class Smtp(BaseStrategy):

	message = None
	success = False

	def target_knowledge(self):
		if self.target.scheme.lower() in ("smtp", "smtps", ):
			return KNOWLEDGE_ALIVE
		return KNOWLEDGE_NONE

	def do_check(self):
		"""
		Method does check the server.
		"""

		timeout = int(self.options['timeout'])
		if self.target.scheme.lower().endswith('s'):
			smtp_cls = lambda netloc: SMTP_SSL(
				netloc, None, None, None, None, timeout
			)
		else:
			smtp_cls = lambda netloc: SMTP(
				netloc, None, None, timeout
			)

		netloc = self.target.netloc
		debug("opening smtp to " + netloc)
		try:
			smtp_connection = smtp_cls(netloc)
			response = smtp_connection.noop()
			message = "server said: " + response[1].decode()
			success = response[0] == 250
		except (SocketError, SMTPException, ) as error:
			message = str(error)
			success = False

		self.message = message
		self.success = success

		debug("  %sreached\n\n'%s'\n" % (
			'NOT ' if not self.success else '',
			''.join([COLOR_LIGHT, self.message, COLOR_STD])
		))

	def get_mail_message(self):
		try:
			return self.message
		except AttributeError:
			raise RuntimeError(
				"strategy asked for check result prior callind do_check()"
			)

	def get_mail_subject(self):
		try:
			return "%s getting '%s'!" % (
				'Success' if self.success else 'Error',
				self.target.netloc
			)
		except AttributeError:
			raise RuntimeError(
				"strategy asked for check result prior callind do_check()"
			)

	def get_last_check_success(self):
		try:
			return self.success
		except AttributeError:
			raise RuntimeError(
				"strategy asked for success prior callind do_check()"
			)
