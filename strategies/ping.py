#!/usr/bin/env python
from subprocess import check_output, CalledProcessError, STDOUT

from meerkatmon import (	Strategy,
							debug,
							KNOWLEDGE_EXISTS,
							KNOWLEDGE_NONE,
							COLOR_LIGHT,
							COLOR_STD )

class Ping(Strategy):

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
		return "%s pinging '%s'!" % (
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
