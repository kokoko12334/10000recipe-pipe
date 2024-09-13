import json
import pickle
import io
import numpy as np
from typing import List
from openai import OpenAI
from utils.logutils import RecipeLogger
from utils.validation import OutputSchema, ValidationError
from utils.aws_ssm import SSMParameterStore

ssm = SSMParameterStore()
BUCKET_NAME = ssm.get_parameter("RECIPE_BUCKETNAME")
OPENAIKEY = ssm.get_parameter("OPENAIKEY")
INGRE_VECTOR = 'ingre_vector2.pk'

recipe_logger = RecipeLogger(BUCKET_NAME)
openai_client = OpenAI(api_key=OPENAIKEY)
schema = OutputSchema()

recipe_logger.s3.head_object(Bucket=BUCKET_NAME, Key=INGRE_VECTOR)
response = recipe_logger.s3.get_object(Bucket=BUCKET_NAME, Key=INGRE_VECTOR)
ingre_vector = pickle.loads(response['Body'].read())

def cal_recipe_vector(ingre: List[str], weight: List[float]) -> List[float]:
  
    n = len(ingre)
    weight_sum = sum(weight)
    weight_adj = [round(w / weight_sum, 4) for w in weight]
    matrix = np.zeros((n,1536))
    for i in range(n):
        v = ingre_vector[ingre[i]] * weight_adj[i]
        matrix[i] = v
    recipe_vector = matrix.sum(axis=0)/n
    return [float(x) for x in recipe_vector]

@recipe_logger.log_and_upload()
def lambda_handler(event, context):
    
    batch_id = event['batch_id']
    rcp_info = event['rcp_info']
    
    if batch_id:
        file_id = openai_client.batches.retrieve(batch_id).output_file_id

        file_response = openai_client.files.content(file_id)

        result = file_response.text
        lines = result.splitlines()

        data_list = []
        for line in lines:
            if line.strip():
                try:
                    data = json.loads(line)
                    ingredient = data['custom_id']
                    embedding = data['response']['body']['data'][0]['embedding']
                    data_list.append((ingredient, embedding))
                except json.JSONDecodeError as e:
                    recipe_logger.log_message("ERROR", f'trans-embedding-vector-lambda: fail - Failed to JSON parsing {line}, error:{e}.')
                    raise e

        for i in range(len(data_list)):
            ingredient, embedding = data_list[i]
            ingre_vector[ingredient] = np.array(embedding)

        with io.BytesIO() as byte_stream:

            pickle.dump(ingre_vector, byte_stream)
            # S3에 파일 업로드  
            try:
                byte_stream.seek(0)
                recipe_logger.s3.upload_fileobj(byte_stream, BUCKET_NAME, INGRE_VECTOR)
                recipe_logger.log_message("INFO", f'trans-embedding-vector-lambda: succeeded - Successfully uploaded {INGRE_VECTOR} to {BUCKET_NAME}.')
            except Exception as e:
                recipe_logger.log_message("ERROR", f'trans-embedding-vector-lambda: fail - Failed to upload {INGRE_VECTOR} to {BUCKET_NAME}, error:{e}.')
                raise e
        
    for rcp in rcp_info:
        ingres = rcp['ingres']
        weight = [1] * len(ingres)
        v = cal_recipe_vector(ingres, weight)
        rcp['vector'] = v

    JSONFILE_KEY = f'recipe-json-files/{recipe_logger.formatted_now}-{batch_id}-recipe.json'
    with io.BytesIO() as json_buffer:
        json_buffer.write(json.dumps(rcp_info, ensure_ascii=False).encode('utf-8'))

        try:
            json_buffer.seek(0)
            recipe_logger.s3.upload_fileobj(json_buffer, BUCKET_NAME, JSONFILE_KEY)
            recipe_logger.log_message("INFO", f'trans-embedding-vector-lambda: succeeded - Successfully uploaded {JSONFILE_KEY} to {BUCKET_NAME}.')
        except Exception as e:
            recipe_logger.log_message("ERROR", f'trans-embedding-vector-lambda: fail - Failed to upload {JSONFILE_KEY} to {BUCKET_NAME}, error:{e}.')
            raise e
        
    output = {
        "state": "completed",
        "json_file_key": JSONFILE_KEY
    }

    try:
        schema.validate(output)
        recipe_logger.log_message("INFO", f"trans-embedding-vector-lambda: succeeded - {len(rcp_info)} successfully validated")
    except ValidationError as e:
        recipe_logger.log_message("ERROR", e)
        raise ValidationError(e)
    
    return output

