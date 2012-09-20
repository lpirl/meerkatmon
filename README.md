# MeerkatMon

This script is intended to provide a simple way of monitoring different
kinds of services.

## Installation

First, make sure your server can send mails.
This should lead to an email in your inbox:

	echo "foo" | sendmail -t your_mail_address@example.com

If you *have* installed and configured services (to be monitored),
this is a cakewalk:

	cd /your/desired/location/
	git clone git://github.com/lpirl/meerkatmon.git
	cd meerkatmon
	nano meerkatmon.conf

Add all services to be monitored, exit the editor
and - optionally - check if everything works as expected:

	./meerkatmon.py

Then, add for example

	*/23 * * * * /usr/bin/python3 -O /your/desired/location/meerkatmon/meerkatmon.py

to check all services every 23 minutes to your crontab using `crontab -e`,
preferably *NOT* as root.

	crontab -e

Done.

## Simplicity

In contrast to fully bloated monitoring tools,
it is neither required to setup or maintain additional services
(such as web or database servers), nor to learn new methods of
configuration or installation.
It makes use of tools, that are present on nearly every server
(Python, Cron and the facility to send mails).

## Flexibility

MeerkatMon offers strategies in the submodule `strategies`
(just one at the moment...) to check the availability of services.
Administrators/Developers can easily provide new strategies by
implementing a small interface on a class in this module.
