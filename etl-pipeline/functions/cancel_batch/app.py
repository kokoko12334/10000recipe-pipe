from openai import OpenAI, ConflictError
from utils.logutils import RecipeLogger
from utils.aws_ssm import SSMParameterStore

ssm = SSMParameterStore()
BUCKET_NAME = ssm.get_parameter("RECIPE_BUCKETNAME")
OPENAIKEY = ssm.get_parameter("OPENAIKEY")

recipe_logger = RecipeLogger(BUCKET_NAME)
openai_client = OpenAI(api_key=OPENAIKEY)

@recipe_logger.log_and_upload()
def lambda_handler(event, context):
    
    batch_id = event["batch_id"]
    try:
        openai_client.batches.cancel(batch_id)
    except ConflictError:
        pass

    BATCH_FILE = f'batch_files/batch_{recipe_logger.formatted_now}-{batch_id}.jsonl'
    recipe_logger.s3.delete_object(Bucket=BUCKET_NAME, Key=BATCH_FILE)
    recipe_logger.log_message("INFO", f'delete-batch-lambda: succeeded - Successfully delete batch:{batch_id}.')

    output = {
        "rcp_info": event['rcp_info']
    }
    
    return output
