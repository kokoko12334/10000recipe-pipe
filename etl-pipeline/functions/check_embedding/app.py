from openai import OpenAI
from utils.logutils import RecipeLogger
from utils.aws_ssm import SSMParameterStore

ssm = SSMParameterStore()
BUCKET_NAME = ssm.get_parameter("RECIPE_BUCKETNAME")
OPENAIKEY = ssm.get_parameter("OPENAIKEY")

recipe_logger = RecipeLogger(BUCKET_NAME)
openai_client = OpenAI(api_key=OPENAIKEY)

@recipe_logger.log_and_upload()
def lambda_handler(event, context):
    
    batch_id = event['batch_id']
    state = False

    if openai_client.batches.retrieve(batch_id).status == 'completed':
        state = True
        recipe_logger.log_message("INFO", f"check-embedding-done-lambda: succeeded - Successfully batch file embedded: {batch_id} ")
    
    event["state"] = state
    return event
