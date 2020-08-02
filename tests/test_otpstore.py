#!/usr/bin/env python

"""Tests for `otpstore` package."""

import pytest


from otpstore import OtpStore
from time import sleep

QUICK_EXPIRY_TIMEOUT_SECONDS = 3


@pytest.fixture
def otp_store_with_defaults():
    otpstore = OtpStore()
    yield otpstore
    otpstore.delete_all()


@pytest.fixture
def otp_store_with_quick_expiry():
    otpstore = OtpStore(expiry_seconds=QUICK_EXPIRY_TIMEOUT_SECONDS)
    yield otpstore
    otpstore.delete_all()


def test_otp_generation(otp_store_with_defaults):
    key = "test@example.com"
    otp_store_with_defaults.set_otp(key)
    val = otp_store_with_defaults.get_otp_dict(key)
    assert "otps" in val


def test_otp_get(otp_store_with_defaults):
    key = "test1@example.com"
    otp = "O2179897"
    otp_store_with_defaults.set_otp(key, otp)
    assert otp_store_with_defaults.get_otp(key) == otp


def test_otp_verification(otp_store_with_defaults):
    key = "test1@example.com"
    otp = "O21790T7"
    set_otp = otp_store_with_defaults.set_otp(key, otp)
    print("set otp is ", set_otp)
    print("otp dict is ", otp_store_with_defaults.get_otp_dict(key))
    verified, msg = otp_store_with_defaults.verify_otp(key, otp)
    print("Message is ", msg)
    assert verified


def test_otp_expiry(otp_store_with_quick_expiry):
    key = "test2@example.com"
    otp = "D21790T7"
    otp_store_with_quick_expiry.set_otp(key, otp)
    sleep(QUICK_EXPIRY_TIMEOUT_SECONDS + 1)
    verified, msg = otp_store_with_quick_expiry.verify_otp(key, otp)
    assert not verified and msg == "OTP has expired. Try generating the OTP again"


def test_otp_before_expiry(otp_store_with_quick_expiry):
    key = "test3@example.com"
    otp = "A1B2C345"
    otp_store_with_quick_expiry.set_otp(key, otp)
    sleep(QUICK_EXPIRY_TIMEOUT_SECONDS - 1)
    verified, msg = otp_store_with_quick_expiry.verify_otp(key, otp)
    assert verified
