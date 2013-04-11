#!/usr/bin/env python
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from lib.strategies import (	BaseStrategy,
								KNOWLEDGE_ALIVE,
								KNOWLEDGE_NONE )
from lib.util import (	debug,
						COLOR_LIGHT,
						COLOR_STD )

class Http(BaseStrategy):

	OPTION_MAXDEVIATION = 'max_size_deviation_percentage'
	OPTION_STATUSCODE = 'status_code'

	_options_help = {
		OPTION_MAXDEVIATION: 'test fails if response deviates too much in size',
		OPTION_STATUSCODE: 'set an expected status code another than 200',
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

	def _do_request(self):
		"""
		Method does actually speak with the target and sets
		self.{message, success, response_str} accordingly.
		"""
		response_str = None
		try:
			try:
				response = urlopen(
					self.target.geturl(),
					timeout = self.options.get_int('timeout', 5)
				)
				response_str = response.read()
			except HTTPError as e:
				response = e

			message = "server said: " + response.msg
			success = response.code == self.options.get_int(
				self.OPTION_STATUSCODE, 200)

		except URLError as e:
			success = False
			message = str(e.reason)

		self.message = message
		self.success = success
		self.response_str = response_str


	def do_check(self):
		"""
		Method coordinates check.
		"""
		self._do_request()

		debug("%sreached\n\n'%s'\n" % (
			'NOT ' if not self.success else '',
			''.join([COLOR_LIGHT, self.message, COLOR_STD])
		))

		if self.success:
			response_str = self.response_str
			prev_response_str = self.load_sample()
			if prev_response_str is not None:
				self.compare_responses(response_str, prev_response_str)
			self.save_sample(response_str)

	def compare_responses(self, response1, response2):

		try:
			max_deviation = self.options.get_float(
				self.OPTION_MAXDEVIATION,
				None
			)
		except TypeError as e:
			return

		if len(response2):
			deviation = abs((100 * len(response1) / len(response2)) - 100 )
		else:
			deviation = 100
		additional_message = "Deviation in size %f%% (max %f%%)" % (
			deviation, max_deviation
		)

		debug(additional_message)

		self.success = deviation <= max_deviation
		self.message += "\n\n" + additional_message

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
