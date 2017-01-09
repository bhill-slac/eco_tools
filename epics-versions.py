#!/usr/bin/python
import re
import sys
import optparse
import commands
import fileinput
import glob
import os
import pprint
import signal
import traceback

from version_utils import *

#
# Purpose:
#
#   This script searches for releases of EPICS modules and reports
#   which versions are available along with any dependencies.
#
#   However, in addition to EPICS modules, this script can show
#   version information for the following as well:
#
#       base                    - EPICS base
#       modules                 - All modules
#       modules/<mod_name>      - Module named mod_name
#       ioc/common/<ioc_name>   - common IOC named ioc_name
#       ioc/amo/<ioc_name>      - AMO IOC named ioc_name
#       ioc/sxr                 - All SXR IOC's
#       screens/edm/xpp         - XPP edm control room screens
#       screens                 - All control room screens
#       etc.
#
#   If a release has a configure/RELEASE file which specifies
#   BASE_MODULE_VERSION, it's value will be shown as the EPICS base version.
#
#   If the --verbose option is selected, all version macros
#   matching *_MODULE_VERSION in the configure/RELEASE file
#   will be shown.
#
#   Example:
#       epics-versions -v ioc/common/Leviton
#   Assuming the following directory is the latest release of ioc/common/Leviton:
#       $(EPICS_SITE_TOP)/ioc/common/Leviton/R1.1.0
#   Output would be:
#       ioc/common/Leviton      R1.1.0      Base    R3.14.9-0.3.0
#           AUTOSAVE_MODULE_VERSION         = R4.2.1.2-1.2.0
#           IOCADMIN_MODULE_VERSION         = R2.0.0-1.1.0
#           GENERALTIME_MODULE_VERSION      = R1.2.2.2-1.0.0
#           SNMP_MODULE_VERSION             = R1.1.0-1.5.0
#
#
# Copyright 2011,2012,2016 Stanford University
# Photon Controls and Data Systems
# Author: Bruce Hill <bhill@slac.stanford.edu>
#
# Released under the GPLv2 licence <http://www.gnu.org/licenses/gpl-2.0.html>
#
DEF_EPICS_TOP_PCDS  = "/reg/g/pcds/package/epics"
DEF_EPICS_TOP_AFS   = "/afs/slac/g/pcds/package/epics"
DEF_EPICS_TOP_LCLS  = "/afs/slac/g/lcls/epics"
DEF_EPICS_TOP_MCC   = "/usr/local/lcls/epics"
debugScript         = False


# Create a pretty printer for nicer diagnostics
pp  = pprint.PrettyPrinter( indent=4 )

# Pre-compile regular expressions for speed
baseVersionRegExp   = re.compile( r"^\s*([A-Za-z0-9_-]*BASE[A-Za-z0-9_-]*VER[SION]*)\s*=\s*(\S*)\s*$" )
versionRegExp       = re.compile( r"^\s*([A-Za-z0-9_-]*VERSION)\s*=\s*(\S*)\s*$" )
parentRegExp        = re.compile( r"RELEASE\s*=\s*(\S*)\s*$" )

class ValidateError( Exception ):
    pass

def debug_signal_handler(signal, frame):
    import pdb
    pdb.set_trace()
signal.signal(signal.SIGINT, debug_signal_handler)

