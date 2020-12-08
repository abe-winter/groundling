"user management helpers"

import uuid, os, binascii
import scrypt, asyncpg
from starlette.routing import Router
from starlette.exceptions import HTTPException
from starlette.authentication import requires
from starlette.responses import RedirectResponse, PlainTextResponse
from . import util, middleware
from .util import tobytes
from .clients import mixpanel_bg, send_email
from .orm import select, update, insert

# todo: move these to conf
USE_MIXPANEL = False
SITE_NAME = None
FROM_ADDR = None
HOME = None # name of home route

app = Router()

async def login_helper(request, form):
  row = await select(util.POOL, "userid, pass_hash, pass_salt from users", {'email': form['email']})
  if not row:
    middleware.flash(request, "No account with that email")
    return RedirectResponse(request.url_for('get_login'), status_code=302)
  if tobytes(row['pass_hash']) != scrypt.hash(form['password'].encode(), tobytes(row['pass_salt'])):
    middleware.flash(request, "Bad password")
    return RedirectResponse(request.url_for('get_login'), status_code=302)
  request.session['userid'] = str(row['userid'])
  bgtask = mixpanel_bg(request.session['userid'], 'login.email') if USE_MIXPANEL else None
  return RedirectResponse(request.url_for(HOME), status_code=302, background=bgtask)

def check_password(password):
  if len(password) < 5:
    raise HTTPException(400, "minimum password length is 5")

def check_email(email):
  if '@' not in email:
    raise HTTPException(400, "doesn't look like an email")

async def join_helper(request, form):
  check_password(form['password'])
  check_email(form['email'])
  userid = str(uuid.uuid4())
  pass_salt = os.urandom(64)
  pass_hash = scrypt.hash(form['password'].encode(), pass_salt)
  # todo: need to normalize email or aliasers like me will be in trouble
  try:
    await insert(util.POOL, "users", {'userid': userid, 'email': form['email'], 'pass_hash': pass_hash, 'pass_salt': pass_salt})
  except asyncpg.UniqueViolationError:
    middleware.flash(request, "That email already has an account")
    return RedirectResponse(request.url_for('get_join'), status_code=302)
  request.session['userid'] = userid
  bgtask = mixpanel_bg(request.session['userid'], 'join.email') if USE_MIXPANEL else None
  return RedirectResponse(request.url_for(HOME), status_code=302, background=bgtask)

VERIFY_TEMPLATE = """<html><body>
  <h4>Thanks for joining {site_name}</h4>
  <p>Click below to verify your email:</p>
  <a href="{url}">{url}</a>
  <br>
  <p>You're getting this because someone signed up with your email. If that wasn't you, reply to this email and we can work with you to transfer ownership of the account.</p>
</body></html>"""

@app.route('/send-verify', methods=['POST'])
@requires('authenticated')
async def send_verify(request):
  shortcode = binascii.hexlify(os.urandom(24)).decode()
  async with util.POOL.acquire() as con:
    row = await select(con, "email from users", {'userid': request.user})
    await update(con, "users", {'verification_token': shortcode}, {'userid': request.user})
  await send_email(
    row['email'], subject=f"Verify your {SITE_NAME} email",
    body=VERIFY_TEMPLATE.format(url=request.url_for('re_verify', shortcode=shortcode)),
    from_=FROM_ADDR,
  )
  bgtask = mixpanel_bg(request.user, 'verify.start') if USE_MIXPANEL else None
  middleware.flash(request, "Verification email sent") # warning: this doesn't work because home.htm is SPA
  return RedirectResponse(request.url_for(HOME), status_code=302, background=bgtask)

@app.route('/verify/{shortcode}')
async def re_verify(request):
  # todo: doc why this doesn't require logged in session (people click from email)
  shortcode = request.path_params['shortcode']
  async with util.POOL.acquire() as con, con.transaction():
    row = await select(con, "userid, email, email_verified, verification_token from users", {'verification_token': shortcode})
    if row is None or row['verification_token'] != shortcode or row['email_verified'] is not None:
      raise HTTPException(400, "Bad code or already verified")
    if 'userid' in request.session and str(row['userid']) != request.session['userid']:
      raise HTTPException(403, "You're redeeming a token for a different user. You can do this if you (1) log out or (2) use an incognito tab or different browser")
    await update(con, "users", {}, {'userid': row['userid']}, literals=['email_verified = now()'])
  bgtask = mixpanel_bg(request.user, 'verify.ok') if USE_MIXPANEL else None
  middleware.flash(request, 'Thanks for verifying your email!') # warning: this doesn't work because home.htm is SPA
  if 'userid' in request.session:
    return RedirectResponse(request.url_for(HOME), background=bgtask)
  else:
    return PlainTextResponse("Thanks for verifying! Log in or go to a browser where you're logged in.")
