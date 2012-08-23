#!/usr/bin/env python

from meerkatmon import Strategy, KNOWLEDGE_EXISTS, KNOWLEDGE_NONE

class Ping(Strategy):

	def target_knowledge(self):
		if self.target.netloc:
			return KNOWLEDGE_EXISTS
		return KNOWLEDGE_NONE
