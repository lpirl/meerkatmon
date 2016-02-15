#!/usr/bin/env python
from subprocess import check_output, CalledProcessError, STDOUT

from lib.strategies import (	BaseStrategy,
								KNOWLEDGE_EXISTS,
								KNOWLEDGE_NONE )
from lib.util import (	debug,
						COLOR_LIGHT,
						COLOR_STD )

class Ping(BaseStrategy):


	@classmethod
	def get_help(cls):
		"""
		Returns general short helpt text for strategy.
		"""
		return 'Checks if target answers to a ping.'

	def target_knowledge(self):
		if self.target.netloc:
			return KNOWLEDGE_EXISTS
		return KNOWLEDGE_NONE

	def do_check(self):
		cmd = [
			self.which('ping'),
			'-W', self.options.get('timeout', '5'),
			'-c', self.options.get('count', '1'),
			self.target.netloc
		]

		debug("running command: %s" % str(cmd))

		success = True
		try:
			output = check_output(cmd, stderr=STDOUT)
		except CalledProcessError as e:
			success = False
			output = e.output

		self.output = output.decode().strip()
		self.success = success

		debug("had %ssuccess \n\n'%s'\n" % (
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

	def get_last_check_success(self):
		try:
			return self.success
		except AttributeError:
			raise RuntimeError(
				"strategy asked for success prior callind do_check()"
			)
