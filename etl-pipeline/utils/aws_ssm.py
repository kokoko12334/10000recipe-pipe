import boto3

class SSMParameterStore:
    def __init__(self):
        self.ssm = boto3.client('ssm')
    
    #Parameter Store에서 값을 가져옵니다.
    def get_parameter(self, name, with_decryption=True):
        
        response = self.ssm.get_parameter(
            Name=name,
            WithDecryption=with_decryption
        )
        return response['Parameter']['Value']
    
    #Parameter Store에 값을 저장합니다.
    def put_parameter(self, name, value, param_type='String', overwrite=True):
       response = self.ssm.put_parameter(
           Name=name,
           Value=value,
           Type=param_type,
           Overwrite=overwrite
       )
       return response
