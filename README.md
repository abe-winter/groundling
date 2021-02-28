# groundling - starlette helpers and declarative routing

Kitchen sink package for ramping up my small starlette projects.

## Declarative routing

In the declaroute module this has wrappers for declarative routing. They're verbose and not documented, and won't save you any lines of code, but they work.

'declarative routing' means that path parameters and json body params are unpacked automatically into database queries, executed, and their results are returned.

## Other stuff

* a micro-orm on asyncpg
* routes, helpers + middleware for user management / authentication
* httpx (async) clients for postmark (email) + mixpanel
* stackdriver error formatter
* flash message
* some json parser / serializer stuff for types
* symlink-aware version of starlette's static files middleware to support frontend watch builds

You **must** set `DEBUG=1` if you're not on https or else sessions won't work.
