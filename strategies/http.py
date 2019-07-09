#!/usr/bin/env python
from urllib.request import Request, urlopen as urllib_urlopen
from urllib.error import HTTPError, URLError
from socket import error as socket_error
from ssl import SSLError, CertificateError
from lib.strategies import (	BaseStrategy, DeviationCheckMixin,
								KNOWLEDGE_ALIVE,
								KNOWLEDGE_NONE )
from lib.util import (	debug,
						COLOR_LIGHT,
						COLOR_STD )
from http.client import (	BadStatusLine, HTTPResponse, RemoteDisconnected,
													IncompleteRead)

class Http(BaseStrategy, DeviationCheckMixin):

	OPTION_MAX_DEVIATION = 'max_size_deviation_percentage'
	OPTION_STATUS_CODE = 'status_code'
	OPTION_CHECK_SSL_TOO = 'check_SSL_too'
	OPTION_PRESENT_IN_RESPONSE = 'present_in_response'
	OPTION_ABSENT_IN_RESPONSE = 'absent_in_response'

	_options_help = {
		OPTION_MAX_DEVIATION: ('test fails if response deviates too much in size ' +
													'(absent configuration or negative values disable ' +
													'this check)'),
		OPTION_STATUS_CODE: 'set an expected status code another than 200',
		OPTION_CHECK_SSL_TOO: 'for HTTP targets, check target using HTTPS as well',
		OPTION_PRESENT_IN_RESPONSE: 'test fails if given string not in response',
		OPTION_ABSENT_IN_RESPONSE: 'test fails if given string in response',
	}

	message = None
	success = False
	response_str = None

	def target_knowledge(self):
		if self.target.scheme.lower() in ("http", "https", ):
			return KNOWLEDGE_ALIVE
		return KNOWLEDGE_NONE

	@classmethod
	def get_help(cls):
		"""
		Returns general short helpt text for strategy.
		"""
		return 'Used for HTTP targets.'

	@classmethod
	def urlopen(cls, url, *args, **kwargs):
		"""
		Wraps 'urlopen' provided by 'urllib' to set own user agent.
		"""
		request = Request(
			url,
			None,
			{ 'User-Agent' : 'MeerkatMon (https://github.com/lpirl/meerkatmon)' }
		)
		return urllib_urlopen(request, *args, **kwargs)

	def _do_request(self):
		"""
		Method does actually speak with the target and sets
		self.{message, success, response_str} accordingly.
		"""
		response_str = None
		try:
			try:
				response = Http.urlopen(
					self.target.geturl(),
					timeout = self.options.get_int('timeout', 5)
				)
				response_str = response.read()
			except (HTTPError, SSLError, BadStatusLine, IncompleteRead,
							CertificateError) as e:
				response = e

			response_message = getattr(response, "msg", None)
			if response_message is None:
				message = "no message from server"
			else:
				message = "message from server: '%s'" % response_message

			response_code = getattr(response, "code", None)

			success = response_code == self.options.get_int(
				self.OPTION_STATUS_CODE, 200
			)

		except URLError as e:
			success = False
			message = str(e.reason)

		except socket_error as e:
			success = False
			message = str(type(e)) + ": " + str(e)

		self.message = message
		self.success = success
		self.response_str = response_str

	def _check_response_content(self):
		additional_message = ""

		assert self.response_str is not None

		present = self.options.get_bytes(self.OPTION_PRESENT_IN_RESPONSE)
		if present and present not in self.response_str:
			additional_message += \
				"\nunexpectedly not found in response: '%s'" % present.decode()

		absent = self.options.get_bytes(self.OPTION_ABSENT_IN_RESPONSE)
		if absent and absent in self.response_str:
			additional_message += \
				"\nunexpectedly found in response: '%s'" % absent.decode()

		if additional_message:
			self.message += additional_message
			self.success = False

	def do_check(self):
		"""
		Method coordinates check.
		"""
		self._do_request()

		debug("%sreached\n\n'%s'\n" % (
			'NOT ' if not self.success else '',
			''.join([COLOR_LIGHT, self.message, COLOR_STD])
		))

		if self.response_str is not None:
			self._check_response_content()
		self.check_deviation(self.response_str)

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
