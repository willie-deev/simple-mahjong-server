import configparser


class ConfigHandler:
	def __init__(self, main):
		self.main = main
		self.config = configparser.ConfigParser()
		self.config.optionxform = str
		self.config.read('config.ini')

	def get(self, section, option):
		value = self.config.get(section, option)
		return value

	def getBool(self, section, option):
		value = self.config.getboolean(section, option)
		return value

	def setDefault(self, section, option, value):
		if not self.config.has_section(section):
			self.config.add_section(section)
		if not self.config.has_option(section, option):
			self.config.set(section, option, str(value))

	def setDefaults(self):
		self.setDefault("standard", "playerRandomOrder", True)
		with open('config.ini', 'w') as configfile:
			self.config.write(configfile)
