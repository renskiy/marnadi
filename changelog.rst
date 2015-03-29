Changelog
=========

.. currentmodule:: marnadi

Release 0.2.9
-------------

- Enhancement: Header's __hash__() uses main value (w/o params) to calculate hash
- Enhancement: Header implements collections.Mapping interface
- Enhancement: added query_string, remote_addr, remote_host properties to the Request
- Enhancement: Request's environ property became public
- Enhancement: HttpError implements collections.Iterable and collections.Sized interfaces

Release 0.2.8
-------------

- Enhancement #15: added ability to provide param callback mapping when instantiating the `Route`

Release 0.2.7
-------------

- Fix #14: Fixed cookies with international locales

Release 0.2.6
-------------

- Fix: Fixed HttpError, responses due to not supported and not allowed methods
