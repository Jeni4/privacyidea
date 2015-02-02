from .base import MyTestCase
import json
from privacyidea.lib.error import (TokenAdminError, ParameterError)
from privacyidea.lib.token import get_tokens
from privacyidea.lib.user import User
from urllib import urlencode

PWFILE = "tests/testdata/passwords"

import json
from .base import MyTestCase
from privacyidea.lib.resolver import (save_resolver)
from privacyidea.lib.realm import (set_realm)
from privacyidea.lib.user import (User)
from privacyidea.lib.tokenclass import TokenClass
from privacyidea.lib.tokens.totptoken import HotpTokenClass
from privacyidea.models import (Token,
                                 Config,
                                 Challenge, TokenRealm)
from privacyidea.lib.config import (set_privacyidea_config, get_token_types)
import datetime
from privacyidea.lib.token import (create_tokenclass_object,
                                    get_tokens,
                                    get_token_type, check_serial,
                                    get_num_tokens_in_realm,
                                    get_realms_of_token,
                                    token_exist, token_has_owner,
                                    get_token_owner, is_token_owner,
                                    get_tokenclass_info,
                                    get_tokens_in_resolver,
                                    get_all_token_users, get_otp,
                                    get_token_by_otp, get_serial_by_otp,
                                    get_tokenserial_of_transaction,
                                    gen_serial, init_token, remove_token,
                                    set_realms, set_defaults, assign_token,
                                    unassign_token, resync_token,
                                    reset_token, set_pin, set_pin_user,
                                    set_pin_so, enable_token,
                                    is_token_active, set_hashlib, set_otplen,
                                    set_count_auth, add_tokeninfo,
                                    set_sync_window, set_count_window,
                                    set_description, get_multi_otp,
                                    set_max_failcount, copy_token_pin,
                                    copy_token_user, lost_token,
                                    check_token_list, check_serial_pass,
                                    check_user_pass, auto_assign_token,
                                    get_dynamic_policy_definitions,
                                    get_tokens_paginate)

from privacyidea.lib.error import (TokenAdminError, ParameterError)


