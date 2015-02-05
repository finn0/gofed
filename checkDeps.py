#!/bin/python

import json
import sys
import Repos
import specParser
import Utils
import optparse

def getGoDeps(path):
	deps = {}
	with open(path, 'r') as file:
		json_deps = json.loads(file.read())

	if "Deps" not in json_deps:
		return {}

	for dep in json_deps["Deps"]:
		if "ImportPath" not in dep or "Rev" not in dep:
			continue

		ip = str(dep["ImportPath"])
		rev = str(dep["Rev"])
		deps[ip] = rev

	return deps


if __name__ == "__main__":

	parser = optparse.OptionParser("%prog [-p] deps.json")

	parser.add_option_group( optparse.OptionGroup(parser, "deps.json", "JSON file with golang deps") )

	parser.add_option(
	    "", "-p", "--pull", dest="pull", action = "store_true", default = False,
	    help = "pull all repositories"
	)

	options, args = parser.parse_args()

	if len(args) != 1:
		print "Synopsis: prog [-p] deps.json"
		exit(1)

	json_file = args[0]

	deps = getGoDeps(json_file)
	if deps == {}:
		print "%s is corrupted or has no dependencies" % json_file
		exit(1)

	im = Repos.loadIMap()
	repos = Repos.parseReposInfo()

	for dep in deps:
		ip = dep
		commit = deps[dep]
		pkg = ''
		if 'golang(%s)' % ip in im:
			pkg, _ = im['golang(%s)' % ip]
		else:
			print "import path %s not found" % ip
			continue

		if pkg not in repos:
			print "package %s not found in golang.repos" % pkg
			continue

		path, upstream = repos[pkg]
		ups_commits = Repos.getRepoCommits(path, upstream, pull=options.pull)
		pkg_commit  = specParser.getPackageCommits(pkg)

		# now fedora and commit, up to date?
		if commit not in ups_commits:
			print "%s: upstream commit not found" % pkg
			continue

		if pkg_commit not in ups_commits:
			print "%s: package commit not found" % pkg
			continue

		commit_ts = int(ups_commits[commit])
		pkg_commit_ts = int(ups_commits[pkg_commit])

		if commit == pkg_commit:
			print "%spackage %s up2date%s" % (Utils.GREEN, pkg, Utils.ENDC)
		elif commit_ts > pkg_commit_ts:
			print "%spackage %s outdated%s" % (Utils.RED, pkg, Utils.ENDC)
		else:
			print "%spackage %s has newer commit%s" % (Utils.YELLOW, pkg, Utils.ENDC)

	

