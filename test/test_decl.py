import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient
from groundling.declaroute import Mkroute
from groundling.declquery import SelectQuery, InsertQuery, UpdateQuery, PermissionList

app = Starlette(debug=True)

Mkroute(
  route='/users/self',
  queries={'user': SelectQuery('* from users')},
  help="your profile",
).get(app)

Mkroute(
  route='/users/{userid}',
  queries={'user': SelectQuery(
    '* from users',
    user_param=False,
    path_params=True,
  )},
  help="any user's profile",
).get(app)

Mkroute(
  route='/item',
  queries={'item': InsertQuery(
    'items',
    params={'body_param': 'database_column'},
    literals={'another_column': 100},
    idcol='id',
    path_params=True,
  )},
  help="insert a thing",
).post(app)

Mkroute(
  route='/item/{id}',
  queries={
    'set': UpdateQuery('items', params={'body_param': 'database_column'}, path_params=True, user_param=None),
  },
  permission=PermissionList([SelectQuery('count(*) from items', path_params=True)]),
  help="update a thing"
).patch(app)

@pytest.mark.skip
def test_mkroute_get():
  client = TestClient(app)
  res = client.get('/users/me')
  assert res.status == 200
  raise NotImplementedError
