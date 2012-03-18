#!/usr/bin/env python

from meerkatmon import Strategy

class Ping(Strategy):

	def target_knowledge(self):
		if self.target.netloc:
			return 1
		return 0
