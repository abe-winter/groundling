# pylint: disable=too-many-arguments
"ultra lightweight ORM on top of asyncpg"

import re, logging
import asyncpg

RE_OPERATOR = re.compile(r'([=<>]+|i?like)', re.I)

def render_where_field(index, key):
  "assumes operator-less keys are intended to be =, leaves it alone if it has an operator, detects tails too for any($1) support"
  match = RE_OPERATOR.search(key)
  if match:
    if match.end() < len(key):
      return key[:match.end()] + key[match.end():].replace('$', f"${index}")
    else:
      return f"{key} ${index}"
  else:
    return f"{key} = ${index}"

def format_whereclause(where, where_literal=None, base_index=0):
  where_literal = where_literal or {}
  return ' and '.join([render_where_field(i + base_index + 1, key) for i, key in enumerate(where)] + list(where_literal or ()))

def format_select(fields, where, where_literal, suffix):
  "returns (query, params)"
  return (f"select {fields} {'where' if where or where_literal else ''} {format_whereclause(where, where_literal)}{' ' + suffix if suffix else ''}", *where.values())

async def run_query(con_or_pool, method, args):
  "indirection that resolves method name (i.e. db.execute vs db.fetch) and supports pool as well as con"
  if isinstance(con_or_pool, asyncpg.pool.Pool):
    async with con_or_pool.acquire() as con:
      return await getattr(con, method)(*args)
  else:
    return await getattr(con_or_pool, method)(*args)

def select(con_or_pool, fields, where, fetch='fetchrow', where_literal=(), suffix=None):
  "orm-light: one-line wrapper for selecting a single row"
  # yes dictionary order is guaranteed in 3.7+ https://mail.python.org/pipermail/python-dev/2017-December/151283.html
  args = format_select(fields, where, where_literal, suffix)
  logging.debug('select %s', args[0])
  return run_query(con_or_pool, fetch, args)

def insert(con_or_pool, table, fields, suffix='', literals=None):
  "orm-light insert shortcut"
  literals = literals or {}
  subs = ','.join([f'${i + 1}' for i in range(len(fields))] + list(literals.values()))
  all_fields = (*fields, *literals)
  args = (f"insert into {table} ({','.join(all_fields)}) values ({subs}) " + suffix, *fields.values())
  logging.debug('insert %s', args[0])
  return run_query(con_or_pool, 'execute', args)

def update(con_or_pool, table, fields, where, literals=None, suffix=None, method='execute'):
  "literals here are set x=y, not where fields"
  # note: render_where_field below to support like {'x = $ + 1': val}, i.e. expressions right of operator
  set_stmts = [render_where_field(i + 1, field) for i, field in enumerate(fields)] + list(literals or ())
  query = f"update {table} set {', '.join(set_stmts)} where {format_whereclause(where, base_index=len(fields))} {suffix or ''}"
  args = (query, *fields.values(), *where.values())
  logging.debug('update %s %s', method, args[0])
  return run_query(con_or_pool, method, args)
