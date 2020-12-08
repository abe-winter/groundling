"config that must be set by importer"

USE_MIXPANEL = False # bool, whether to write to mixpanel
SITE_NAME = None # human-readable site name, used in emails
HOME = None # home route, for login redirect
SERVICE_NAME = None # for stackdriver
DEFAULT_FROM_ADDR = None # for sending emails
VERIFY_FROM_ADDR = None # for sending email verification messages
STATIC_DIR = 'backend/static' # path to static files

def init(params_dict):
  globals().update(params_dict)
