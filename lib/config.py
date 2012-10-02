from lib.util import debug

class FillFromFileDict(dict):
	"""
	Like a dictionary, but can be filled from a config file.
	"""

	def fill_from_file(self, filename):
		"""
		Method loads configuration from file into dictionary.
		"""
		debug("loading configuration from '%s'" % filename)
		fp = open(filename, "r")
		sections = dict()
		options = dict()
		for line in fp.readlines():
			line = line.strip()

			if line.startswith("#"):
				continue

			if line.startswith('[') and line.endswith(']'):
				options = dict()
				sections[line[1:-1].strip()] = options
				continue

			if '=' in line:
				key, value = tuple(line.split("=", 1))
				options[key.strip()] = value.strip()
				continue

		fp.close()
		debug("configuration is: '%s'" % str(sections))

		self.update(sections)

class CastingDict(dict):
	"""
	Like a dictionary, but can privede values casted to some type.
	"""

	def get_int(self, *args, **kwargs):
		"""
		Returns requested value as int
		"""
		return int(super(CastingDict, self).get(*args, **kwargs))

	def get_bool(self, *args, **kwargs):
		"""
		Returns requested value as int
		"""
		return bool(super(CastingDict, self).get(*args, **kwargs))

	def get_float(self, *args, **kwargs):
		"""
		Returns requested value as int
		"""
		return float(super(CastingDict, self).get(*args, **kwargs))

class ConfigDict(FillFromFileDict):
	"""
	Ensures that nested dicts in FillFromFileDict are CastingDict's.
	"""

	def fill_from_file(self, *args, **kwargs):
		"""
		Converts every nested dict to a CastingDict.
		"""
		super(ConfigDict, self).fill_from_file(*args, **kwargs)

		for key, value in self.items():
			self.__setitem__(key, CastingDict(value))
