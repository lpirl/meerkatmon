# MeerkatMon

This script is intended to provide a simple way of monitoring different
kinds of services.

## Installation

TODO

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
