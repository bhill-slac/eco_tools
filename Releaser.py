import re
import sys
import shutil
import tempfile
import os
import subprocess
import Repo

class BuildError( Exception ):
    pass

class ValidateError( Exception ):
    pass

class InstallError( Exception ):
    pass

class Releaser(object):
    def __init__( self, repo, opt, args ):
        self._repo		= repo
        self._opt		= opt
        self._package	= args
        self._package	= ""
        self._version	= ""
        self._ReleaseTag= None
        self._retcode	= 0
        # Create a directory where files will be checked-out
        self.tmpDir		= tempfile.mktemp("-epics-release")
        self.grpowner	= None

    def __del__( self ):
        self.DoCleanup( 0 )

    def DoCleanup( self, errCode = 0 ):
        self._retcode = errCode
        if self._opt.debug and self._retcode != 0:
            traceback.print_tb(sys.exc_traceback)
            print "%s exited with return code %d." % (sys.argv[0], retcode)

        if self._opt.keeptmp:
            if os.path.exists(self.tmpDir):
                print "\n--keeptmp flag set. Remove the tmp build directory manually:"
                print "\t%s" % (self.tmpDir)
        else:
            if self._opt.verbose:
                print "Cleaning up temporary files ..."
            sys.stdout.flush()
            try:
                sys.stdout.flush()
                if os.path.exists(self.tmpDir):
                    if self._opt.verbose:
                        print "rm -rf", self.tmpDir
                    shutil.rmtree( self.tmpDir )
            except:
                print "failed:\n%s." % (sys.exc_value)
                print "\nCould not remove the following directories, remove them manually:"
                if os.path.exists(self.tmpDir):
                    print "\t%s" % (self.tmpDir)
    
    def RemoveTag( self ):
        return self._repo.RemoveTag( self._package[0], self._opt.release )
    
    def TagRelease( self ):
        return self._repo.TagRelease( self._package[0], self._opt.release, self._opt.branch, self._opt.message )

    def ValidateArgs( self ):
        # validate the module specification
        if self._package and "current" in self._package[0]:
            raise ValidateError, "The module specification must not contain \"current\": %s" % (self._package[0])

        # validate the repo
        if not self._repo:
            raise ValidateError, "Repo not found for package %s" % (self._package[0])
        defaultPackage	= None
        ( repo_url, repo_branch, repo_tag ) = self._repo.GetWorkingBranch()
        if repo_url:
            if self._opt.debug:
                print "Releaser.ValidateArgs: repo_url    =", repo_url
                print "Releaser.ValidateArgs: repo_branch =", repo_branch
                print "Releaser.ValidateArgs: repo_tag    =", repo_tag
                print "Releaser.ValidateArgs: package     =", self._package
            defaultPackage = self._repo.GetDefaultPackage( self._package )

        if self._opt.debug:
            print "defaultPackage:", defaultPackage

        # If we have a defaultPackage from the working directory,
        # Check it against the other options
        if defaultPackage:
            if not self._package or not self._package[0]:
                self._package = [ defaultPackage ]

        # Determine the release package SVN URL
        if not self._opt.branch:
            if not self._package or not self._package[0]:
                raise ValidateError, "No release package specified"
            if len( self._package ) > 1:
                raise ValidateError, "Multiple  release packages specified: %s" % (self._package)
            if repo_url:
                self._opt.branch = repo_url
            else:
                self._opt.branch = os.path.join(	self._repo, self._gitStub2,
                                                    self._package[0], "current"	)
                if not gitPathExists( self._opt.branch, self._opt.revision ):
                    self._opt.branch = os.path.join(self._repo, self._gitStub1,
                                                    self._package[0], "current"	)

        # Make sure the release package exists
        if not gitPathExists( self._opt.branch, self._opt.revision ):
            raise ValidateError, "Invalid git branch at rev %s\n\t%s" % (	self._opt.revision,
                                                                            self._opt.branch )

        # validate release tag
        if not self._opt.release:
            raise ValidateError, "Release tag not specified (--release)"
        if not re.match( r"(R\d+(\.\d+)+-\d+\.\d+\.\d+)|(R\d+\.\d+\.\d+)", self._opt.release ):
            raise ValidateError, "%s is an invalid release tag: Must be R[<orig_release>-]<major>.<minor>.<bugfix>" % self._opt.release
        if not self._ReleaseTag:
            if not self._package or not self._package[0]:
                raise ValidateError, "No release package specified"
            self._ReleaseTag = os.path.join(	self._repo, self._gitRelDir,
                                                self._package[0], self._opt.release	)

        if self._opt.noTag == False and gitPathExists( self._ReleaseTag ):
            raise ValidateError, "SVN release tag already exists: %s" % ( self._ReleaseTag )
