import inspect, json, logging, os, sys, uuid
import httpx
from starlette.background import BackgroundTask
from . import conf

def stackdriver_error(message):
  frame = inspect.stack()[1]
  sys.stderr.write(json.dumps({
    "serviceContext": {"service": conf.SERVICE_NAME},
    "message": message,
    "@type": "type.googleapis.com/google.devtools.clouderrorreporting.v1beta1.ReportedErrorEvent",
    "context": {
      "reportLocation": {
        "filePath": frame.filename,
        "lineNumber": frame.lineno,
        "functionName": frame.function,
      },
    },
  }) + '\n')

async def send_mixpanel(userid, event):
  "don't call directly -- use mixpanel_bg and background= in starlette Response"
  token = os.environ.get('MIXPANEL_TOKEN')
  if not token:
    print('warning: mixpanel not initialized')
    return
  if isinstance(userid, uuid.UUID): # to prevent json error
    userid = str(userid)
  async with httpx.AsyncClient() as client:
    res = await client.post(
      "https://api.mixpanel.com/track#live-event",
      data={
        'data': json.dumps({
          'event': event,
          'properties': {
            'token': token,
            'distinct_id': userid,
          },
        }),
      },
    )
    res.raise_for_status()
    if res.text != '1':
      print('warning: non-1 response from mixpanel')

def mixpanel_bg(*args):
  return BackgroundTask(send_mixpanel, *args)

async def send_email(dest, subject, body, from_=None):
  from_ = from_ or conf.DEFAULT_FROM_ADDR
  if from_.endswith('@'):
    from_ = from_ + conf.DOMAIN
  logging.debug('send_email %s %s', dest, subject)
  # todo: queue this instead
  if 'POSTMARK_TOKEN' not in os.environ:
    print('warning: no postmark token, skipping email')
    return False
  async with httpx.AsyncClient() as client:
    res = await client.post(
      "https://api.postmarkapp.com/email",
      headers={'Accept': 'application/json', 'X-Postmark-Server-Token': os.environ['POSTMARK_TOKEN']},
      json={
        'From': from_,
        'To': dest,
        'Subject': subject,
        'HtmlBody': body,
        'MessageStream': 'outbound',
      },
    )
    res.raise_for_status()
  return True
