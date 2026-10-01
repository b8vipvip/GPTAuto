import unittest

from gptauto.ci_policy import is_transient_failure


class CiPolicyTests(unittest.TestCase):
    def test_transient_network_failure_gets_one_retry(self):
        self.assertTrue(is_transient_failure("download failed: ECONNRESET", conclusion="failure", run_attempt=1))

    def test_second_attempt_never_retries_again(self):
        self.assertFalse(is_transient_failure("ECONNRESET", conclusion="failure", run_attempt=2))

    def test_product_test_failure_is_not_transient(self):
        self.assertFalse(is_transient_failure("AssertionError: expected 3 got 4", conclusion="failure", run_attempt=1))

    def test_startup_failure_is_retryable_once(self):
        self.assertTrue(is_transient_failure("", conclusion="startup_failure", run_attempt=1))


if __name__ == "__main__":
    unittest.main()
