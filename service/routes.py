"""
Account Service

This microservice handles the lifecycle of Accounts
"""
# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            # paths=url_for("list_accounts", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based the data in the body that is posted
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()
    # Uncomment once get_accounts has been implemented
    # location_url = url_for("get_accounts", account_id=account.id, _external=True)
    location_url = "/"  # Remove once get_accounts has been implemented
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )
######################################################################
# LIST ALL ACCOUNTS
######################################################################

@app.route("/accounts", methods=["GET"])
def list_accounts():
    """
    Fetch a list of all accounts
    This route handles the retrieval of every account in the system.
    """
    app.logger.info("Fetching all account records")
    all_accounts = Account.all()
    results = [item.serialize() for item in all_accounts]
    app.logger.info("Found [%s] total accounts", len(results))
    return jsonify(results), status.HTTP_200_OK


######################################################################
# READ AN ACCOUNT
######################################################################

@app.route("/accounts/<int:account_id>", methods=["GET"])
def get_accounts(account_id):
    """
    Retrieve a specific account by ID
    This route fetches a single account given its unique ID.
    """
    app.logger.info("Fetching account with ID: %s", account_id)

    result = Account.find(account_id)
    if not result:
        abort(status.HTTP_404_NOT_FOUND, f"Account with id [{account_id}] not located.")
    
    return result.serialize(), status.HTTP_200_OK


######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################

@app.route("/accounts/<int:account_id>", methods=["PUT"])
def update_account(account_id):
    """
    Modify an account
    This endpoint receives new account data and updates the existing one.
    """
    app.logger.info("Processing update for account ID: %s", account_id)

    existing = Account.find(account_id)
    if not existing:
        abort(status.HTTP_404_NOT_FOUND, f"Account with id [{account_id}] not found for update")
    
    existing.deserialize(request.get_json())
    existing.update()

    return existing.serialize(), status.HTTP_200_OK


######################################################################
# DELETE AN ACCOUNT
######################################################################

@app.route("/accounts/<int:account_id>", methods=["DELETE"])
def delete_accounts(account_id):
    """
    Remove an account
    Deletes an account corresponding to the provided account ID.
    """
    app.logger.info("Attempting deletion of account ID: %s", account_id)

    target = Account.find(account_id)
    if target:
        target.delete()
    return "", status.HTTP_204_NO_CONTENT


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################

def check_content_type(media_type):
    """Validates the request's content type header"""
    header_type = request.headers.get("Content-Type")
    if header_type and header_type == media_type:
        return
    app.logger.error("Received invalid Content-Type: %s", header_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )
