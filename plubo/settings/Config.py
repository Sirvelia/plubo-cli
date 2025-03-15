import os
import json

CONFIG_FILE = os.path.expanduser("~/.pb_cli_config.json")

class Config:
    @staticmethod
    def _load_config():
        """Loads the configuration file if it exists."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                return {}
        return {}

    @staticmethod
    def _save_config(config):
        """Saves the configuration to the file."""
        with open(CONFIG_FILE, "w") as file:
            json.dump(config, file, indent=4)
    
    @classmethod
    def set(cls, section, key, value):
        """Sets a configuration value."""
        config = cls._load_config()
        if section not in config:
            config[section] = {}
        config[section][key] = value
        cls._save_config(config)
    
    @classmethod
    def get(cls, section, key, default=None):
        """Gets a configuration value."""
        config = cls._load_config()
        return config.get(section, {}).get(key, default)
    
    @classmethod
    def delete(cls, section, key):
        """Deletes a configuration key."""
        config = cls._load_config()
        if section in config and key in config[section]:
            del config[section][key]
            cls._save_config(config)
    
    @classmethod
    def clear_section(cls, section):
        """Clears all settings under a section."""
        config = cls._load_config()
        if section in config:
            del config[section]
            cls._save_config(config)
    
    @classmethod
    def clear_all(cls):
        """Clears the entire configuration file."""
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
    
    @classmethod
    def sections(cls):
        """Returns a list of all top-level sections in the configuration."""
        return list(cls._load_config().keys())
