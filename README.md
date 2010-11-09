BFiCal
======

About
-----
BFiCal is an appengine application that generates an icalendar version of the BFI listings  (currently only for the southbank). The intention is for users to import this .ics file into something that does calendars properly. And iCal. snark.

There's a basic site that lets you navigate the listings by day/week, view listing by year/participant and save calendar reminders for individual showings.

Why
---
I love the BFI, but I find their website intensely frustrating to navigate. BFiCal is an attempt to make that process easier.
I'm keeping the number/frequency of requests to a low level - the spider uses a custom user-agent and honours robots.txt if that were to ever become a problem.

Who
---
BFiCal was created by Ben Burry, with styles and graphics by Alexandra Deschamps-Sonsino. Thanks Alex.


TODO
----
 * Add IMAX listings
 * Add search
 * More caching. Appengine can be a touch slow on the data queries
 * Fix the parser. BFiCal screenscrapes to get its data - this will inevitably break