#		try:
#			if gitPathExists( self._ReleaseTag ):
#				raise ValidateError, "SVN release tag already exists: %s" % ( self._ReleaseTag )
#		except:
#			pass
#		else:
#			raise ValidateError, "SVN release tag already exists: %s" % ( self._ReleaseTag )

        # validate release directory
        if not os.path.exists(self._prefix):
            raise ValidateError, "Invalid release directory %s" % ( self._prefix )
        if not self._opt.installDir:
            if not self._package or not self._package[0]:
                raise ValidateError, "No release package specified"
            self._opt.installDir = os.path.join(self._prefix,
                                                self._package[0], self._opt.release	)

        # validate release message
        if not self._opt.message:
            if self._opt.noMsg:
                self._opt.message = ""
            else:
                print "Please enter a release comment (end w/ ctrl-d on blank line):"
                comment = ""
                try:
                    while True:
                        line = raw_input()
                        comment = "\n".join( [ comment, line ] ) 
                except EOFError:
                    self._opt.message = comment

        if self._opt.message is None:
                raise ValidateError, "Release message not specified (-m)"

        if repo_url:
            # Check release branch vs working dir branch
            if self._opt.branch != repo_url:
                print "Release branch: %s\nWorking branch: %s" % ( self._opt.branch, repo_url )
                if not self._opt.batch:
                    confirmResp = raw_input( 'Release branch does not match working dir.  Proceed (Y/n)?' )
                    if len(confirmResp) != 0 and confirmResp != "Y" and confirmResp != "y":
                        branchMsg = "Branch mismatch!\n"
                        raise ValidateError, branchMsg

        # validate self._grpowner	= DEF_LCLS_GROUP_OWNER
        if self._opt.debug:
            print "ValidateArgs: Success"
            print "  repo_url:    %s" % repo_url
            print "  branch:     %s" % self._opt.branch
            print "  release:    %s" % self._opt.release
            print "  tag:        %s" % self._ReleaseTag
            print "  installDir: %s" % self._opt.installDir
            print "  message:    %s" % self._opt.message

    def execute( self, cmd, outputPipe = subprocess.PIPE ):
        if self._opt.verbose:
            print "EXEC: %s" % ( cmd )
        proc = subprocess.Popen( cmd, shell = True, executable = "/bin/bash",
                                stdout = outputPipe, stderr = outputPipe )
        (proc_stdout, proc_stderr) = proc.communicate( )
        if self._opt.debug:
            print "process returned", proc.returncode
        if proc.returncode != 0:
            errMsg = "Command Failed: %s\n" % ( cmd )
            if proc_stdout:
                errMsg += proc_stdout
            if proc_stderr:
                errMsg += proc_stderr
            errMsg += "Return Code: %d\n" % ( proc.returncode )
            raise RuntimeError, errMsg
        return proc_stdout

    def RemoveBuild( self, buildDir ):
        print "\nRemoving build dir: %s ..." % ( buildDir )
        if rel._opt.dryRun:
            return

        # Make sure we can write to the build directory
        try:
            self.execute("chmod -R u+w %s" % ( buildDir ))
        except OSError:
            raise BuildError, "Cannot make build dir writeable: %s" % ( buildDir )
        except RuntimeError:
            raise BuildError, "Build dir not found: %s" % ( buildDir )
        try:
            self.execute("/bin/rm -rf %s" % ( buildDir ))
        except OSError:
            raise BuildError, "Cannot remove build dir: %s" % ( buildDir )
        except RuntimeError:
            raise BuildError, "Build dir not found: %s" % ( buildDir )
        print "Successfully removed build dir: %s ..." % ( buildDir )

    def BuildRelease( self, buildBranch, buildDir, outputPipe = subprocess.PIPE ):
        os.environ["EPICS_SITE_TOP"] = self._prefix
        if not os.path.exists( buildDir ):
            try:
                if self._opt.debug:
                    print "mkdir -p",	buildDir
                os.makedirs( buildDir, 0775 )
            except OSError:
                raise BuildError, "Cannot create build dir: %s" % ( buildDir )

        # Make sure we can write to the build directory
        try:
            self.execute("chmod -R u+w %s" % ( buildDir ))
        except OSError:
            raise BuildError, "Cannot make build dir writeable: %s" % ( buildDir )

        # Checkout release to build dir
        self._repo.CheckoutRelease( buildBranch, buildDir )

        # Build release
        outputPipe = None
        if self._opt.quiet:
            outputPipe = subprocess.PIPE
        try:
            print "Building Release in %s ..." % ( buildDir )
            buildOutput = self.execute( "make -C %s" % buildDir, outputPipe )
            if self._opt.debug:
                print "BuildRelease: SUCCESS"
        except RuntimeError, e:
            print e
            raise BuildError, "BuildRelease: FAILED"

    def DoTestBuild( self ):
        try:
            self.BuildRelease( self._opt.branch, self.tmpDir )
            self.DoCleanup()
        except BuildError:
            self.DoCleanup()
            raise

    def InstallPackage( self ):
        self.BuildRelease( self._ReleaseTag, self._opt.installDir )

        print "Fixing permissions ...",
        sys.stdout.flush()
        try:
            groups = self.execute("id")
            if re.search( groups, self.grpowner ):
                self.execute("chgrp -R %s %s" % ( self.grpowner, self._opt.installDir ))
            self.execute("chmod -R ugo-w %s" % ( self._opt.installDir ))
            print "done"
        except:
            print "failed.\nERROR: %s." % ( sys.exc_value )

        print "Package %s version %s released." % ( self._package[0], self._opt.release )
