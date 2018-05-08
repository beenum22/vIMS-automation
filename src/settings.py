import os
import argparse
import ConfigParser
from urlparse import urlparse
import logging

logger = logging.getLogger(__name__)


class Settings(object):

    def __init__(self, settings_file):
        self.settings_file = settings_file
        self.conf = ConfigParser.ConfigParser()

    def parse_settings_file(self):
        """ Fetching settings present in Settings file"""
        assert os.path.isfile(
            self.settings_file), self.settings_file + ' file not found'
        try:
            self.conf.read(self.settings_file)
        except ConfigParser.MissingSectionHeaderError as e:
            raise e
        # Fetching section present in the ini file
        settings = {}
        sections = self.conf.sections()
        for section in sections:
            settings[section] = self._get_settings_section(section)
        self.__dict__ = settings

        return settings

    def _get_settings_section(self, section):
        """ Parse the specfic section/stanza in the settings file"""
        dict = {}
        try:
            options = self.conf.options(section)

        except ConfigParser.NoSectionError:
            raise "Section not found."

        for option in options:
            try:
                dict[option] = self.conf.get(section, option)
            except ConfigParser.NoSectionError:
                raise "Exception in ", option
                dict[option] = None
        return dict
