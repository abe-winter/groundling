# sth - starlette helpers

Kitchen sink package for ramping up my small starlette projects.

This project exposes:

* a micro-orm with async support
* a bunch of user-management middleware
* async harnesses for postmark (email) + mixpanel
* stackdriver error formatter
* more opinionated user auth
* barebones 'flash message' feature
* some json parser / serializer stuff for types
* symlink-aware version of starlette's static files middleware to support some development workflows
