from sth import orm

def test_operator_detection():
  assert orm.render_where_field(1, 'a') == 'a = $1'
  assert orm.render_where_field(1, 'a =') == 'a = $1'
  assert orm.render_where_field(1, 'a <') == 'a < $1'
  assert orm.render_where_field(1, 'a >=') == 'a >= $1'
  assert orm.render_where_field(1, 'a like') == 'a like $1'
  assert orm.render_where_field(1, 'a ilike') == 'a ilike $1'
  assert orm.render_where_field(1, 'a LIKE') == 'a LIKE $1'
  assert orm.render_where_field(1, 'a like $') == 'a like $1'
  assert orm.render_where_field(1, 'a >= any($)') == 'a >= any($1)'

def test_select():
  assert orm.format_select("a, b from table", {'x': 1}, (), None) == ('select a, b from table where x = $1', 1)
  assert orm.format_select("a, b from table", {'x': 1}, (), 'limit 10') == ('select a, b from table where x = $1 limit 10', 1)
  assert orm.format_select("a, b from table", {'x': 1}, ('y is null',), None) == ('select a, b from table where x = $1 and y is null', 1)
  assert orm.format_select("a, b from table", {'x <': 1}, ('y is null',), None) == ('select a, b from table where x < $1 and y is null', 1)
