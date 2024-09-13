import json
from pinecone import Pinecone
from utils.logutils import RecipeLogger
from utils.aws_ssm import SSMParameterStore

ssm = SSMParameterStore()
BUCKET_NAME = ssm.get_parameter("RECIPE_BUCKETNAME")
PINECONE_APIKEY = ssm.get_parameter("PINECONE_APIKEY")

recipe_logger = RecipeLogger(BUCKET_NAME)

@recipe_logger.log_and_upload()
def lambda_handler(event, context):

    if 'test' in event:
        INDEX_NAME = "dev-recipe-index"
    else:
        INDEX_NAME = "recipe-index"

    JSONFILE_KEY = event["json_file_key"]
    
    try:
        json_obj = recipe_logger.s3.get_object(Bucket=BUCKET_NAME, Key=JSONFILE_KEY)
        json_data = json_obj['Body'].read().decode('utf-8') 
        rcp_info = json.loads(json_data)

    except Exception as e:
        recipe_logger.log_message("ERROR", f"update-vectordb-lambda: fail - Failed to load to {JSONFILE_KEY}, error:{e}")
        raise e
    
    pc = Pinecone(api_key=PINECONE_APIKEY)
    index = pc.Index(INDEX_NAME)

    vectors = []
    for i in range(len(rcp_info)):
        vector = {
            "id": str(rcp_info[i]["rcp_no"]),
            "values": rcp_info[i]["vector"],
            "metadata":{
                "image_url": rcp_info[i]["img_url"],
                "ingre": str(rcp_info[i]["ingres"]),
                "name": rcp_info[i]["rcp_name"],
                "url": rcp_info[i]["url"],
            },
        }
        vectors.append(vector)
    try:
        result = index.upsert(vectors=vectors)
        recipe_logger.log_message("INFO", f"update-vectordb-lambda: succeeded - Successfully uploaded {result['upserted_count']} to {INDEX_NAME}.")
    except Exception as e:
        recipe_logger.log_message("ERROR", f"update-vectordb-lambda: fail - Failed to upload to {index}, error:{e}")
        raise e

    output = {
        "upserted_count" : result['upserted_count']
    }

    return output