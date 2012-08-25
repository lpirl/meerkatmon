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
			'/bin/ping',
			'-W', self.options.get('timeout', '5'),
			'-c', self.options.get('count', '1'),
			self.target.netloc
		]

		debug("running command: %s" % unicode(cmd))

		success = True
		try:
			output = check_output(cmd, stderr=STDOUT)
		except CalledProcessError, e:
			success = False
			output = e.output
		output = ''.join([COLOR_LIGHT, output.strip(), COLOR_STD])

		debug("  had %ssuccess '%s'" % ('NO ' if not success else '', output))
