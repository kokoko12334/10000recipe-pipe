import re
from marshmallow import Schema, fields, validates, ValidationError

def is_korean_or_english(text: str) -> bool:
    pattern = re.compile(r'^[가-힣a-zA-Z]+$')
    return bool(pattern.match(text))

def is_valid_url(url: str, contains: str) -> bool:
    return contains in url

def is_float_or_empty(value) -> bool:
    if value == "":
        return True
    try:
        float(value)
        return True
    except ValueError:
        return False

class RcpInfoSchema(Schema):
    rcp_name = fields.Str(required=True)
    url = fields.Str(required=True)
    img_url = fields.Str(required=True)
    ingres = fields.List(fields.Str(), required=True)
    vector = fields.List(fields.Float(), missing=[])

    @validates('rcp_name')
    def validate_rcp_name(self, value):
        if not is_korean_or_english(value):
            raise ValidationError(f"'{value}' must be Korean or English.")

    @validates('url')
    def validate_url(self, value):
        if not is_valid_url(value, "https://m.10000recipe.com/recipe"):
            raise ValidationError(f"URL '{value}' must contain 'https://m.10000recipe.com/recipe'.")

    @validates('img_url')
    def validate_img_url(self, value):
        if not is_valid_url(value, "https://recipe1.ezmember"):
            raise ValidationError(f"Image URL '{value}' must contain 'https://recipe1.ezmember'.")

    @validates('ingres')
    def validate_ingres(self, value):
        for item in value:
            if not is_korean_or_english(item):
                raise ValidationError(f"'{item}' in 'ingres' must be Korean or English.")

    @validates('vector')
    def validate_vector(self, value):
        if not all(is_float_or_empty(x) for x in value):
            raise ValidationError(f"All elements in 'vector' must be float or empty.")

class OutputSchema(Schema):
    state = fields.Str(required=True)
    rcp_no_arr = fields.List(fields.Integer(), required=True)
    rcp_info = fields.List(fields.Nested(RcpInfoSchema), required=True)

    @validates('rcp_no_arr')
    def validate_rcp_no_arr(self, value):
        if not all(isinstance(x, int) and x > 0 for x in value):
            raise ValidationError(f"All elements in 'rcp_no_arr' must be positive integers.")