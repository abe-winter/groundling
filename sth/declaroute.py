"declaroute -- declarative routing"

import uuid
from dataclasses import dataclass, field
from typing import Dict
from starlette.authentication import requires
from starlette.responses import JSONResponse
from . import util
from .declquery import BaseQuery, PermissionList

@dataclass
class Mkroute:
  "declarative constructor for an automatic starlette API routes on top of DB queries"
  route: str
  queries: Dict[str, BaseQuery]
  user_param: str = 'userid' # None to omit
  help: str = None # ship to docs somewhere
  authed: bool = True
  permission: PermissionList = field(default_factory=PermissionList)

  def get_or_patch(self, app, **kwargs):
    "common guts for get and patch"
    async def handler(request):
      res = {}
      async with util.POOL.acquire() as con, con.transaction():
        await self.permission.check(con, request)
        for name, query in self.queries.items():
          res[name] = await query.run(con, request)
      return JSONResponse(res)

    if self.authed:
      handler = requires('authenticated')(handler)
    return app.route(self.route, **kwargs)(handler)

  def get(self, app):
    "mount a get request"
    return self.get_or_patch(app)

  def patch(self, app):
    return self.get_or_patch(app, methods=['PATCH'])

  def post(self, app):
    "mount a post request, i.e. create a thing"
    async def handler(request):
      new_id = str(uuid.uuid4())

      async with util.POOL.acquire() as con, con.transaction():
        await self.permission.check(con, request)
        for _, query in self.queries.items():
          await query.run(con, request, new_id)
      return JSONResponse({next(iter(self.queries.values())).idcol: new_id})

    if self.authed:
      handler = requires('authenticated')(handler)
    return app.route(self.route, methods=['POST'])(handler)
