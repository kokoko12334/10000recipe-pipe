from functions.get_urls import app

def test_get_urls():
    input_payload = {"test": 0}

    data = app.lambda_handler(input_payload, "")

    assert "state" in data
    assert "rcp_no_arr" in data