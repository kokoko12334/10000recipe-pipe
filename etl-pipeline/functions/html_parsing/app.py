import requests
import re
import requests
from bs4 import BeautifulSoup
from utils.validation import OutputSchema, ValidationError
from utils.logutils import RecipeLogger
from utils.aws_ssm import SSMParameterStore

ssm = SSMParameterStore()
BUCKET_NAME = ssm.get_parameter("RECIPE_BUCKETNAME")
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.3904.108 Safari/537.36'

recipe_logger = RecipeLogger(BUCKET_NAME)
schema = OutputSchema()

@recipe_logger.log_and_upload()
def lambda_handler(event, context):
    rcp_no_arr = event['rcp_no_arr']
    rcp_info = []

    for i in range(len(rcp_no_arr)):
        rcp_no = rcp_no_arr[i]
        url = f"https://m.10000recipe.com/recipe/{rcp_no}"
        response = requests.get(url, headers={'User-Agent': USER_AGENT})
            
        try:
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')

            if "레시피 정보가 없습니다." in str(soup.contents[0]):
                recipe_logger.log_message("ERROR", f"html-parsing-lambda: Failed data: {rcp_no}, error: NoRecipe")
                continue

            image_url = ""
            img_div = soup.find('div', class_='view3_pic_img')
            if img_div:
                image_url = img_div.find('img')['src']

            rcp_name = ""
            title_div = soup.find('div', class_='view3_top_tit')
            if title_div:
                rcp_name = title_div.contents[0]

            ingres = ""
            ingre_tag = soup.find('dl', class_='view3_ingre')
            if ingre_tag:
                ul_tag = soup.find('ul', class_='ingre_list')
                ingres_arr = []
                if not ul_tag:
                    dl_tag = soup.find('dl', class_='view3_ingre')
                    if dl_tag:
                        ingres = dl_tag.find('dd').contents[0]
                        for ingre in ingres.split(","):
                            validate_ingre = re.sub(r'\d+.*', '', ingre).strip()
                            ingres_arr.append(validate_ingre)        
                else:
                    for li_tag in ul_tag.find_all('li'):
                        ingre = ""
                        a_tag = li_tag.find('div', class_='ingre_list_name').find('a')
                        if a_tag:
                            ingre = a_tag.get_text(strip=True)
                        else:
                            ingre = li_tag.find('div', class_='ingre_list_name').get_text(strip=True)

                        validate_ingre = re.sub(r'\d+.*', '', ingre).strip()
                        ingres_arr.append(validate_ingre)

            recipe = {
                "rcp_name":rcp_name, 
                "rcp_no":rcp_no,
                "url":url,
                "img_url":image_url, 
                "ingres":ingres_arr,
                "vector":[] 
            }
            rcp_info.append(recipe)

        except ValidationError as e:
            recipe_logger.log_message("ERROR", f"html-parsing-lambda: Parsing Failed data: {rcp_no}, error:{e}")
            raise ValidationError(e)
        except Exception as e:
            recipe_logger.log_message("ERROR", f"html-parsing-lambda: Parsing Failed data: {rcp_no}, error:{e}")
            raise Exception(e)

    recipe_logger.log_message("INFO", f"html-parsing-lambda: succeeded - {len(rcp_info)} items parsed successfully.")

    output = {
        "rcp_info": rcp_info
    }

    try:
        schema.validate(output)
        recipe_logger.log_message("INFO", f"html-parsing-lambda: succeeded - {len(rcp_info)} successfully validated")
    except ValidationError as e:
        recipe_logger.log_message("ERROR", e)
        raise ValidationError(e)
    
    return output