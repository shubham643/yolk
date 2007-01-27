#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

Name: yolk.py

Desc: Command-line tool for listing Python packages installed by setuptools,
      package metadata, package dependencies, and querying The Cheese Shop
      (PyPI) for Python package release information.

Author: Rob Cakebread <gentoodev a t gmail.com>

License  : PSF (Python Software Foundation License)

"""

import sys
import optparse
import pkg_resources
import webbrowser

from yolklib import __version__
from yolklib.metadata import get_metadata
from yolklib.yolklib import Distributions
from yolklib.pypi import CheeseShop


#Functions for obtaining info about packages installed with setuptools
##############################################################################

def show_deps(pkg_ver):
    """Show dependencies for package(s)"""

    try:
        (pkg_name, ver) = pkg_ver[0].split("=")
    except ValueError:
        pkg_name = pkg_ver[0]
        ver = None

    pkgs = pkg_resources.Environment()

    if not len(pkgs[pkg_name]):
        print >> sys.stderr, "Can't find package for %s" % pkg_name
        sys.exit(2)

    for pkg in pkgs[pkg_name]:
        if not ver:
            print pkg.project_name, pkg.version
        #XXX accessing protected member. There's a better way.
        i = len(pkg._dep_map.values()[0])
        if i:
            while i:
                if not ver or ver and pkg.version == ver:
                    if ver and i == len(pkg._dep_map.values()[0]):
                        print pkg.project_name, pkg.version
                    print "  " + str(pkg._dep_map.values()[0][i - 1])
                i -= 1
        else:
            print >> sys.stderr, \
                "No dependency information was supplied with the package."
            sys.exit(2)

def print_metadata(show, metadata, active, show_metadata, fields):
    """Print out formatted metadata"""
    version = metadata['Version']
    #When showing all packages, note which are not active:
    if show == "all" and not active:
        active = " *"
    else:
        active = ""

    print '%s (%s)%s' % (metadata["Name"], version, active)

    if fields:
        #Only show specific fields
        for field in metadata.keys():
            if field in fields:
                print "    %s: %s" % (field, metadata[field])
    elif show_metadata:
        #Print all available metadata fields
        for field in metadata.keys():
            if field != "Name" and field != "Summary":
                print "    %s: %s" % (field, metadata[field])
    else:
        #Default when listing packages
        print "    %s" % metadata["Summary"]
    print 

def show_distributions(show, pkg_name, version, show_metadata, fields):
    """Show list of installed activated OR non-activated packages"""
    dists = Distributions()
    results = 0
    for dist, active in dists.get_distributions(show, pkg_name, version):
        metadata = get_metadata(dist)
        print_metadata(show, metadata, active, show_metadata, fields)
        results += 1
    if show == "all" and results:
        print "Versions with '*' are non-active."

#PyPI functions
##############################################################################
def get_download_links(package_name, version):
    """Query PyPI for pkg download URI for a packge"""
    if version:
        versions = (version)
    else:
        #If they don't specify version, show em all.
        (package_name, versions) = PYPI.query_versions_pypi(package_name, None)
    
    for ver in versions:
        metadata = PYPI.release_data(package_name, ver)
        #Try the package's metadata in case there's nothing with release_urls
        if metadata.has_key('download_url'):
            print metadata['download_url']

        for urls in PYPI.release_urls(package_name, ver):
            print urls['url']
def browse_website(package_name, browser = None):
    """Launch web browser at project's homepage"""
    #Get verified name from pypi.
    (pypi_pkg_name, versions) = PYPI.query_versions_pypi(package_name)
    if len(versions):
        metadata = PYPI.release_data(pypi_pkg_name, versions[0])
        if metadata.has_key("home_page"):
            print "Launching browser: %s" % metadata['home_page']
            if browser == 'konqueror':
                browser = webbrowser.Konqueror()
            else:
                browser = webbrowser.get()
            try:
                browser.open(metadata['home_page'], 2)
            except AttributeError:
                browser.open(metadata['home_page'], 2)
            return

    print "No homepage URL found."

def show_pkg_metadata_pypi(package_name, version):
    """Show pkg metadata queried from PyPI"""

    metadata = PYPI.release_data(package_name, version)
    for key in metadata.keys():
        print "%s: %s" % (key, metadata[key])

def get_all_versions_pypi(package_name, use_cached_pkglist):
    """Fetch list of available versions for a package from The Cheese Shop"""
    (pypi_pkg_name, versions) = PYPI.query_versions_pypi(package_name,
            use_cached_pkglist)

    #pypi_pkg_name may != package_name; it returns the name with correct case
    #i.e. You give beautifulsoup but PyPI knows it as BeautifulSoup

    if versions:
        print_pkg_versions(pypi_pkg_name, versions)
    else:
        print >> sys.stderr, "Nothing found on PyPI for %s" % \
            package_name
        sys.exit(2)

def pypi_search(spec):
    """Search PyPI by metadata keyword"""
    keyword = spec[0]
    term = " ".join(spec[1:])
    spec = {}
    spec[keyword] = term
    for pkg in PYPI.search(spec): 
        print "%s (%s):\n    %s\n" % (pkg['name'], pkg['version'], 
                pkg['summary'])

def get_rss_feed():
    """Show last 20 package updates from PyPI RSS feed"""
    rss = PYPI.get_rss()
    for pkg in rss.keys():
        print "%s\n    %s\n" % (pkg, rss[pkg])

#Utility functions
##############################################################################

def parse_pkg_ver(args):
    """Return tuple with package_name and version from CLI args"""

    version = package = None
    if len(args) == 1:
        package = args[0]
    elif len(args) == 2:
        package = args[0]
        version = args[1]
    return (package, version)

