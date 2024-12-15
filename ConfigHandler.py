import configparser
from enum import Enum


class DefaultConfig(Enum):
	SERVERSIDE_RANDOM_PLAYER_ORDER = ("player_random_order", "True")

	def key(self):
		return self.value[0]

	def default(self):
		return self.value[1]


class ConfigHandler:
	def __init__(self, main):
		self.main = main
		self.configFile = "config.ini"
		self.config = configparser.ConfigParser()
		self.config.optionxform = str
		self.config.read(self.configFile)

	def get(self, section: str, key: str):
		if not self.config.has_section(section):
			raise KeyError(f"Section '{section}' not found in config.")
		if not self.config.has_option(section, key):
			raise KeyError(f"Key '{key}' not found in section '{section}' in config.")
		return self.config.get(section, key)

	def get(self, enum: DefaultConfig):
		section = enum.name.split('_')[0].lower()
		key = enum.key()
		return self.config.get(section, key)

	def set(self, section: str, key: str, value: str):
		if not self.config.has_section(section):
			self.config.add_section(section)
		self.config.set(section, key, value)

	def setDefaults(self):
		for item in DefaultConfig:
			section = item.name.split('_')[0].lower()
			key = item.key()
			value = item.default()
			if not self.config.has_section(section):
				self.config.add_section(section)
			self.config.set(section, key, value)
			self.save()

	def save(self):
		with open(self.configFile, "w") as configfile:
			self.config.write(configfile)
