#!/usr/bin/perl -w
#
# $Id: wwwgnats_admin.cgi,v 1.1 2001/11/17 04:14:53 hgayosso Exp $
#
# This script is used to administrate a GNATS data base using a web
# based interface.
#
# MODIFICATIONS:
# 06-Nov-1998	Initially generated... MWS
#
# 10-Nov-1998  fixed up to run with SUID bit set. MWS
#
# 29-May-2001  hacked up to run wih gnats 4.0 beta under apache-suexec. PAP
#----------------------------------------------------------------------
#use strict;

my $GNATS_DB_LIST = "/usr/local/etc/gnats/databases";
my $GNATS_REPOSITORY="/var/local/gnats/";
my $GNATS_ADM_SUBDIR="/gnats-adm/";

#$MAKE = "/usr/ccs/bin/make";
my $MKCAT= "/usr/local/libexec/gnats/mkcat";
my $MKDB= "/usr/local/libexec/gnats/mkdb";
my $SHELL = "/bin/sh";

# the CGI object
use vars '$q';
# Use CGI::Carp first, so that fatal errors come to the browser, including
# those caused by old versions of CGI.pm.
use CGI::Carp qw/fatalsToBrowser/;
use CGI 2.56 qw/:standard :netscape/;
use Socket;
use IO::Handle;


use File::Basename;

# constants
my $DEBUG=0;			# set to non-zero to enble debug messages
my $REVISION = '$Revision: 1.1 $ ';
my $REVISION_DATE = '$Date: 2001/11/17 04:14:53 $';
my ($VERSION) = $REVISION =~ m/.*: ([0-9]\..*)\$/ ;
$REVISION_DATE =~ m/^\$.+: (.+)\$/;
my $VERSION_DATE = "$1 GMT";

### Environment variables

use vars qw($script_name $cmd $server_name $query_string);

$script_name = defined $ENV{"SCRIPT_NAME"}? $ENV{"SCRIPT_NAME"} : '';
my $SCRIPT_PATH = dirname($SCRIPT_NAME);
my $PATH_INFO = $ENV{"PATH_INFO"};
$SERVER_NAME = defined $ENV{"SERVER_NAME"}? $ENV{"SERVER_NAME"} : '';
my $DOCUMENT_ROOT=$ENV{'DOCUMENT_ROOT'};
my $HTTPD_ROOT= dirname($DOCUMENT_ROOT) if ($DOCUMENT_ROOT);

$ENV{'PATH'} = "/bin:/usr/bin:/usr/local/bin:/usr/ccs/bin";
my $FIND = "/usr/bin/find";
my $LOCK_EXT = ".lock";

# untaint the query string for setuid to work properly.
$query_string = defined $ENV{"QUERY_STRING"}? $ENV{"QUERY_STRING"}: '';
$query_string =~ /^(.*)$/;
$query_string = $1;
#and clean up the environment settings for same
$ENV{BASH_ENV} = '';
$ENV{ENV} = '';

# Standard header and footer definitions

my $HEADING_TEXT1 = "<H2>GNATS System Administration for Host:&#160;&#160;" . $SERVER_NAME . "</H2>\n";
my $HEADING_TEXT2a = "<H4>Database: &#160;&#160;";
my $HEADING_TEXT2b = "</H4><hr>";

my $FOOTER = "<p><hr>Web Based Administration Tool Version $VERSION on $VERSION_DATE<p>
" . &main_page_link() . "<p>";

main();

