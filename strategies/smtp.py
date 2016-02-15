#!/usr/bin/env python
from smtplib import SMTP, SMTP_SSL, SMTPException
from urllib.error import URLError
from socket import error as SocketError
from lib.strategies import (	BaseStrategy, DeviationCheckMixin,
								KNOWLEDGE_ALIVE,
								KNOWLEDGE_NONE )
from lib.util import (	debug,
						COLOR_LIGHT,
						COLOR_STD )

class Smtp(BaseStrategy, DeviationCheckMixin):

	message = None
	success = False

	OPTION_MAX_DEVIATION = 'max_size_deviation_percentage'

	_options_help = {
		OPTION_MAX_DEVIATION: 'test fails if connect response deviates too much in size',
	}

	@classmethod
	def get_help(cls):
		"""
		Returns general short helpt text for strategy.
		"""
		return 'Used to check SMTPS targets. Checks if HELO/EHLO works.'

	def target_knowledge(self):
		if self.target.scheme.lower() in ("smtp", "smtps", ):
			return KNOWLEDGE_ALIVE
		return KNOWLEDGE_NONE

	def do_check(self):
		"""
		Method does check the server.
		"""

		timeout = self.options.get_int('timeout')
		if self.target.scheme.lower().endswith('s'):
			client = SMTP_SSL(
				None, None, None, None, None, timeout
			)
		else:
			client = SMTP(
				None, None, None, timeout
			)

		netloc = self.target.netloc
		debug("opening smtp to " + netloc)
		try:
			response = client.connect(netloc)
			response_status = response[0]
			response_message = response[1]
			client.quit()
			message = "server said: " + response_message.decode()
			success = response_status == 220
			self.message = message
			self.success = success
			self.check_deviation(response_message)
		except (SocketError, SMTPException, ) as error:
			self.message = str(error)
			self.success = False

		debug("%sreached\n\n'%s'\n" % (
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

	def get_last_check_success(self):
		try:
			return self.success
		except AttributeError:
			raise RuntimeError(
				"strategy asked for success prior callind do_check()"
			)