class ValidateAPITestCase(MyTestCase):
    """
    test the api.validate endpoints
    """

    def test_00_create_realms(self):
        self.setUp_user_realms()


        # create a  token and assign it to the user
        db_token = Token(self.serials[0], tokentype="hotp")
        db_token.update_otpkey(self.otpkey)
        db_token.save()
        token = HotpTokenClass(db_token)
        self.assertTrue(token.token.serial == self.serials[0], token)
        token.set_user(User("cornelius", self.realm1))
        token.set_pin("pin")
        self.assertTrue(token.token.user_id == "1000", token.token.user_id)

    def test_02_validate_check(self):
        # is the token still assigned?
        tokenbject_list = get_tokens(serial=self.serials[0])
        tokenobject = tokenbject_list[0]
        self.assertTrue(tokenobject.token.user_id == "1000",
                        tokenobject.token.user_id)

        """                  Truncated
           Count    Hexadecimal    Decimal        HOTP
           0        4c93cf18       1284755224     755224
           1        41397eea       1094287082     287082
           2         82fef30        137359152     359152
           3        66ef7655       1726969429     969429
           4        61c5938a       1640338314     338314
           5        33c083d4        868254676     254676
           6        7256c032       1918287922     287922
           7         4e5b397         82162583     162583
           8        2823443f        673399871     399871
           9        2679dc69        645520489     520489
        """
        # test for missing parameter user
        with self.app.test_request_context('/validate/check',
                                           method='POST',
                                           data={"pass": "pin287082"}):
            self.assertRaises(ParameterError, self.app.full_dispatch_request)

        # test for missing parameter serial
        with self.app.test_request_context('/validate/check',
                                           method='POST',
                                           data={"pass": "pin287082"}):
            self.assertRaises(ParameterError, self.app.full_dispatch_request)

        # test for missing parameter "pass"
        with self.app.test_request_context('/validate/check',
                                           method='POST',
                                           data={"serial": "123456"}):
            self.assertRaises(ParameterError, self.app.full_dispatch_request)


    def test_03_check_user(self):
        # get the original counter
        tokenobject_list = get_tokens(serial=self.serials[0])
        hotp_tokenobject = tokenobject_list[0]
        count_1 = hotp_tokenobject.token.count

        # test successful authentication
        with self.app.test_request_context('/validate/check',
                                           method='POST',
                                           data={"user": "cornelius",
                                                 "pass": "pin287082"}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = json.loads(res.data).get("result")
            self.assertTrue(result.get("status") is True, result)
            self.assertTrue(result.get("value") is True, result)

        # Check that the counter is increased!
        tokenobject_list = get_tokens(serial=self.serials[0])
        hotp_tokenobject = tokenobject_list[0]
        count_2 = hotp_tokenobject.token.count
        self.assertTrue(count_2 > count_1, (hotp_tokenobject.token.serial,
                                            hotp_tokenobject.token.count,
                                            count_1,
                                            count_2))

        # test authentication fails with the same OTP
        with self.app.test_request_context('/validate/check',
                                           method='POST',
                                           data={"user": "cornelius",
                                                 "pass": "pin287082"}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = json.loads(res.data).get("result")
            self.assertTrue(result.get("status") is True, result)
            self.assertTrue(result.get("value") is False, result)

    def test_03a_check_user_get(self):
        # Reset the counter!
        count_1 = 0
        tokenobject_list = get_tokens(serial=self.serials[0])
        hotp_tokenobject = tokenobject_list[0]
        hotp_tokenobject.token.count = count_1
        hotp_tokenobject.token.save()

        # test successful authentication
        with self.app.test_request_context('/validate/check',
                                           method='GET',
                                           query_string=urlencode(
                                                    {"user": "cornelius",
                                                    "pass": "pin287082"})):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = json.loads(res.data).get("result")
            self.assertTrue(result.get("status") is True, result)
            self.assertTrue(result.get("value") is True, result)

        # Check that the counter is increased!
        tokenobject_list = get_tokens(serial=self.serials[0])
        hotp_tokenobject = tokenobject_list[0]
        count_2 = hotp_tokenobject.token.count
        self.assertTrue(count_2 > count_1, (hotp_tokenobject.token.serial,
                                            hotp_tokenobject.token.count,
                                            count_1,
                                            count_2))

        # test authentication fails with the same OTP
        with self.app.test_request_context('/validate/check',
                                           method='GET',
                                           query_string=urlencode(
                                                    {"user": "cornelius",
                                                    "pass": "pin287082"})):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = json.loads(res.data).get("result")
            self.assertTrue(result.get("status") is True, result)
            self.assertTrue(result.get("value") is False, result)

    def test_04_check_serial(self):
        # test authentication successful with serial
        with self.app.test_request_context('/validate/check',
                                           method='POST',
                                           data={"serial": self.serials[0],
                                                 "pass": "pin969429"}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = json.loads(res.data).get("result")
            self.assertTrue(result.get("status") is True, result)
            self.assertTrue(result.get("value") is True, result)

        # test authentication fails with serial with same OTP
        with self.app.test_request_context('/validate/check',
                                           method='POST',
                                           data={"serial": self.serials[0],
                                                 "pass": "pin969429"}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = json.loads(res.data).get("result")
            self.assertTrue(result.get("status") is True, result)
            self.assertTrue(result.get("value") is False, result)

    def test_05_simple_check_user(self):
        # test successful authentication
        with self.app.test_request_context('/validate/simplecheck',
                                           method='POST',
                                           data={"user": "cornelius",
                                                 "pass": "pin338314"}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            self.assertTrue(res.data == ":-)", res.data)

        # test authentication fails with the same OTP
        with self.app.test_request_context('/validate/simplecheck',
                                           method='POST',
                                           data={"user": "cornelius",
                                                 "pass": "pin338314"}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            self.assertTrue(res.data == ":-(", res.data)

    def test_06_saml_check(self):
                # test successful authentication
        with self.app.test_request_context('/validate/samlcheck',
                                           method='POST',
                                           data={"user": "cornelius",
                                                 "pass": "pin338314"}):
            self.assertRaises(NotImplementedError,
                              self.app.full_dispatch_request)