#
# MAIN starts here:
#
sub main
	{
	# Make sure nobody tries to swamp our server with a huge file attachment.
	# Has to happen before 'new CGI'.
    $CGI::POST_MAX = $site_post_max if defined($site_post_max);

	# Create the query object.  Check to see if there was an error, which
	# happens if the post exceeds POST_MAX.
	$q = new CGI;
	if ($q->cgi_error())
	{
		print $q->header(-status=>$q->cgi_error());
          $q->start_html('Error');
		page_heading('Initialization failed', 'Error');
		print $q->h3('Request not processed: ', $q->cgi_error());
		warn("gnats_admin: cgi error: ", $q->cgi_error(), " stacktrace: ", print_stacktrace());
		exit();
	}	

	$script_name = $q->script_name;
	$cmd = $q->param('cmd') || ''; # avoid perl -w warning

#	print "Content-type: text/html\n\n";
#	print "<HTML>\n";
	print $q->header(),
		$q->start_html("Gnats Admin");

#---------------------------------------------------------------------
# Determine what to do
#---------------------------------------------------------------------

	if ($cmd eq 'Edit')
	    {
	    &edit_page();
	    }
	elsif ($cmd eq 'Save changes')
	    {
	    &handle_edit();
	    }
	elsif ($cmd eq 'Abort edit')
	    {
	    &handle_edit();
	    }
	elsif ($cmd eq 'View')
	    {
	    &view_page();
	    }
	elsif ($cmd eq 'unlock file')
	    {
	    &handle_unlock();
	    }
	elsif ($cmd eq 'Configure db')
	    {
	    &config_list();
	    }
	elsif ($cmd eq 'Create new db')
	    {
	    &create_db_page();
	    }
	elsif ($cmd eq 'Initialize db')
	    {
	    &make_db();
	    }
	else # Main menu of choices
	    {
	    &main_menu();
	    }
#	else
#	    {
#	    print "<head><title>GNATS Administration Front End</title></head>
#<H1>Tracking Front End</H1>
#<body>
#" . heading_text();
#	    print "Bad subdirectory/parameters specified in URL.\n";
#	    }

#---------------------------------------------------------------------
# print standard footer
#---------------------------------------------------------------------
	print "$FOOTER \n";

#	print "<h3> This script should be run SUID gnats!</h3>" if (! -u $ENV{'SCRIPT_FILENAME'});

	$q->end_html();
	#print "\n</body>\n";
	#print "</HTML>\n";
	exit(0);
	}


#---------------------------------------------------------------------
#
#---------------------------------------------------------------------
sub heading_text
    {
    my($database) = @_;

    my $heading = $HEADING_TEXT1;

    $heading .= $HEADING_TEXT2a . $database . $HEADING_TEXT2b unless !defined $database;
    return $heading;
    }
#---------------------------------------------------------------------
#
#---------------------------------------------------------------------
sub config_list
    {
    my($database) = $q->param('database');

    # Display title
    print "<head><title>GNATS Admin</title></head>\n
<body>",
		heading_text($database), $q->p(),
		"Below are the administrative files for the GNATS database.", $q->p();

    &list_file_links(find_db_root($database).$GNATS_ADM_SUBDIR);

    }

#---------------------------------------------------------------------
#
#---------------------------------------------------------------------
sub main_menu
    {
    # Display title
    print "<head><title>GNATS Admin</title></head>\n
<body>\n",
heading_text(),
"\n";

	print "<hr>\n<table>\n",
		$q->start_form();
    print $q->Tr( $q->td( $q->submit('cmd','Create new db'), $q->p(' ') ) );
    list_databases();

	print $q->end_form(),"</table>";

    }

#---------------------------------------------------------------------
#
#---------------------------------------------------------------------
sub create_db_page
	{
	    print "<head><title>GNATS Admin</title></head>\n
<body>\n",
			heading_text(),
"\n<HR>\n
<p>Enter information for the new database:</p>";
		print $q->start_form(), $q->table(
			$q->Tr( 
				$q->td("DB Name"),
				$q->td($q->textfield(-name=>'database',
						-size=>$textwidth))
			),

			$q->Tr(
				$q->td("DB Description"),
				$q->td($q->textfield(-name=>'dbdesc',
				  -size=>$textwidth))
			),
			$q->Tr(
				$q->td("DB Directory"),
				$q->td($q->textfield(-name=>'dbdir',
				  -size=>$textwidth)),
				$q->td($q->submit('cmd','Initialize db'))
			)),
		$q->end_form();
	}

#---------------------------------------------------------------------
#
#---------------------------------------------------------------------
sub make_db
	{
	print "<head><title>GNATS Admin</title></head>\n
<body>\n",
heading_text(),
"\n";
	my ($database) = $q->param('database');
	my ($dbdesc) = $q->param('dbdesc');
	my ($dbdir) = $GNATS_REPOSITORY.$q->param('dbdir');
	$dbdir=~ /^(.*)$/; # untaint data 
	$dbdir= $1;
	
	$| = 1; # force buffer flush
	print "<p>Creating new database $database in directory $dbdir\n<pre>";
	system("echo \"($MKDB $dbdir) 2>&1\" | $SHELL");
#    my @arglist = ("mkdb", $dbdir);
#	system($MKDB, @arglist);
	print "</pre>\n";
	$| = 0; # stopp flush
	
	open (DBLIST, "+>>" . $GNATS_DB_LIST) or die "cannot open $GNATS_DB_LIST: $!";      
	flock (DBLIST, 2) or die "cannot lock $GNATS_DB_LIST: $!";

	print DBLIST "$database:$dbdesc:$dbdir";
	flock(DBLIST, 8) or die "cannot unlock $GNATS_DB_LIST: $!";

	close (DBLIST);
	}

