from functions.create_batch import app as create_app
from functions.cancel_batch import app as cancel_app
import pytest
import json

@pytest.fixture
def load_test_data():
    with open("./etl-pipeline/tests/unit/rcpinfo_testdata.json", "r", encoding="utf-8") as file:
        test_data = json.load(file)
    return test_data["rcp_info"]

def test_create_batch(load_test_data):
    test_data = load_test_data
    input_payload = {
        "rcp_info": test_data,
        "test": 0
    }

    batch_id = create_app.lambda_handler(input_payload, "")["batch_id"]
    input_payload['batch_id'] = batch_id
    data = cancel_app.lambda_handler(input_payload, "")

    assert "rcp_info" in data