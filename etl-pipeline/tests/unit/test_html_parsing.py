from functions.html_parsing import app
import pytest
import json

@pytest.fixture
def load_test_data():
    with open("./etl-pipeline/tests/unit/rcpinfo_testdata.json", "r", encoding="utf-8") as file:
        test_data = json.load(file)
    return test_data["rcp_info"]

def test_html_parsing(load_test_data):
    test_data = load_test_data
    input_payload = {
    "rcp_no_arr": [7033006, 7033041, 7033042, 7033043, 7033044]
    }
    data = app.lambda_handler(input_payload, "")["rcp_info"]

    for i in range(len(data)):
        assert data[i]["rcp_name"] == test_data[i]["rcp_name"]
        assert data[i]["rcp_no"] == test_data[i]["rcp_no"]
        assert data[i]["url"] == test_data[i]["url"]
        assert data[i]["img_url"] == test_data[i]["img_url"]
        assert data[i]["ingres"] == test_data[i]["ingres"]