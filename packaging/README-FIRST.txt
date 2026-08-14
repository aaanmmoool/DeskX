====================================================================
 DeskX - Data Sanitizer
 Version 0.1.0  |  Windows
====================================================================

Clean and anonymize spreadsheets before you share them. Everything
runs on your own computer - no internet connection, no account, no
data ever leaves your machine.


--------------------------------------------------------------------
 HOW TO START (GUI)
--------------------------------------------------------------------

1. Unzip this folder anywhere you like (Desktop or Documents is fine).
   Keep all the files together - DeskX.exe needs the files next to it.

2. Double-click  DeskX.exe

That's it. There is nothing to install and you do not need Python.


--------------------------------------------------------------------
 HOW TO START (CLI)
--------------------------------------------------------------------

This package also includes deskx.exe — the same sanitization engine
as a command-line tool. You still do NOT need Python or pip.

1. Open PowerShell or Command Prompt
2. cd into this unzipped folder
3. Run:

   .\deskx.exe --help
   .\deskx.exe sanitize "C:\path\to\file.xlsx"
   .\deskx.exe preview "C:\path\to\file.csv"
   .\deskx.exe transform "C:\path\to\file.csv" --pipeline "PII Sanitization"

Optional: add this folder to your PATH if you want to type "deskx"
from any directory.


--------------------------------------------------------------------
 "WINDOWS PROTECTED YOUR PC" MESSAGE
--------------------------------------------------------------------

The first launch may show a blue SmartScreen warning. This appears for
any app that has not paid for a commercial signing certificate - it is
not a virus warning.

To continue:

   Click  "More info"   ->   click  "Run anyway"

Windows will remember your choice and stop asking.


--------------------------------------------------------------------
 SUPPORTED FILES
--------------------------------------------------------------------

   CSV    .csv
   Excel  .xlsx
   JSON   .json
   Text   .txt


--------------------------------------------------------------------
 HOW IT WORKS
--------------------------------------------------------------------

GUI:
   Upload  ->  Preview  ->  Configure  ->  Review
           ->  Choose where to save  ->  Process  ->  Done

CLI (interactive):
   deskx sanitize file.xlsx
   Detect sensitive columns -> choose transforms -> review -> save

CLI (repeatable):
   deskx transform file.xlsx --pipeline "PII Sanitization"


--------------------------------------------------------------------
 YOUR ORIGINAL FILE IS NEVER TOUCHED
--------------------------------------------------------------------

DeskX always writes a separate, cleaned copy. It will refuse to save
over your source file, and it never silently replaces an existing
result - you are asked first.

By default, cleaned files from the GUI are saved to:

   Documents\DeskX\Output

You can pick any other folder in the save dialog.


--------------------------------------------------------------------
 UNINSTALLING
--------------------------------------------------------------------

Delete this folder. To also remove saved settings and recent-file
history, delete:

   %APPDATA%\DeskX


--------------------------------------------------------------------
 NEED HELP?
--------------------------------------------------------------------

GUI: open DeskX and click Help at the bottom of the left sidebar.
CLI: run  .\deskx.exe --help  or  .\deskx.exe sanitize --help

====================================================================
