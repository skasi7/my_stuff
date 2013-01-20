#-*- coding: utf-8 -*-

"""
App classes to easy python development.
"""

# Imports externals
import os
import sys
import yaml
import logging
import logging.handlers
import optparse
import simplejson
import ConfigParser

# Imports internals


class NullHandler(logging.Handler):
  """
  Empty logging handler used to avoid the message:
  "No handlers could be found for logger X.Y.Z" for more information, see:
  http://docs.python.org/library/logging.html#configuring-logging-for-a-library
  """

  def emit(self, record):
    """
    Overriden method. Does nothing.

    :param record: Logging record to emit.
    """
    pass

# Avoid duplicated logging entries setting a handler for the root Logger
logging.getLogger().addHandler(NullHandler())


class App(object):
  """
  Application class, bundles optparse and logging together.

  :param appName: Application name.
  :type appName: string

  :param usage: Usage string to use in the option parser.
  :type usage: string
  """

  def __init__(self, appName=None, usage=None):
    object.__init__(self)
    self.__log = logging
    self.__appName = appName or 'app'
    self.__parser = optparse.OptionParser(usage=usage or '%prog [options]')
    self.__configFilenames = []
    self.config = {}

  def __createLoggingOpts(self):
    """
    Method for initializing logging options.

    :raises optparse.OptionError: When SysLog logging is not supported by
      target platform.
    """
    self.__parser.add_option('-e', dest='stderrLevel',
        help='standard error debugging level [error]',
        default='error')

  def __createConfigOpts(self):
    """
    Method for initializing configuration options.
    """
    defaultPath = '/etc/%s.cfg' % (self.__appName)
    configPaths = ['/etc/%s.%s' % (self.__appName, ext) for
        ext in ('cfg', 'yml', 'json')]
    configPaths = [path for path in configPaths if os.path.exists(path)]
    defaultPath = len(configPaths) and configPaths[0] or defaultPath
    self.__parser.add_option('-c', dest='cfgFilename',
        help='configuration filename [%s]' % defaultPath,
        default=defaultPath)

  def __createLoggers(self, options):
    """
    Method for create enabled loggers.

    :raises optparse.OptionValueError: When any logger level is unknown.
    """
    # Logger instance
    # Setting the NullHandler, for more information, see:
    # http://docs.python.org/library/logging.html#configuring-logging-for-a-library
    logging.getLogger(self.__appName).addHandler(NullHandler())
    logger = logging.getLogger(self.__appName)
    # Formatter instance
    fmt = '%(asctime)s %(name)s %(levelname)s %(message)s'
    formatter = logging.Formatter(fmt)

    handler = self.__createStderrHandler(options.stderrLevel)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.setLevel(logging.DEBUG) # Global level
    self.__log = logger

  def __createStderrHandler(self, level):
    """
    Method for create stderr logger (if enabled).

    :raises optparse.OptionValueError: When StdErr level is unknown.

    :returns: The handler of the logger.
    """
    level = (level == 'no') and 'notset' or level
    handler = logging.StreamHandler()

    try:
      handler.setLevel(eval('logging.%s' % level.upper()))
    except AttributeError:
      raise optparse.OptionValueError, \
          'invalid standard error level %s' % level
    return handler

  def __createConfigurators(self, options):
    """
    Method for create enabled configurations.
    """
    self.__configFilenames.append(options.cfgFilename)

  def __readSimplejsonFilename(self, filename):
    """
    Method for read a simplejson formated filename.

    :param filename: Filename to read.
    :type filename: string

    :raises IOError: If filename is not found.
    :raises ValueError: If file is not json formated.

    :returns: The data dictionary of the json file.
    """
    stream = open(filename)
    data = simplejson.load(stream)
    stream.close()
    return data

  def __readConfigParserFilename(self, filename):
    """
    Method for read a simplejson formated filename.

    :param filename: Filename to read.
    :type filename: string

    :raises: ConfigParser.ParsingError: If unable to read/parse the filename

    :returns: The data dictionary of the ConfigParser file.
    """
    parser = ConfigParser.SafeConfigParser()
    if not parser.read([filename]):
      raise ConfigParser.ParsingError, 'Unable to read/parse file'
    data = {}
    for section in parser.sections():
      sectionData = {}
      for name, value in parser.items(section):
        sectionData[name] = value
      data[section] = sectionData
    return data

  def __readYamlFilename(self, filename):
    """
    Method for read a YAML formated filename.

    :param filename: Filename to read.
    :type filename: string

    :raises IOError: If filename is not found.
    :raises AssertionError: If file is not YAML formatted.

    :returns: The data dictionary of the YAML file.
    """
    stream = open(filename)
    try:
      data = [item for item in yaml.safe_load_all(stream)]
    except yaml.parser.ParserError:
      assert False
    assert len(data) == 1
    return data[0]

  def updateConfig(self, data):
    """
    Method for update the public configuration data dictionary.

    :param data: Data dictionary to use.
    :type data: dict

    :raises RuntimeError: If data is not a dictionary.
    """
    if not isinstance(data, dict):
      raise ValueError, 'data must be a dict instance'
    self.config.update(data)
    self.__log.debug('Config dictionary successfully updated!')

  def parseConfigFilename(self, filename):
    """
    Method for parsing configuration files.

    :param filename: Filename to parse.
    :type filename: string

    :returns: Configuration data parsed or None
    :rtype: dict
    """
    self.__log.debug('Parsing configuration filename "%s".' % filename)

    data = None
    try:
      data = self.__readSimplejsonFilename(filename)
    except IOError:
      self.__log.warning('Filename "%s" not found. Ignored.' % filename)
      return # We know is not found, aborting...
    except ValueError:
      self.__log.debug('Unable to parse "%s" in JSON format.' % filename)

    if data:
      if isinstance(data, dict):
        return data
      else:
        self.__log.warning('Filename "%s" in JSON format, but root must '
            'be a dictionary. Ignored.' % filename)
        return

    try:
      data = self.__readConfigParserFilename(filename)
    except ConfigParser.ParsingError:
      self.__log.debug('Unable to parse "%s" in ConfigParser format.' %
          filename)

    try:
      data = self.__readYamlFilename(filename)
    except IOError:
      self.__log.warning('Filename "%s" not found. Ignored.' % filename)
      return # We know is not found, aborting...
    except AssertionError:
      self.__log.debug('Unable to parse "%s" in YAML format.' %
          filename)

    return data

  def __readConfigurationFilenames(self):
    """
    Method for read all configuration filenames, in ConfigParser or
    simplejson formats. Also can read mixed formats. The results of reading
    such files are stored on the *config* attribute. When reading a
    ConfigParser formated file, config will show a dictionary instead the
    well-known ConfigParser complex API.

    JSON first-level names and ConfigParser sections will collision and being
    overwritten if have the same name.
    """
    for filename in self.__configFilenames:
      data = self.parseConfigFilename(filename)
      if data:
        self.updateConfig(data)

  def add_option(self, *args, **kwargs):
    """
    Overrided version of the optparse.OptionParser.add_option method.

    :raises optparse.OptionError: When some mistake was detected.
    """
    self.__parser.add_option(*args, **kwargs)

  def print_help(self):
    """
    Overrides optparse.OptionParser.print_help.
    """
    self.__parser.print_help()

  def parse_args(self):
    """
    Overrides optparse.OptionParser.parse_args adding the logging creation.

    :returns: A tuple containing the parsed options and the unparsed argument
      list.
    :rtype: tuple
    """
    self.__createLoggingOpts()
    self.__createConfigOpts()
    (options, args) = self.__parser.parse_args()
    self.__createLoggers(options)
    self.__createConfigurators(options)
    self.__readConfigurationFilenames()
    return (options, args)

  def getLogger(self):
    """
    Returns the internal (global) generated logger.

    :returns: The internal logger.
    """
    return self.__log

  def getConfig(self):
    """
    Returns the internal configuration dict.

    :returns: The internal configuration dict.
    :rtype: dict
    """
    return self.config

  def exit(self, value):
    """
    Convenience function to exits program logging the exit.

    :param value: return value to exit with.
    :type value: int
    """
    self.__log.warning('Exitting by application request with %d' % value)
    sys.exit(value)

