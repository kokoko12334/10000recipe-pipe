import json
import pickle
import io
from openai import OpenAI
from utils.logutils import RecipeLogger
from botocore.exceptions import ClientError
from utils.aws_ssm import SSMParameterStore

ssm = SSMParameterStore()
BUCKET_NAME = ssm.get_parameter("RECIPE_BUCKETNAME")
OPENAIKEY = ssm.get_parameter("OPENAIKEY")

recipe_logger = RecipeLogger(BUCKET_NAME)
openai_client = OpenAI(api_key=OPENAIKEY)

@recipe_logger.log_and_upload()
def lambda_handler(event, context):

    if 'test' in event:
        INGRE_VECTOR = 'ingre_vector2_dev.pk'
    else:
        INGRE_VECTOR = 'ingre_vector2.pk'

    rcp_info = event["rcp_info"]
    
    model = "text-embedding-3-small"
    recipe_logger.s3.head_object(Bucket=BUCKET_NAME, Key=INGRE_VECTOR)
    response = recipe_logger.s3.get_object(Bucket=BUCKET_NAME, Key=INGRE_VECTOR)
    ingre_vector = pickle.loads(response['Body'].read())

    ingres_set = set()
    for rcp in rcp_info:
        for ingre in rcp['ingres']:
            if ingre not in ingre_vector:
                ingres_set.add(ingre)

    data = []
    for ingredient in ingres_set: 
        json_data = {
            "custom_id": f"{ingredient}", 
            "method": "POST", 
            "url": "/v1/embeddings", 
            "body": {
                "input": ingredient,
                "model": model,
                "encoding_format": "float"
            }
        }
        data.append(json_data)

    batch_id = ""
    state = False

    if data:
        state = True
        try:
            with io.BytesIO() as byte_stream:

                # JSON Lines 데이터를 문자열로 변환하고 UTF-8로 인코딩하여 BytesIO에 작성
                json_lines = "\n".join(json.dumps(entry, ensure_ascii=False) for entry in data)
                byte_stream.write(json_lines.encode('utf-8'))

                # # BytesIO 객체의 내용을 S3에 업로드
                byte_stream.seek(0)  # 파일 포인터를 처음으로 이동
                batch_input_file = openai_client.files.create(
                    file=byte_stream,
                    purpose="batch"
                )

                batch = openai_client.batches.create(
                    input_file_id=batch_input_file.id,
                    endpoint="/v1/embeddings",
                    completion_window="24h",
                    metadata={
                      "description": "FCKU"
                    }
                )
                batch_id = batch.id
                recipe_logger.log_message("INFO", f'create-batch-lambda: succeeded - Successfully request batch:{batch_id}.')
                BATCH_FILE = f'batch_files/batch_{recipe_logger.formatted_now}-{batch_id}.jsonl'

                # BytesIO 객체의 내용을 S3에 업로드
                byte_stream.seek(0)  # 파일 포인터를 처음으로 이동
                recipe_logger.s3.upload_fileobj(byte_stream, BUCKET_NAME, BATCH_FILE)
                recipe_logger.log_message("INFO", f'create-batch-lambda: succeeded - Successfully uploaded {BATCH_FILE} to bucket {BUCKET_NAME}.')

        except ClientError as e:
            recipe_logger.log_message("ERROR", f'create-batch-lambda: Failed to upload {BATCH_FILE} to bucket {BUCKET_NAME}. Error: {e}')
            
    output = {
        "state": state,
        "batch_id":batch_id,
        "rcp_info":rcp_info
    }

    return output