def ExpandModulePath( moduleTop, module, opt ):
    # Create the path to module
    modPath = os.path.join( moduleTop, module )

    # See if it exists
    if not os.path.isdir( modPath ):
        if opt.debug:
            print "ExpandModulePath: %s not found" % ( modPath )
        return []

    # See if this is a screens release
    screenArg   = False
    if "screens" in modPath:
        screenArg   = True

    if opt.debug:
        print "ExpandModulePath: Expanding %s ..." % ( modPath )

    selectedReleases = [ ]
    for dirPath, dirs, files in os.walk( modPath, topdown=True ):
        if len( dirs ) == 0:
            continue
        if '.git' in dirs:
            dirs.remove( '.git' )
        if '.svn' in dirs:
            dirs.remove( '.svn' )
        if 'CVS' in dirs:
            dirs.remove( 'CVS' )

        # Loop through the directories looking for releases
        releases = [ ]
        dirs.sort()
        for dir in dirs[:]:
            # Remove from list so we don't search recursively
            dirs.remove( dir )
            if not isReleaseCandidate(dir):
                continue
            release = os.path.join( dirPath, dir )
            if screenArg:
                verPath = os.path.join( release, "Makefile" )
            else:
                verPath = os.path.join( release, "configure", "RELEASE" )

            buildPath = os.path.join( release, "build" )
            if os.path.isfile( verPath ) or os.path.isdir( buildPath ):
                if opt.debug:
                    print "ExpandModulePath: Found ", release
                releases += [ release ]

        if len( releases ) == 0:
            continue;

        # Create the release set so we can order the releases by version number
        releaseSet  = { }
        for release in releases:
            ( reldir, ver ) = os.path.split( release )
            relNumber = VersionToRelNumber( ver )
            while relNumber in releaseSet:
                relNumber -= 1e-12
            releaseSet[ relNumber ] = release

        #if opt.debug:
        #   print "ExpandModulePath Module Releases: "
        #   pp.pprint( releaseSet )

        for release in sorted( releaseSet.keys(), reverse = True ):
            selectedReleases += [ releaseSet[ release ] ]

    if opt.debug:
        print "ExpandModulePath Selected Releases: "
        pp.pprint( selectedReleases )
    return selectedReleases

def ReportReleases( moduleTop, module, releases, opt ):
    if opt.debug:
        print "ReportReleases: ", module
    found = False
    priorModule = None
    for release in releases:
        reportedModule = ReportRelease( moduleTop, module, release, priorModule, opt )
        if reportedModule != None:
            found = True
            priorModule = reportedModule
    return found

def ReportRelease( moduleTop, module, release, priorModule, opt ):

    # Get the module and version from the release string
    ( relPath, moduleVersion ) = os.path.split( release )
    module = relPath.replace( moduleTop, "" )
    module = module.lstrip( "/" )
    if opt.debug:
        print "ReportRelease: %s, priorModule = %s" % ( module, priorModule )
    if module == priorModule and not opt.showAll:
        return None

    moduleDependents    = {}
    baseDependents      = {}
    if not module.startswith( "screens" ):
        # Get the base and dependent modules from RELEASE files
        releaseFiles = []
        releaseFiles += [ os.path.join( release, "..", "..", "RELEASE_SITE" ) ]
        releaseFiles += [ os.path.join( release, "RELEASE_SITE" ) ]
        releaseFiles += [ os.path.join( release, "configure", "RELEASE" ) ]
        releaseFiles += [ os.path.join( release, "configure", "RELEASE.local" ) ]
        for releaseFile in releaseFiles:
            if opt.debug:
                print "Checking release file: %s" % ( releaseFile )
            if not os.path.isfile( releaseFile ):
                continue
            for line in fileinput.input( releaseFile ):
                m = versionRegExp.search( line )
                if m and m.group(1) and m.group(2):
                    moduleDependents[ m.group(1) ] = m.group(2)
                m = baseVersionRegExp.search( line )
                if m and m.group(1) and m.group(2):
                    baseDependents[ m.group(1) ] = m.group(2)

    baseVer = "?"
    baseVerMacros = [ "BASE_MODULE_VERSION", "BASE_VERSION", "EPICS_BASE_VER", "EPICS_BASE_VERSION" ]
    for baseMacro in baseVerMacros:
        # For the BASE macro's, remove them from moduleDependents
        if baseMacro in moduleDependents:
            del moduleDependents[ baseMacro ]

        if not baseMacro in baseDependents:
            continue

        # Skip any defined by other macros
        baseMacroValue = baseDependents[ baseMacro ]
        if '$' in baseMacroValue:
            continue

        # Found a base version!
        baseVer = baseMacroValue

    if module == 'base':
        baseVer = moduleVersion

    if baseVer != "?" and opt.debug:
        print "%s BaseVersion: %s" % ( moduleTop, baseVer )

    buildPath = os.path.join( release, "build" )
    if os.path.isdir( buildPath ):
        baseVerPrompt = "Templated IOC"
    else:
        # See if they've restricted output to a specific base version
        if opt.base and opt.base != baseVer:
            return None
        if "screens" in release or module == "base":
            baseVerPrompt = ""
        elif opt.wide:
            baseVerPrompt = " BASE=" + baseVer
        else:
            baseVerPrompt = "%-18s = %s" % ( "BASE", baseVer )

    # Print the module and version, along with base version if any
    if opt.wide:
        print "%s %s" % ( release, baseVerPrompt ),
    else:
        print "%-24s %-18s %s" % ( module, moduleVersion, baseVerPrompt )

    # Show moduleDependents for --verbose
    if opt.verbose:
        for dep in sorted( moduleDependents.keys() ):
            # Print dependent info w/o newline (trailing ,)
            depRoot = dep.replace( "_MODULE_VERSION", "" )
            if opt.wide:
                # Don't print newline in wide mode 
                print " %s=%s" % ( depRoot, moduleDependents[ dep ] ),
            else:
                print "%-24s %-18s %-18s = %s" % ( "", "", depRoot, moduleDependents[ dep ] )
    if opt.wide:
        print

    if os.path.isdir( buildPath ):
        # Templated IOC
        # Show parent release for each ioc
        configFiles = glob.glob( os.path.join( release, "*.cfg" ) )
        for configFile in configFiles:
            for line in fileinput.input( configFile ):
                match = parentRegExp.search( line )
                if match:
                    iocName = os.path.basename(configFile).replace( '.cfg', '' )
                    parentRelease = match.group(1)
                    print "%-4s %-20s %s" % ( '', iocName, parentRelease )

    return module

