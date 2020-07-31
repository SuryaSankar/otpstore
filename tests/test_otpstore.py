#!/usr/bin/env python

"""Tests for `otpstore` package."""

import pytest


from otpstore import OtpStore


@pytest.fixture
def otp_store_with_defaults():
    return OtpStore()


def test_otp_generation(otp_store_with_defaults):
	key = "test@example.com"
	otp_store_with_defaults.set_otp(key)
	val = otp_store_with_defaults.get(key)
	assert "otps" in val

def test_otp_verification(otp_store_with_defaults):
	pass
