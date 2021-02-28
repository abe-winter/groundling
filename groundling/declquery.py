"declarative queries"

from dataclasses import dataclass, field
from starlette.exceptions import HTTPException
from . import util, orm

MULTI = {'fetch': 'fetch'}

@dataclass
class Pager:
  "paging control"
  order_by: str
  per_page: int = 10
  page_param: str = 'page'

  def suffix(self, request):
    page = int(request.query_params[self.page_param])
    offset = page * self.per_page
    return f"order by {self.order_by} offset {offset} limit {self.per_page}"

class PermissionList(list):
  "note: this is a list because it's not always going to be an easy join"

  async def check(self, con, request):
    if len(self) == 0:
      return
    for perm in self:
      row = await perm.run(con, request)
      if row['count']:
        # todo: permit permission lambda instead of relying on count
        break
    else:
      raise HTTPException(404, "not found or no permission")

@dataclass
class BaseQuery:
  "thing for running a query based on route params"
  query: str # this is table for inserts
  params: dict = field(default_factory=dict)
  user_param: str = 'userid' # None to omit
  query_kwargs: dict = field(default_factory=dict)
  idcol: str = None # todo: maybe move this to Mkroute, probably should agree for all queries
  literals: dict = field(default_factory=dict) # warning: literals as in not path params, but not sql literals. use query_kwargs for that.
  path_params: bool = False # when True, merge path_params into query_params

  def query_params(self, request, query_params):
    "common query param logic"
    if self.path_params:
      # careful: param order is load-bearing in insert(). some callers rely on path params being first. better to expose named params from ORM
      query_params.update(request.path_params)
    if self.user_param:
      query_params[self.user_param] = request.user
    return query_params

  async def load_body_params(self, request, params):
    "load body params into query or update (passed in)"
    if self.params:
      body = await request.json()
    for body_param, dbcol in self.params.items():
      if isinstance(dbcol, str):
        params[dbcol] = body[body_param] if body_param in body else request.path_params[body_param]
      else:
        raise TypeError('weird val type', type(dbcol))
    return params

@dataclass
class SelectQuery(BaseQuery):
  multi: bool = False # multiple rows instead of single row
  pager: Pager = None

  async def run(self, con, request, new_id=None): # pylint: disable=unused-argument
    query_params = self.query_params(request, {})
    query_params.update(self.literals)

    # unpack route params
    for rparam, dbcol in self.params.items():
      if isinstance(dbcol, str):
        query_params[dbcol] = request.path_params[rparam]
      elif isinstance(dbcol, tuple):
        dbcol, transform = dbcol
        query_params[dbcol] = transform(request.path_params[rparam])
      else:
        raise TypeError('weird val type', type(dbcol))

    if self.pager is not None:
      assert self.multi
      raise NotImplementedError("todo: paging suffix")

    return util.prep_serial(await orm.select(con, self.query, query_params, **self.query_kwargs, **(MULTI if self.multi else {})))

@dataclass
class UpdateQuery(BaseQuery):
  async def run(self, con, request, new_id=None): # pylint: disable=unused-argument
    query_params = self.query_params(request, {})
    query_params.update(self.literals)
    update_params = await self.load_body_params(request, {})
    return await orm.update(con, self.query, update_params, query_params, **self.query_kwargs)

@dataclass
class InsertQuery(BaseQuery):
  async def run(self, con, request, new_id=None):
    query_params = self.query_params(request, {})
    if new_id is not None:
      # null case is inserts from non-POST, I think
      query_params[self.idcol] = new_id
    for key, val in self.literals.items():
      if callable(val):
        query_params[key] = val(request, await request.json())
      else:
        query_params[key] = val
    await self.load_body_params(request, query_params)
    return await orm.insert(con, self.query, query_params, **self.query_kwargs)