#---------------------------------------------------------------------
# return a list files
#
# args: dir
#---------------------------------------------------------------------
sub list_files
    {
    my($dir) = @_;
    my($pwd) = $ENV{'PWD'};

    my(@list, $file) ;

    chdir $dir or die "Couldn't change to $dir:$!<BR>";

    foreach $file (`$FIND . \\( -type d ! -name . -prune \\) -o \\( -type f -print \\)`)
		{
		# filter out .lock, *~, .*, .bak files
		chomp $file;
		$file =~ s,^\./(.*),$1,;
		next if ($file =~ m/\.lock$|~$|^\.|.bak$/);
		push(@list, $file);
		}

	chdir ($pwd);

    return @list
    }

#---------------------------------------------------------------------
# Lock a file
#
# args: file
#
# return: true for successful locking
#---------------------------------------------------------------------
sub lock_file
    {
    my($file) = @_;

    my($lockfile) = "$file$LOCK_EXT";

    my($text);

    # see if a lock is already set
    if (-f $lockfile)
		{
		open(FILE, "<$lockfile");
		$text = <FILE>;
		print "<h3>File Locked</h3>
<p>File $file was locked on :<br>$text".
	    &file_unlock_link($q->param('database'), basename($file), "<p>Click here to unlock");
		close(FILE);
		return 0;
		}

    # now set the lock file
    if (! -f $file or !open(FILE, ">$lockfile"))
		{
		print "Can't create lock file for $file";
		return 0;
		}
    print "<p>lock file name = `$lockfile'" if ($DEBUG);

    print FILE scalar(localtime) . "\n";
    close(FILE);
    return 1;
    }

#---------------------------------------------------------------------
# Unlock a file
#
# args: file
#---------------------------------------------------------------------
sub unlock_file
    {
    my($file) = @_;

    my($lockfile) = "$file$LOCK_EXT";

    unlink $lockfile if (-f $file);
    }

#---------------------------------------------------------------------
# Check for file lock
#
# args: file
#---------------------------------------------------------------------
sub is_locked
    {
    my($file) = @_;

    my($lockfile) = "$file$LOCK_EXT";

    return (-f $lockfile);
    }

#---------------------------------------------------------------------
# Read a file
#
# Args: file
#
# return: true for success
#---------------------------------------------------------------------
sub read_file
    {
    my($file) = @_;

    if (!open(FILE, "<$file"))
		{
		print "<p>Error reading `$file'";
		return 0;
		}

    # suck up the whole file
    my(@lines) = <FILE>;

    close(FILE);

    return @lines;
    }

#---------------------------------------------------------------------
# write the file
#
# args: file, lines
#
# return: true for success
#---------------------------------------------------------------------
sub write_file
    {
    my($file, @lines) = @_;

    my($tmp,$path);
    $path = dirname($file);
    $tmp = "$path/.tmp." . basename($file);

    if (!open(FILE, "> $tmp"))
		{
		print "<p>Error opening temp file $tmp";
		return 0;
		}

    print FILE @lines;
    close(FILE);

    # now move the temp file to the real file
    unlink($file);
    rename($tmp, $file);
    return 1;
    }

#---------------------------------------------------------------------
# View a file
#
# args: $file
#---------------------------------------------------------------------
sub view_page
    {

    my($database) = $q->param('database');
    my($file) = $q->param('file');

    # Display title
    print "<head><title>GNATS Admin</title></head>\n
<body>\n",
heading_text($database), "\n";

    my($filepath) = find_db_root($database) . $GNATS_ADM_SUBDIR . $file;

    my(@lines) = &read_file($filepath);

    if (@lines)
		{
		my $text = join("", @lines);
		print $q->h3("Contents of file `$file'"), "<p>";
		print $q->start_form(), $q->hidden('database', $database),
			$q->hidden('file', $file), $q->submit('cmd','Edit'),
		      $q->end_form();
		print "<hr>
<pre>$text</pre>";
		}
    else
		{
		print $q->h3("No lines in file `$filepath'") ;
		}
	print &db_file_config_link($database), "\n";
    }

