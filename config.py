from configparser import ConfigParser


class ConfigException(Exception):
    pass


class MigrationConfig(ConfigParser):
    def __init__(self, config_file):
        super(MigrationConfig, self).__init__()

        self.read(config_file)
        self.validate_config()

    def validate_config(self):
        required_values = {
            'source': {
                'url': None,
                'username': None,
                'group_id': None,
                'private_token': None,
                'recursive': ('False', 'True')
            },
            'destination': {
                'url': None,
                'username': None,
                'group_id': None,
                'private_token': None,
            },
            'default': {
                'migrate_strategy': ('export-import', 'import-url'),
                'skip_existing': ('True', 'False'),
                'replica': ('source-to-destination', 'destination-to-source', 'both', 'none'),
                'log_level': ('debug', 'info'),
            }
        }
        """
        Notice the different mode validations for global mode setting: we can
        enforce different value sets for different sections
        """

        for section, keys in required_values.items():
            if section not in self:
                raise ConfigException(
                    'Missing section %s in the config file' % section)

            for key, values in keys.items():
                if key not in self[section] or self[section][key] == '':
                    raise ConfigException((
                        'Missing value for %s under section %s in ' +
                        'the config file') % (key, section))

                if values:
                    if self[section][key] not in values:
                        raise ConfigException((
                            'Invalid value for %s under section %s in ' +
                            'the config file') % (key, section))


if __name__ == "__main__":
    cfg = {}

    try:
        # The example config file has an invalid value so cfg will stay empty first
        cfg = MigrationConfig('config.ini')
    except ConfigException as e:
        # Initially you'll see this due to the invalid value
        print(e)
    else:
        # Once you fix the config file you'll see this
        print(cfg['client']['fallback'])