#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
  ioprofiler: Performs I/O profiling based on strace.
  Authors = Rafael Treviño <skasi.7@gmail.es>
  Date = 13/08/12
"""

# Imports externals
import fnmatch
import logging
import optparse
import os
import re
import subprocess
import sys
import tempfile

# Imports internals


class File(object):

  def __init__(self, filename):
    object.__init__(self)
    self.__filename = filename
    self.__writeLog = dict()
    self.__writeTime = 0.0
    self.__readLog = dict()
    self.__readTime = 0.0

  def getFilename(self):
    return self.__filename

  def write(self, amount, time):
    if self.__writeLog.has_key(amount):
      self.__writeLog[amount] += 1
    else:
      self.__writeLog[amount] = 1
    self.__writeTime += time

  def read(self, amount, time):
    if self.__readLog.has_key(amount):
      self.__readLog[amount] += 1
    else:
      self.__readLog[amount] = 1
    self.__readTime += time

  def log(self):
    if not self.__writeLog and not self.__readLog:
      return

    retStr = """Filename: %s""" % self.__filename
    if self.__writeLog:
      retStr += """
Write log (total time %.2fms):
%s
""" % (self.__writeTime * 1000,
    '\n'.join(['%d write%s of %d bytes' % (qty, qty != 1 and 's' or '', bytes) for bytes, qty in self.__writeLog.iteritems()]))
    if self.__readLog:
      retStr += """
Read log (total time %.2fms):
%s
""" % (self.__readTime * 1000,
    '\n'.join(['%d read%s of %d bytes' % (qty, qty != 1 and 's' or '', bytes) for bytes, qty in self.__readLog.iteritems()]))
    print retStr


class FileManager(object):

  def __init__(self, filenamePattern=None):
    object.__init__(self)
    self.__activeFiles = {
        0: File('<stdin>'),
        1: File('<stdout>'),
        2: File('<stderr>')
      }
    self.__closedFiles = []
    self.__filenameRe = filenamePattern and re.compile(fnmatch.translate(filenamePattern)) or None

  def open(self, filename, fd):
    logging.debug('Opened "%s" as fd %d' % (filename, fd))
    self.__activeFiles[fd] = File(filename)

  def write(self, fd, amount, time):
    logging.debug('Wrote %d bytes from fd %d' % (amount, fd))
    self.__activeFiles[fd].write(amount, time)

  def read(self, fd, amount, time):
    logging.debug('Red %d bytes from fd %d' % (amount, fd))
    self.__activeFiles[fd].read(amount, time)

  def close(self, fd):
    logging.debug('Closed fd %d' % (fd, ))
    self.__closedFiles.append(self.__activeFiles.pop(fd))

  def logAll(self):
    for file in self.__closedFiles:
      if not self.__filenameRe or self.__filenameRe.match(file.getFilename()):
        file.log()
    for _, file in self.__activeFiles.iteritems():
      if not self.__filenameRe or self.__filenameRe.match(file.getFilename()):
        file.log()


class MatchEvent(object):
  _prog = None

  def match(self, matchLine):
    if self._prog is None:
      return # No prog pattern to match
    matchObj = self._prog.match(matchLine)
    if matchObj is None:
      logging.debug('Unable to match %s' % matchLine)
      return # Not a match

    self._match(matchObj)

  def _match(self, matchObj):
    raise NotImplementedError


class OpenEvent(MatchEvent):
  _prog = re.compile(r'\(\"([^\"]+)\", ([_|A-Z]+)(, \d+)?\)[ ]+= (-?\d+)[^\<]+\<([.\d]+)\>')

  def _match(self, matchObj):
    fd = int(matchObj.group(4))
    if fd < 0:
      return # Some error in the open
    fileManager.open(matchObj.group(1), fd)


class IOEvent(MatchEvent):
  _prog = re.compile(r'\((\d+), \"(.*)\"\.*, (\d+)\)[ ]+= (\d+)[^\<]+\<([.\d]+)\>')

  def _getData(self, matchObj):
    return (int(matchObj.group(1)),
        int(matchObj.group(4)),
        float(matchObj.group(5)))


class WriteEvent(IOEvent):

  def _match(self, matchObj):
    data = self._getData(matchObj)
    fileManager.write(data[0], data[1], data[2])


class ReadEvent(IOEvent):

  def _match(self, matchObj):
    data = self._getData(matchObj)
    fileManager.read(data[0], data[1], data[2])


class CloseEvent(MatchEvent):
  _prog = re.compile(r'\((\d+)\)')

  def _match(self, matchObj):
    fd = int(matchObj.group(1))
    fileManager.close(fd)


class UnknownEvent(MatchEvent):

  def match(self, matchLine):
    logging.error('Invalid line: %s' % matchLine)


syscallDict = {
    'open': OpenEvent(),
    'write': WriteEvent(),
    'read': ReadEvent(),
    'close': CloseEvent()
  }


def profileIt(args):
  params = ['strace'
      , '-ffT'
      , '-e', 'trace=open,close,read,write'] + args
  logging.info('Running "%s"' % ' '.join(params))

  null = open('/dev/null', 'wb')
  strace = subprocess.Popen(params, stdout=null, stderr=subprocess.PIPE)

  _, stderr = strace.communicate()
  if strace.returncode:
    logging.error('strace ended abnormally with return code %d: %s' % (strace.returncode, stderr.strip()))
    return 3

  unknownEvent = UnknownEvent()

  prog = re.compile(r'([^\(]+)(\(.+)')
  for line in stderr.splitlines():
    matchObj = prog.match(line)
    if matchObj is None:
      continue # Not a match
    
    syscall = matchObj.group(1)
    if syscallDict.has_key(syscall):
      syscallDict[syscall].match(matchObj.group(2))
    else:
      unknownEvent.match(line)

  return 0


# Main entry point
if __name__ == '__main__':
  usage = 'Usage: %prog [options]'
  parser = optparse.OptionParser(usage=usage)
  parser.add_option('-l', '--log_level', dest='logLevel', default='INFO',
      help='log level [INFO]')
  programName, _ = os.path.splitext(sys.argv[0])
  parser.add_option('-f', '--log_file', dest='logFile', default='%s.log' % programName,
      help='log file [%s.log]' % programName)
  parser.add_option('-p', '--patternr', dest='filenamePattern', default=None,
      help='profile only files with this filename pattern')
  options, args = parser.parse_args()

  loggingFormat = '%(asctime)s %(levelname)s %(message)s'
  numericLevel = getattr(logging, options.logLevel.upper(), None)
  if not isinstance(numericLevel, int):
    print 'ERROR: Invalid log level: %s' % options.logLevel
    sys.exit(2)
  if options.logFile == '-':
    options.logFile = None

  # Define logging
  logging.basicConfig(format=loggingFormat, level=numericLevel, filename=options.logFile, filemode='w')

  fileManager = FileManager(options.filenamePattern)
  retCode = profileIt(args)
  fileManager.logAll()

  sys.exit(retCode)