#---------------------------------------------------------------------
# list links to found files
#
# args: dir
#---------------------------------------------------------------------
sub list_file_links
    {
    my($dir) = @_;

    my @list = &list_files($dir);

    print "<p> no files found in `$dir'\n" unless (@list);

    my($file);
    
#    print "<ul>\n";
#    foreach $file (sort @list)
#		{
#		print "<li>". &file_edit_link($file, "Edit") . " or " .
#		   	 &file_view_link($file, "View") . "&#160;&#160; $file\n";
#		}
#    print "</ul>\n";

    print $q->start_form(), $q->hidden('database', $q->param('database')),
		$q->table(
			$q->Tr( $q->td( $q->scrolling_list (-name=>"file",
                               -size=>7,
                               -values=>\@list)), 
					$q->td($q->submit('cmd','View'), $q->br(), $q->br(), $q->submit('cmd','Edit'))
			)); 

        $q->end_form();
    }

#---------------------------------------------------------------------
# edit page
#
# args: $file
#---------------------------------------------------------------------
sub edit_page
    {
	my($database) = $q->param('database');
	my($filename) = $q->param('file');


    print "<head><title>GNATS Admin</title></head>\n
<body>\n",
heading_text($database);

    my(@lines);
    my($file) = find_db_root($database) . $GNATS_ADM_SUBDIR . $filename;

	$file =~ /^(.*)$/; # untaint data 
	$file = $1;

    if (&lock_file($file))
	{
		@lines = &read_file($file);
		my $text = join("",@lines);
		my $rows = $#lines + 3;
		$rows = 25 if ($rows > 25);

		print $q->start_form(), $q->hidden('database', $database), $q->hidden('file', $file),

		"<p>Contents of `$file'
<font color=\"#FF0000\"><p>NOTE: USE ABORT BUTTON TO CANCEL EDIT!!</font>
<p>",
		$q->submit('cmd', 'Save changes'),
		$q->submit('cmd', 'Abort edit'),

		"<p><textarea name=contents cols=80 rows=$rows>$text</textarea>
<p>",
		$q->submit('cmd', 'Save changes'),
		$q->submit('cmd', 'Abort edit'),
	}
    }



#---------------------------------------------------------------------
# list the databases available for editing in a form with a button
#
# args:
#---------------------------------------------------------------------
sub list_databases
    {
	my(@databaselist) = read_database_list();
	
	print $q->Tr( {-valign=>"top"},
			$q->td( $q->submit('cmd','Configure db')),
			$q->td( $q->scrolling_list (-name=>"database",
                               -size=>9,
                               -values=>\@databaselist)),
		);

    }

#---------------------------------------------------------------------
# read and parse the list of databases
#
# args:
#---------------------------------------------------------------------
sub read_database_list
    {
	if (!open(FILE, "<$GNATS_DB_LIST"))
		{
		print "<p>Error reading `$GNATS_DB_LIST'";
		return 0;
		}

	# suck up the whole file
	my(@lines) = <FILE>;

	close(FILE);

    # 
    my($masterdbline, $dbname, @dbnamelist, @rest);
	my($index) = 0;

    foreach $masterdbline (@lines)
		{
		$masterdbline =~ /^(.*)$/; # untaint data (ie. strip CR/LF)
		($dbname, @rest) = split(":", $1);
		$dbnamelist[$i++] = $dbname unless $dbname =~ "^#";
		}
	return sort(@dbnamelist);
	}

#---------------------------------------------------------------------
# find the directory path for the root of a database
#
# args:
#---------------------------------------------------------------------
sub find_db_root
    {

    my($database) = @_;
	if (!open(FILE, "<$GNATS_DB_LIST"))
		{
		print "<p>Error reading `$GNATS_DB_LIST'";
		return 0;
		}

	# suck up the whole file
	my(@lines) = <FILE>;

	close(FILE);

    # 
    my($masterdbline, $dbname, $dbdescription, $dbpath);
	my($index) = 0;

    foreach $masterdbline (@lines)
	{
		if  ($masterdbline =~ /^$database:/)
		{
			$masterdbline =~ /^(.*)$/; # untaint data
			($dbname, $dbdescription, $dbpath) = split(":", $1);
			return $dbpath;
		}
	}
#	print "Database $database not found in databases list<BR>";
	return 0;
	}

