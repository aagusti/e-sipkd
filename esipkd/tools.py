import os
import re
import json
import urllib2
import urllib
from email.utils import parseaddr
import colander
from types import (
    IntType,
    LongType,
    )
from datetime import (
    datetime,
    timedelta,
    )
import locale
import pytz
from pyramid.threadlocal import get_current_registry    


################
# Phone number #
################
MSISDN_ALLOW_CHARS = map(lambda x: str(x), range(10)) + ['+']
BULANS = ((1,'Januari'),
          (2,'Februari'),
          (3,'Maret'),
          (4,'April'),
          (5,'Mei'),
          (6,'Juni'),
          (7,'Juli'),
          (8,'Agustus'),
          (9,'September'),
          (10,'Oktober'),
          (11,'November'),
          (12,'Desember'),
          )
          
def email_validator(node, value):
    name, email = parseaddr(value)
    if not email or email.find('@') < 0:
        raise colander.Invalid(node, 'Invalid email format')
        
def get_msisdn(msisdn, country='+62'):
    for ch in msisdn:
        if ch not in MSISDN_ALLOW_CHARS:
            return
    try:
        i = int(msisdn)
    except ValueError, err:
        return
    if not i:
        return
    if len(str(i)) < 7:
        return
    if re.compile(r'^\+').search(msisdn):
        return msisdn
    if re.compile(r'^0').search(msisdn):
        return '%s%s' % (country, msisdn.lstrip('0'))

################
# Money format #
################
def should_int(value):
    int_ = int(value)
    return int_ == value and int_ or value

def thousand(value, float_count=None):
    if float_count is None: # autodetection
        if type(value) in (IntType, LongType):
            float_count = 0
        else:
            float_count = 2
    return locale.format('%%.%df' % float_count, value, True)

def money(value, float_count=None, currency=None):
    if value < 0:
        v = abs(value)
        format_ = '(%s)'
    else:
        v = value
        format_ = '%s'
    if currency is None:
        currency = locale.localeconv()['currency_symbol']
    s = ' '.join([currency, thousand(v, float_count)])
    return format_ % s

###########    
# Pyramid #
###########    
def get_settings():
    return get_current_registry().settings
    
def get_timezone():
    settings = get_settings()
    return pytz.timezone(settings.timezone)

########    
# Time #
########
one_second = timedelta(1.0/24/60/60)
TimeZoneFile = '/etc/timezone'
if os.path.exists(TimeZoneFile):
    DefaultTimeZone = open(TimeZoneFile).read().strip()
else:
    DefaultTimeZone = 'Asia/Jakarta'

def as_timezone(tz_date):
    localtz = get_timezone()
    if not tz_date.tzinfo:
        tz_date = create_datetime(tz_date.year, tz_date.month, tz_date.day,
                                  tz_date.hour, tz_date.minute, tz_date.second,
                                  tz_date.microsecond)
    return tz_date.astimezone(localtz)    

def create_datetime(year, month, day, hour=0, minute=7, second=0,
                     microsecond=0):
    tz = get_timezone()        
    return datetime(year, month, day, hour, minute, second,
                     microsecond, tzinfo=tz)

def create_date(year, month, day):    
    return create_datetime(year, month, day)
    
def create_now():
    tz = get_timezone()
    return datetime.now(tz)
    
def _DTstrftime(chain):
    ret = chain and datetime.strftime(chain, "%d-%m-%Y")
    if ret:
      return ret
    else:
      return chain
      
def _DTnumberformat(chain):
    import locale
    locale.setlocale(locale.LC_ALL, 'id_ID.utf8')
    ret = locale.format("%d", chain, grouping=True)
    if ret:
      return ret
    else:
      return chain
      
def _DTactive(chain):
    ret = chain==1 and 'Aktif' or 'Inaktif'
    if ret:
      return ret
    else:
      return chain
      
class RecaptchaResponse(object):
    def __init__(self, is_valid, error_code=None):
        self.is_valid = is_valid
        self.error_code = error_code

def captcha_submit(recaptcha_challenge_field,
            recaptcha_response_field,
            private_key,
            remoteip):
    """
    Submits a reCAPTCHA request for verification. Returns RecaptchaResponse
    for the request

    recaptcha_challenge_field -- The value of recaptcha_challenge_field from the form
    recaptcha_response_field -- The value of recaptcha_response_field from the form
    private_key -- your reCAPTCHA private key
    remoteip -- the user's ip address
    """

    if not (recaptcha_response_field and recaptcha_challenge_field and
            len (recaptcha_response_field) and len (recaptcha_challenge_field)):

        return RecaptchaResponse (is_valid = False, error_code = 'incorrect-captcha-sol')


    def encode_if_necessary(s):
        if isinstance(s, unicode):
            return s.encode('utf-8')
        return s

    params = urllib.urlencode ({
            'privatekey':  encode_if_necessary(private_key),
            'remoteip'  :  encode_if_necessary(remoteip),
            'secret'    :  encode_if_necessary(recaptcha_challenge_field),
            'response'  :  encode_if_necessary(recaptcha_response_field),
            })
            
    #print "https://%s/recaptcha/api/siteverify" % VERIFY_SERVER
    request = urllib2.Request (
        url = "https://www.google.com/recaptcha/api/siteverify",
        data = params,
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "User-agent": "reCAPTCHA Python"
            }
        )
    httpresp = urllib2.urlopen (request)

    return_values = json.loads(httpresp.read())
    httpresp.close()

    return_code = return_values['success']
    if (return_code == True):
        return RecaptchaResponse (is_valid=True)
    else:
        return RecaptchaResponse (is_valid=False, error_code = return_values['error_code'])
