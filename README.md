# sth - starlette helpers

Kitchen sink package for ramping up my small starlette projects.

This project exposes:

* a micro-orm on asyncpg
* routes, helpers + middleware for user management / authentication
* httpx (async) clients for postmark (email) + mixpanel
* stackdriver error formatter
* flash message
* some json parser / serializer stuff for types
* symlink-aware version of starlette's static files middleware to support frontend watch builds
