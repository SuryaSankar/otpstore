"""Main module."""
from toolspy import random_string
import redis
import json

class OtpStore(object):

	def __init__(
			self, redis_client=None, redis_host="localhost", 
			otp_length=8, expiry_seconds=120,
			generation_attempts=3, verification_attempts=2):
		if redis_client:
			self.redis_client = redis_client
		else:
			self.redis_client = redis.StrictRedis(host=redis_host)
		self.otp_length = otp_length
		self.expiry_seconds = expiry_seconds
		self.generation_attempts = generation_attempts
		self.verification_attempts = verification_attempts

	def set(self, key, value):
		return self.redis_client.set(key, value)

	def get(self, key):
		return self.redis_client.get(key)

	def has(self, key):
		return self.get(key) is not None

	def generate_otp_dict(self, otp=None):
		if otp is None:
			otp = random_string(self.otp_length)
		return {
			"otps": [otp],
			"verifs_left": self.verification_attempts,
		}

	def initialize_key(self, key, otp=None):
		self.set(key, json.dumps(self.generate_otp_dict(otp=otp)))

	def set_otp(self, key, otp=None):
		otp_dict = self.get(key)
		if otp_dict:
			if len(otp_dict['ops']) >= self.generation_attempts:
				raise Exception(
					"Only {} otps can be generated within a span of {} seconds".format(
						self.generation_attempts, self.expiry_seconds))
			else:
				otp_dict['otps'].append(self.generate_otp_dict(otp=otp))
		else:
			self.initialize_key(key, otp=otp)

	def verify_otp(self, key, otp):
		otp_dict = self.get(key)
		if otp_dict:
			if otp_dict['verifs_left'] <= 0:
				return (False, "Too many wrong attempts. Try generating otp again after some time.")
			otp_dict['verifs_left'] -= 1
			if otp in otp_dict['otps']:
				return (True, None)
			return (False, "Invalid OTP.")
		return (False, "OTP has expired. Try generating the OTP again")