def ExpandModulesForTop( moduleTop, modules, opt ):
    moduleTopShown = False
    numReleasesForTop = 0
    for module in modules:
        releases = ExpandModulePath( moduleTop, module, opt )

        # validate the module specification
        if not releases or not releases[0]:
            continue
        if not opt.wide and moduleTopShown == False:
            print "Releases under %s:" % moduleTop
            moduleTopShown = True

        # Report all releases for this module
        if not ReportReleases( moduleTop, module, releases, opt ):
            print "%s/%s: No releases found matching specification.\n" % ( moduleTop, module )
        numReleasesForTop += len(releases)
    return numReleasesForTop

# Entry point of the script. This is main()
try:
    parser = optparse.OptionParser( description = "Report on available module versions and dependencies",
                                    usage = "usage: %prog [options] MODULE ...\n"
                                            "\tMODULE can be one or more of:\n"
                                            "\t\tbase\n"
                                            "\t\tmodules\n"
                                            "\t\tmodules/<MODULE_NAME>\n"
                                            "\t\tioc\n"
                                            "\t\tioc/<hutch>\n"
                                            "\t\tioc/<hutch>/<IOC_NAME>\n"
                                            "\t\tscreens/edm/<hutch>\n"
                                            "\t\tetc ...\n"
                                            "\tEx: %prog ioc/xpp\n"
                                            "\tFor help: %prog --help" )
    parser.set_defaults(    verbose     = False,
                            revision    = "HEAD",
                            debug       = debugScript )

    parser.add_option(  "-a", "--all", dest="showAll", action="store_true",
                        help="display all revisions of each module" )

    parser.add_option(  "-v", "--verbose", dest="verbose", action="store_true",
                        help="show dependent modules" )

    parser.add_option(  "-d", "--debug", dest="debug", action="store_true",
                        help="display more info for debugging script" )

    parser.add_option(  "-b", "--base",
                        help="Restrict output to modules for specified base version\n"
                             "ex. --base=R3.14.9-0.3.0" )

    parser.add_option(  "-w", "--wide", dest="wide", action="store_true",
                        help="Wide output, all module info on one line\n"   )

    parser.add_option(  "--top", dest="moduleTop", metavar="TOP",
                        default=None,
                        help="Top of EPICS module release area\n"
                             "ex. --top=/afs/slac/g/pcds/package/epics/R3.14.12.5-0.1.0/modules" )

    parser.add_option(  "--allTops", dest="allTops", action="store_true",
                        help="Search all accessible known EPICS module release locations\n" )

    # Future options
    #add_option(    "--prefix", "path to the root of the release area"

    # Parse the command line arguments
    ( opt, args ) = parser.parse_args()

    # validate the arglist
    if not args or not args[0]:
        raise ValidateError, "No valid modules specified."

    # See if we can find EPICS_SITE_TOP
    epics_site_top = os.environ.get( "EPICS_SITE_TOP" )
    if not epics_site_top:
        epics_site_top = os.environ.get( "EPICS_TOP" )

    releaseCount = 0
    if epics_site_top:
        # See if we find any matches in the ioc release areas
        iocTops = []
        iocTops += [ epics_site_top ]
        iocTops += [ os.path.join( epics_site_top, "iocTop" ) ]
        iocTops += [ os.path.join( epics_site_top, "ioc" ) ]
        iocTops += [ os.path.join( epics_site_top, "ioc", "common" ) ]
        iocTops += [ os.path.join( epics_site_top, "ioc", "amo" ) ]
        iocTops += [ os.path.join( epics_site_top, "ioc", "sxr" ) ]
        iocTops += [ os.path.join( epics_site_top, "ioc", "xpp" ) ]
        iocTops += [ os.path.join( epics_site_top, "ioc", "cxi" ) ]
        iocTops += [ os.path.join( epics_site_top, "ioc", "mec" ) ]
        iocTops += [ os.path.join( epics_site_top, "ioc", "mfx" ) ]
        iocTops += [ os.path.join( epics_site_top, "ioc", "xcs" ) ]
        iocTops += [ os.path.join( epics_site_top, "ioc", "xrt" ) ]
        iocTops += [ os.path.join( epics_site_top, "ioc", "tst" ) ]
        iocTops += [ os.path.join( epics_site_top, "ioc", "fee" ) ]
        iocTops += [ os.path.join( epics_site_top, "ioc", "las" ) ]
        iocTops += [ os.path.join( epics_site_top, "screens" ) ]
        iocTops += [ os.path.join( epics_site_top, "screens", "edm" ) ]
        for iocTop in iocTops:
            releaseCount += ExpandModulesForTop( iocTop, args, opt )

    # See which moduleTop to search
    if not opt.moduleTop:
        # --top not specified, look for EPICS_MODULES_TOP in environment
        opt.moduleTop = os.environ.get( "EPICS_MODULES_TOP" )
        if not opt.moduleTop:
            opt.moduleTop = os.environ.get( "EPICS_MODULES" )
        if not opt.moduleTop:
            if epics_site_top:
                opt.moduleTop = os.path.join( epics_site_top, 'modules' ) 
                if not os.path.isdir( opt.moduleTop ):
                    opt.moduleTop = None

    if opt.moduleTop:
        releaseCount += ExpandModulesForTop( opt.moduleTop, args, opt )

    # If we haven't found a default or --allTops, try any we can find
    if opt.allTops or not opt.moduleTop:
        for site_top in [ DEF_EPICS_TOP_LCLS, DEF_EPICS_TOP_MCC, DEF_EPICS_TOP_PCDS, DEF_EPICS_TOP_AFS ]:
            for dirPath, dirs, files in os.walk( site_top, topdown=True ):
                if len( dirs ) == 0:
                    continue
                for dir in dirs[:]:
                    # Remove from list so we don't search recursively
                    dirs.remove( dir )
                    moduleTop = os.path.join( site_top, dir, 'modules' ) 
                    if not os.path.isdir( moduleTop ):
                        continue
                    if opt.moduleTop and moduleTop == opt.moduleTop:
                        # Already done this one
                        continue
                    releaseCount += ExpandModulesForTop( moduleTop, args, opt )

    if releaseCount == 0:
        errorMsg = "Unable to find any releases for these modules:"
        for module in args:
            errorMsg += " "
            errorMsg += module
        raise ValidateError, errorMsg

    # All done!
    sys.exit(0)

except ValidateError:
    print "Error: %s\n" % sys.exc_value 
    parser.print_usage()
    sys.exit(6)

except KeyboardInterrupt:
    print "\nERROR: interrupted by user."
    sys.exit(2)

except SystemExit:
    raise

except:
    if debugScript:
        traceback.print_tb(sys.exc_traceback)
    print "%s exited with ERROR:\n%s\n" % ( sys.argv[0], sys.exc_value )
    sys.exit( 1 )