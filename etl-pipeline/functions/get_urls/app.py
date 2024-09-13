import requests
from bs4 import BeautifulSoup
from bisect import bisect_left
from utils.logutils import RecipeLogger
from utils.validation import OutputSchema, ValidationError
from utils.aws_ssm import SSMParameterStore


ssm = SSMParameterStore()
BUCKET_NAME = ssm.get_parameter("RECIPE_BUCKETNAME")
recipe_logger = RecipeLogger(BUCKET_NAME)
schema = OutputSchema()

@recipe_logger.log_and_upload()
def lambda_handler(event, context):

    if "test" in event:
        latest_rcp_no = int(ssm.get_parameter("LATEST_RCPNO_DEV"))
    else:
        latest_rcp_no = int(ssm.get_parameter("LATEST_RCPNO_PRO"))

    recipe_logger.log_message("INFO", f"get_urls_lambda: latest_rcp_no:{latest_rcp_no}")

    rcp_no_arr = []
    for page_num in range(1,10):
        url = f"https://m.10000recipe.com/recipe/list.html?order=date&page={page_num}"
        res = requests.get(url)
        soup = BeautifulSoup(res.content, 'html.parser')
        recipe_list_tag = soup.find('div', class_='recipe_list')
        for media_tag in recipe_list_tag.findAll('div', class_='media'):
            onclick = media_tag['onclick']
            if onclick:
                rcp_no: str = onclick.split("/")[-1][:-1]
                if rcp_no.isdigit():
                    rcp_no_arr.append(int(rcp_no))
    
    rcp_no_arr = rcp_no_arr[::-1]    
    idx = bisect_left(rcp_no_arr, latest_rcp_no)
    rcp_no_arr = rcp_no_arr[idx+1:]
    
    state = False
    if rcp_no_arr:
        state = True
        
    recipe_logger.log_message("INFO", f"get_urls_lambda: {{state:{state}, length:{len(rcp_no_arr)}}}")

    output = {
        "state": state,
        "rcp_no_arr": rcp_no_arr
    }

    try:
        schema.validate(output)
        recipe_logger.log_message("INFO", f"get_urls_lambda: succeeded - urls successfully validated")
        if state:
            if "test" in event:
                ssm.put_parameter("LATEST_RCPNO_DEV", str(rcp_no_arr[-1]))
            else:
                ssm.put_parameter("LATEST_RCPNO_PRO", str(rcp_no_arr[-1]))

    except ValidationError as e:
        recipe_logger.log_message("ERROR", e)
        raise ValidationError(e)

    return output