def print_pkg_versions(package_name, versions):
    """Print list of versions available for a package"""

    for ver in versions:
        print "%s %s" % (package_name, ver)

def setup_opt_parser():
    """Setup the optparser"""
    usage = "usage: %prog [options] <package_name> <version>"
    opt_parser = optparse.OptionParser(usage=usage)
    opt_parser.add_option("-v", "--version", action='store_true', dest=
                         "version", default=False, help=
                         "Show yolk version and exit.")

    group_local = optparse.OptionGroup(opt_parser, 
            "Query installed Python packages",
            "The following options show information about Python packages "
            "installed by setuptools. Activated packages are normal packages "
            "on sys.path that can be imported. Non-activated packages need "
            "'pkg_resources.require()' before they can be imported, such as "
            "packages installed with 'easy_install --multi-version'")

    group_local.add_option("-l", "--list", action='store_true', dest='all', 
                         default=False, help=
                         "List all packages installed by setuptools.")

    group_local.add_option("-a", "--activated", action='store_true', dest=
                         'active', default=False, help=
                         "List only activated packages installed by "
                         "setuptools.")

    group_local.add_option("-n", "--non-activated", action='store_true', 
                         dest='nonactive', default=False, help=
                         "List only non-activated packages installed by "
                         "setuptools.")

    group_local.add_option("-m", "--metadata", action='store_true', dest=
                         "metadata", default=False, help=
                         "Show all metadata for packages installed by "
                         "setuptools (use with -l -a or -n)")

    group_local.add_option("-f", "--fields", action="store", dest="fields", 
                         default=False, help=
                         "Show specific metadata fields. "
                         "(use with -l -a or -n)")

    group_local.add_option("-d", "--depends", action='store_true', dest=
                         "depends", default=False, help=
                         "Show dependencies for a package installed by " +
                         "setuptools if they are available. " +
                         "(use with -l -a or -n)")

    group_pypi = optparse.OptionGroup(opt_parser, "PyPI (Cheese Shop) options",
            "The following options query the Python Package Index:")


    group_pypi.add_option("-C", "--use-cached-pkglist", action=
                         'store_true', dest="use_cached_pkglist", 
                         default=False, help=
                         "Use cached package list instead of querying PyPI " + 
                         "(Use -F to force retrieving list.)")

    group_pypi.add_option("-D", "--download-links", action='store_true', 
                         dest="download_links", default=False, help=
                         "Show download URL's for package listed on PyPI. ")

    group_pypi.add_option("-F", "--fetch-package-list", action=
                         'store_true', dest="fetch_package_list", 
                         default=False, help=
                         "Fetch and cache list of packages from PyPI.")

    group_pypi.add_option("-H", "--browse-homepage", action=
                         'store_true', dest="browse_website", 
                         default=False, help=
                         "Launch web browser at home page for package.")

    group_pypi.add_option("-L", "--latest", action=
                         'store_true', dest="rss_feed", 
                         default=False, help=
                         "Show last 20 updates on PyPI.")

    group_pypi.add_option("-M", "--query-metadata", action=
                         'store_true', dest="query_metadata_pypi", 
                         default=False, help=
                         "Show metadata for a package listed on PyPI.")

    group_pypi.add_option("-S", "--search", action=
                         'store_true', dest="search", 
                         default=False, help=
                         "Search PyPI by spec and operator.")

    group_pypi.add_option("-V", "--versions-available", action=
                         'store_true', dest="versions_available", 
                         default=False, help=
                         "Show available versions for given package " + 
                         "listeded on PyPI.")
    opt_parser.add_option_group(group_local)
    opt_parser.add_option_group(group_pypi)
    return opt_parser


def main():
    """Main function"""
    opt_parser = setup_opt_parser()
    (options, remaining_args) = opt_parser.parse_args()

    if options.search:
        if len(remaining_args):
            pypi_search(remaining_args)
        else:
            opt_parser.print_help()
        sys.exit(0)

    if len(sys.argv) == 1 or len(remaining_args) > 2:
        opt_parser.print_help()
        sys.exit(2)
    (package, version) = parse_pkg_ver(remaining_args)

    if options.version:

        print "Version %s" % __version__.version
    elif options.depends:

        if not remaining_args:
            print >> sys.stderr, "I need at least a package name."
            print >> sys.stderr, \
                "You can also specify a package name and version:"
            print >> sys.stderr, "  yolk.py -d kid 0.8"
            sys.exit(2)
        show_deps(remaining_args)
    elif options.all:

        if options.active or options.nonactive:
            opt_parser.print_help()
            sys.exit(2)
        show_distributions("all", package, version, options.metadata,
                options.fields)

    elif options.active:

        if options.all or options.nonactive:
            opt_parser.print_help()
            sys.exit(2)
        show_distributions("active", package, version, options.metadata,
                options.fields)

    elif options.nonactive:

        if options.active or options.all:
            opt_parser.print_help()
            sys.exit(2)
        show_distributions("nonactive", package, version, options.metadata,
                options.fields)
    elif options.versions_available:

        get_all_versions_pypi(package, options.use_cached_pkglist)
    elif options.browse_website:
        browse_website(package)

    elif options.fetch_package_list:

        PYPI.store_pkg_list()
    elif options.download_links:
        get_download_links(package, version)

    elif options.rss_feed:
        get_rss_feed()

    elif options.query_metadata_pypi:

        if version:
            show_pkg_metadata_pypi(package, version)
        else:

            #If they don't specify version, show all.

            (package, versions) = PYPI.query_versions_pypi(package, None)
            for ver in versions:
                show_pkg_metadata_pypi(package, ver)
    else:
        opt_parser.print_help()
        sys.exit(2)

PYPI = CheeseShop()

if __name__ == "__main__":
    main()
