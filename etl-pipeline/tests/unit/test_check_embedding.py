from functions.check_embedding import app

def test_get_urls():
    input_payload = {"batch_id": "batch_lx1vDv9YWDeqCEsF8ssExqSz"}

    data = app.lambda_handler(input_payload, "")

    assert "state" in data