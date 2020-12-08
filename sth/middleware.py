import os
from aiofiles.os import stat as aio_stat
from starlette.authentication import AuthenticationBackend, AuthCredentials
from starlette.staticfiles import StaticFiles

def flash_middleware(request, call_next):
  request.state.flashm = request.session.pop('flashm', None)
  return call_next(request)

def flash(request, message):
  "message flashing a la flask, rails, django etc"
  request.session['flashm'] = message

class StaticFilesSym(StaticFiles):
  "subclass StaticFiles middleware to allow symlinks"
  async def lookup_path(self, path):
    for directory in self.all_directories:
      full_path = os.path.realpath(os.path.join(directory, path))
      try:
        stat_result = await aio_stat(full_path)
        return (full_path, stat_result)
      except FileNotFoundError:
        pass
    return ("", None)

class AuthBackend(AuthenticationBackend):
  async def authenticate(self, request): # pylint: disable=arguments-differ
    userid = request.session.get('userid')
    if userid:
      return AuthCredentials(['authenticated']), userid

def use_all(app):
  "register all middlewares on app, doubles as documentation for how to install the middlewares"
  raise NotImplementedError
