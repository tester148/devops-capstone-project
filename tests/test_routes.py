"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_get_account(self):
        """Should successfully fetch one account"""
        sample_entry = self._create_accounts(1)[0]
        response = self.client.get(
            f"{BASE_URL}/{sample_entry.id}", content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_result = response.get_json()
        self.assertEqual(json_result["name"], sample_entry.name)

    def test_get_account_not_found(self):
        """Should return 404 when account is not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_account_list(self):
        """Should retrieve list of all existing accounts"""
        self._create_accounts(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        account_list = response.get_json()
        self.assertEqual(len(account_list), 5)

    def test_get_account_list_not_found(self):
        """Should return 200 and an empty array when no accounts exist"""
        self._create_accounts(0)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.get_json()
        self.assertEqual(len(results), 0)

    def test_update_account(self):
        """Should modify an existing account's attributes"""
        generated = AccountFactory()
        creation_response = self.client.post(BASE_URL, json=generated.serialize())
        self.assertEqual(creation_response.status_code, status.HTTP_201_CREATED)

        created_entry = creation_response.get_json()
        created_entry["name"] = "something bad"

        update_response = self.client.put(f"{BASE_URL}/{created_entry['id']}", json=created_entry)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        updated_entry = update_response.get_json()
        self.assertEqual(updated_entry["name"], "something bad")

    def test_delete_account(self):
        """Should remove the account from the database"""
        entry_to_delete = self._create_accounts(1)[0]
        deletion = self.client.delete(f"{BASE_URL}/{entry_to_delete.id}")
        self.assertEqual(deletion.status_code, status.HTTP_204_NO_CONTENT)

    def test_method_not_allowed(self):
        """Should respond with 405 for invalid HTTP method usage"""
        invalid_call = self.client.delete(BASE_URL)
        self.assertEqual(invalid_call.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_security_headers(self):
        """Should include all required security headers"""
        secure_request = self.client.get('/')
        self.assertEqual(secure_request.status_code, status.HTTP_200_OK)

    def test_cors_security(self):
        """Should send back CORS policy headers"""
        cors_check = self.client.get('/')
        self.assertEqual(cors_check.status_code, status.HTTP_200_OK)
