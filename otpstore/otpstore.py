"""Main module."""
from toolspy import random_string
import string
import redis
import json


class OtpStore(object):

    def __init__(
            self, redis_client=None, redis_host=None,
            prefix="$otp:",
            otp_length=8, otp_charset=None, expiry_seconds=300,
            generation_attempts=3, verification_attempts=2):
        self.initialize(
            redis_client=redis_client,
            prefix=prefix,
            redis_host=redis_host, otp_length=otp_length,
            expiry_seconds=expiry_seconds,
            generation_attempts=generation_attempts,
            verification_attempts=verification_attempts,
            otp_charset=otp_charset
        )

    def initialize(
            self, redis_client=None, redis_host=None,
            prefix="$otp:",
            otp_length=8, otp_charset=None, expiry_seconds=300,
            generation_attempts=3, verification_attempts=2):
        if redis_client:
            self.redis_client = redis_client
        else:
            if redis_host is None:
                redis_host = "localhost"
            self.redis_client = redis.StrictRedis(host=redis_host)
        self.otp_length = otp_length
        if otp_charset:
            self.otp_charset = otp_charset
        else:
            self.otp_charset = string.digits + string.ascii_letters
        self.expiry_seconds = expiry_seconds
        self.generation_attempts = generation_attempts
        self.verification_attempts = verification_attempts
        self.prefix = prefix

    def _with_prefix(self, key):
        return "{}{}".format(self.prefix, key)

    def _set(self, key, value):
        return self.redis_client.set(self._with_prefix(key), value)

    def _get(self, key):
        return self.redis_client.get(self._with_prefix(key))

    def _expire(self, key, expiry_seconds):
        self.redis_client.expire(self._with_prefix(key), expiry_seconds)

    def _generate_otp_string(self, otp_length=None, otp_charset=None):
        if otp_length is None:
            otp_length = self.otp_length
        if otp_charset is None:
            otp_charset = self.otp_charset
        return random_string(length=otp_length, candidates=otp_charset)

    def _generate_otp_dict(self, otp=None):
        if otp is None:
            otp = self._generate_otp_string()
        return {
            "otps": [otp],
            "verifs_left": self.verification_attempts,
        }

    def _generate_otp_dict_json(self, otp=None):
        return json.dumps(self._generate_otp_dict(otp=otp))

    def keys(self):
        return self.redis_client.keys("{}*".format(self.prefix))

    def delete(self, key):
        return self.redis_client.delete(self._with_prefix(key))

    def delete_all(self):
        keys = self.keys()
        if len(keys) > 0:
            self.redis_client.delete(*keys)

    def get_otp_dict(self, key):
        otpjson = self._get(key)
        if otpjson:
            return json.loads(otpjson)
        return None

    def get_otp(self, key):
        otp_dict = self.get_otp_dict(key)
        if otp_dict:
            return otp_dict['otps'][-1]
        return None

    def set_otp(self, key, otp=None, expiry_seconds=None):
        otp_dict = self.get_otp_dict(key)
        if otp_dict:
            print("got otp dict as ", otp_dict)
            if len(otp_dict['otps']) >= self.generation_attempts:
                raise Exception(
                    "Only {} otps can be generated within a span of {} seconds".format(
                        self.generation_attempts, self.expiry_seconds))
            else:
                print("in else condition")
                otp_dict['otps'].append(otp or self._generate_otp_string())
                self._set(key, json.dumps(otp_dict))
        else:
            self._set(key, self._generate_otp_dict_json(otp=otp))
        if expiry_seconds is None:
            expiry_seconds = self.expiry_seconds
        if expiry_seconds:
            self._expire(key, expiry_seconds)
        return self.get_otp(key)

    def verify_otp(self, key, otp):
        otp_dict = self.get_otp_dict(key)
        if otp_dict:
            if otp_dict['verifs_left'] <= 0:
                return (False, "Too many wrong attempts. Try generating otp again after some time.")
            otp_dict['verifs_left'] -= 1
            if otp in otp_dict['otps']:
                return (True, None)
            return (False, "Invalid OTP.")
        return (False, "OTP has expired. Try generating the OTP again")
