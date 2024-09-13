from functions.trans_vector import app
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
        "batch_id": "batch_igGWfOYmhKcGVf7pYhHNPcku"
    }
    data = app.lambda_handler(input_payload, "")
    
    assert data["state"] == "completed"
    assert "json_file_key" in data