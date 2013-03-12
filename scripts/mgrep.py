#!C:\Python27\python.exe

import multiprocessing
import optparse
import os
import sys
import time


def HumanizeQuantity(quantity, unit):
	prefixes = ('', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi')
	for prefix in prefixes:
		if quantity < 1024:
			break
		quantity /= 1024.0
	else:
		prefix = '?i'
	return '%.2f %s%s' % (quantity, prefix, unit)


def grep(args):
	patterns, filename, ignorePreprocessor = args
	try:
		with open(filename) as fd:
			if ignorePreprocessor:
				matchs = list()
				for lineno, line in	enumerate(fd):
					line = line.strip()
					if line.startswith('#'):
						continue
					if all((pattern in line for pattern in patterns)):
						matchs.append((lineno + 1, line))
				return (filename, matchs)
			else:
				return (filename, [(lineno + 1, line.strip())	for lineno, line in
					enumerate(fd) if all((pattern in line for pattern in patterns))])
	except IOError, e:
		# print 'ERROR processing "%s": %s' % (filename, str(e))
		return (filename, list())


def mgrep(patterns, options, rootPath=None):
	extensions = options.extensions
	excludeDirs = options.excludeDirs
	recursive = options.recursive
	ignorePreprocessor = options.ignorePreprocessor
	rootPath = rootPath or '.'

	extStr = extensions and \
			'%s' % ', '.join(['*%s' % e for e in extensions]) or 'all files'
	recStr = recursive and 'recursively' or 'non-recursively'
	print 'mgrep %s in %s, %s, "%s"' % (' & '.join(['"%s"' % pattern for pattern in patterns]),
			extStr, recStr, rootPath)

	filenames = list()
	for root, dirs, files in os.walk(rootPath):
		if extensions:
			filenames.extend([os.path.join(root, filename) for filename in files
				if os.path.splitext(filename)[1] in extensions])
		else:
			filenames.extend([os.path.join(root, filename) for filename in files])

		if not recursive:
			break

		map(dirs.remove, [eDir for eDir in excludeDirs if eDir in dirs])

	totalSize = sum([os.stat(filename).st_size for filename in filenames])
	totalTime = time.clock()
	pool = multiprocessing.Pool()
	resultDict = dict()
	for result in pool.imap(grep, [(patterns, filename, ignorePreprocessor) for filename in filenames]):
		filename, matchs = result
		for lineno, match in matchs:
			print '  %s(%d): %s' % (filename, lineno, match)
		if len(matchs):
			resultDict[filename] = len(matchs)
	totalTime = time.clock() - totalTime

	print '  Matching lines: %d    Matching files: %d' \
			'    Total files searched: %d    Total time: %.2fs (%s)' % \
			(sum(resultDict.values()), len(resultDict), len(filenames), totalTime,
					HumanizeQuantity(totalSize / totalTime, 'B/s'))


if __name__ == '__main__':
	usage = 'Usage: %prog [options] <pattern> [pattern] ...'
	parser = optparse.OptionParser(usage=usage)
	parser.add_option('--ext', dest='extensions', action='append',
			default=list(), help='extension for filtering files to process')
	parser.add_option('-p', '--path', dest='rootPath', default=None,
			help='root path to begin the search')
	parser.add_option('--no-recursive', dest='recursive',
			action='store_false', default=True, help='disable recursive search')
	parser.add_option('--solution', dest='solution', default=None,
			help='solution filename to infer root of search')
	parser.add_option('--exclude-dir', dest='excludeDirs', action='append',
			default=list(), help='directory exclusion to consider')
	parser.add_option('--default-extensions', dest='defaultExtensions',
			action='store_true', default=False, help='filter by common extensions')
	parser.add_option('--ignore-preprocessor', dest='ignorePreprocessor',
			action='store_true', default=False, help='ignore preprocessor directives')
	options, args = parser.parse_args()

	if not len(args):
		parser.print_help()
		print '\nERROR: No pattern provided'
		sys.exit(1)

	if options.rootPath:
		rootPath = options.rootPath
	elif options.solution:
		rootPath = options.solution.replace('_root.sln', '')
		if not os.path.isdir(rootPath):
			rootPath = '.'
	else:
		rootPath = '.'

	if options.defaultExtensions:
		defaultExtensions = '.cpp;.cxx;.cc;.c;.inl;.h;.hpp;.hxx;.hm'.split(';')
		options.extensions = list(set(options.extensions + defaultExtensions))

	mgrep(args, options, rootPath)


