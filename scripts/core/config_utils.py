import configparser


from core.core_paths import MAYA_CONFIG


class MayaConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()

        if MAYA_CONFIG.exists():
            self.config.read(MAYA_CONFIG.as_posix())

    def set(self, section: str, option: str, value, save: bool = False):
        """
        Set a config value
        :param section:
        :param option:
        :param value:
        :param save:
        """
        if not self.config.has_section(section):
            self.config.add_section(section)

        self.config[section][option] = value

        if save:
            self.save()

    def get(self, section: str, option: str) -> str or None:
        """
        Get a config value
        :param section:
        :param option:
        :return:
        """
        if self.config.has_section(section=section):
            return self.config.get(section=section, option=option)
        else:
            return None

    def save(self):
        """
        Save the config file
        """
        MAYA_CONFIG.parent.mkdir(exist_ok=True)
        with open(MAYA_CONFIG.as_posix(), 'w') as configfile:
            self.config.write(configfile)
