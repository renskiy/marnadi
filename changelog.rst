Changelog
=========

.. currentmodule:: marnadi

Release 0.5.0
-------------

- Fix: fixed compatibility with the Python built-in `wsgiref` module
- Fix: Request.content_length is always of int type
- Fix: fixed len(Header)
- Fix #16: http.Error supplies 'Content-Length' header
- Enhancement: moved HttpError to http.Error
- Enhancement: added tests of http.Data

Release 0.4.2
-------------

- Enhancement: Response and Route became project global
- Enhancement: removed support of Python 3.2 and 3.3 due to incompatibility

Release 0.4.1
-------------

- Enhancement: route sequences can include routes and another sequences (nested route sequences)
- Enhancement: enabled Travis CI integration
- Enhancement: added default Content-Type

Release 0.4.0
-------------

- Enhancement: completely reworked project structure
- Enhancement: Route now has explicit subroutes
- Enhancement: added special http.Method descriptor which can be used for decorating function handlers
- Enhancement: Lazy made its variable private
- Enhancement: Response sets new value of Content-Length even if it's already set

Release 0.3.2
-------------

- Enhancement: reworked starting of response generation

Release 0.3.1
-------------

- Fix: uncaught exceptions are now reraised

Release 0.3.0
-------------

- Enhancement: the Response class now implements collections.Iterator interface
- Enhancement: reworked functional part of the Response class
- Enhancement: added descriptor behavior to the Lazy class

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