#---------------------------------------------------------------------
# handle the edited page
#
# args:
#---------------------------------------------------------------------
sub handle_edit
    {
    print "<head><title>GNATS Admin</title></head>\n
<body>\n";


    # check to see what action to take
    my $database = $q->param('database');
	$database =~ /^(.*)$/; # untaint data 
	$database = $1;

    my $file = find_db_root($database) . $GNATS_ADM_SUBDIR . $q->param('file');
	$file =~ /^(.*)$/; # untaint data 
	$file = $1;

    print heading_text($database);

    # make sure file is locked

    if (! is_locked($file))
	{
		print $q->h3("File `$file' is not locked.").
			&db_file_config_link($database) . "\n";
	}
    elsif ($cmd eq 'Save changes')
	{
		if (write_file($file, $q->param('contents')))
		{
		    print "<p> $file saved.";

			if (basename($file) eq "categories")
			{
				$| = 1; # force buffer flush
				print "<p>Verifying categories\n<pre>";
				system("echo \"($MKCAT --database " . $database . ") 2>&1\" | $SHELL");
				print "</pre>\n";
				$| = 0; # stopp flush

			}
			else { print &db_file_config_link($database) . "\n";}
#		    &run_make();
	    }
	}
    else
	{
		print $q->h3("Edit aborted.\n") .
		    &main_page_link() . ".\n";
	}
    &unlock_file($file);
    }

#---------------------------------------------------------------------
# Create a link back to main page
#
# args: $link_text
#---------------------------------------------------------------------
sub main_page_link
    {
    my($link_text) = @_;
    $link_text = "<p>Back to main page</p>" unless ($link_text);

    return "<a href=\"".$script_name."\">$link_text</a>"
    }

#---------------------------------------------------------------------
# Create a link back to database configuration page
#
# args: $database
#---------------------------------------------------------------------
sub db_file_config_link
    {
    my($database) = @_;
    return "<a href=\"".$script_name."?cmd=Configure db&database=".$database."\">Continue $database configuration</a>"
    }

#---------------------------------------------------------------------
# Handle the unlocking of a file
#---------------------------------------------------------------------
sub handle_unlock
    {
	my($database) = $q->param('database');
    my $file = find_db_root($database) . $GNATS_ADM_SUBDIR . $q->param('file');
	$file =~ /^(.*)$/; # untaint data 
	$file = $1;

    # Display title
    print "<head><title>GNATS Admin</title></head>\n
<body>\n",
    heading_text($database);

    &unlock_file($file);

    print "<p>`$file' Unlocked." . &db_file_config_link($database) . &main_page_link();
    }


#---------------------------------------------------------------------
# Create a link to unlock a file
#
# args: $database, $file, $text
#---------------------------------------------------------------------
sub file_unlock_link
    {
    my($database, $file, $text) = @_;
    $text = $file unless($text);

    return "<a href=\"$SCRIPT_NAME?cmd=unlock file&database=$database&file=$file\">$text</a>"
    }

#---------------------------------------------------------------------
# Translates '+' to ' ' and '%##' to 'chr(0x##)'
#---------------------------------------------------------------------
sub cgi_trans
    {
    my($str) = @_;

    $str =~ s/\+/ /g;
    $str =~ s/%([\dA-Fa-f][\dA-Fa-f])/sprintf("%c",hex($1))/eg;
    return $str;
    }

#---------------------------------------------------------------------
# Process the makefile if present
#
# args:
#---------------------------------------------------------------------
#sub run_make
#    {
#    if (-f "$GNATS_ADM/Makefile")
#	{
#		$| = 1; # force buffer flush
#		print "<p>Rebuilding admin files\n<pre>";
#		system("echo \"(cd $GNATS_ADM; $MAKE) 2>&1\" | $SHELL");
#		print "</pre>\n";
#		$| = 0; # stopp flush
#	}
#    }

#---------------------------------------------------------------------
# Print a stacktrace
# used by the various warn() statments to emit useful diagnostics
# to the web server error logs.
#
# args:
#---------------------------------------------------------------------
sub print_stacktrace {
    my @stacktrace;
    my $i = 1;
    while ( my($subroutine) = (caller($i++))[3] ) {
    push(@stacktrace, $subroutine);
    }
    return 'In: ' . join(' <= ', @stacktrace);
}



# Automatic Emacs style settings
# Local Variables:
# mode: perl
# perl-indent-level:                0
# perl-continued-statement-offset:  4
# perl-continued-brace-offset:      -4
# perl-brace-offset:                4
# perl-brace-imaginary-offset:      4
# perl-label-offset:               -4
# enable-trim-on-save: t
# End:

