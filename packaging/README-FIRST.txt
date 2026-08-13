====================================================================
 DeskX - Data Sanitizer
 Version 0.1.0  |  Windows
====================================================================

Clean and anonymize spreadsheets before you share them. Everything
runs on your own computer - no internet connection, no account, no
data ever leaves your machine.


--------------------------------------------------------------------
 HOW TO START
--------------------------------------------------------------------

1. Unzip this folder anywhere you like (Desktop or Documents is fine).
   Keep all the files together - DeskX.exe needs the files next to it.

2. Double-click  DeskX.exe

That's it. There is nothing to install and you do not need Python.


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

   Upload  ->  Preview  ->  Configure  ->  Review
           ->  Choose where to save  ->  Process  ->  Done

DeskX suggests which columns look sensitive (emails, phone numbers,
names, IDs) and lets you mask, hash, pseudonymize, or remove them.


--------------------------------------------------------------------
 YOUR ORIGINAL FILE IS NEVER TOUCHED
--------------------------------------------------------------------

DeskX always writes a separate, cleaned copy. It will refuse to save
over your source file, and it never silently replaces an existing
result - you are asked first.

By default, cleaned files are saved to:

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

Open DeskX and click  Help  at the bottom of the left sidebar.

====================================================================
