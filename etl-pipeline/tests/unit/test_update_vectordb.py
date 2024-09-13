from functions.update_vectordb import app

def test_create_batch():
    json_file_key = "recipe-json-files/20240913-batch_igGWfOYmhKcGVf7pYhHNPcku-recipe.json"
    input_payload = {
        "json_file_key": json_file_key,
        "test": 0
    }
    data = app.lambda_handler(input_payload, "")
    
    assert data["upserted_count"] == 5
