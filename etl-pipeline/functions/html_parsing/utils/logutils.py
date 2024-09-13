import logging
import boto3
import pytz
from botocore.exceptions import ClientError
from datetime import datetime
from io import StringIO
from functools import wraps

class KoreanTimeFormatter(logging.Formatter):
    # 시간 포맷을 한국 시간으로 설정
    def formatTime(self, record, fmt=None):
        # 시간을 한국 시간으로 변환
        utc_time = datetime.fromtimestamp(record.created, pytz.utc)
        korea_time = utc_time.astimezone(pytz.timezone('Asia/Seoul'))
        return korea_time.strftime('%Y-%m-%d %H:%M:%S')  # 기본 포맷 사용
    

class RecipeLogger:
    def __init__(self, bucket_name: str):
        utc_now = datetime.now(pytz.utc)
        korea_tz = pytz.timezone('Asia/Seoul')
        korea_now = utc_now.astimezone(korea_tz)
        formatted_now = korea_now.strftime("%Y%m%d")
        
        self.log_buffer = StringIO()

        # 로깅 핸들러를 직접 설정
        handler = logging.StreamHandler(self.log_buffer)
        handler.setLevel(logging.INFO)

        # 커스텀 포맷터 사용
        formatter = KoreanTimeFormatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.logger = logging.getLogger('DartLogger')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # 기존 핸들러 제거 (필요시)
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        self.logger.addHandler(handler)
        
        # 로그 파일 이름 설정
        self.log_file_name = f'recipe-stepfunction-{formatted_now}_log.txt'
        self.LOGFILE_KEY = f'recipe-stepfunction-logs/{self.log_file_name}'
        self.BUCKET_NAME = bucket_name
        
        # S3 클라이언트 설정
        self.s3 = boto3.client('s3')

    # 버퍼리셋 메소드
    def reset_log_buffer(self):
        self.log_buffer.truncate(0)
        self.log_buffer.seek(0)

    #로그메시지 기록 메소드
    def log_message(self, level: str, message: str):
        if level == 'ERROR':
            self.logger.error(message)
        elif level == 'INFO':
            self.logger.info(message)
        else:
            self.logger.debug(message)
    
    # s3에 로그파일 저장 메소드
    def put_log(self):
        try:
            response = self.s3.get_object(Bucket=self.BUCKET_NAME, Key=self.LOGFILE_KEY)
            existing_log_content = response['Body'].read().decode('utf-8')
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                existing_log_content = ""
                self.log_message('ERROR', f"Unexpected error: {e}")
            else:
                existing_log_content = ""
        
        # 로그 버퍼의 내용 읽기
        new_log_content = self.log_buffer.getvalue()
        
        # 새로운 로그를 기존 로그에 추가
        updated_log_content = existing_log_content + new_log_content
        
        # 버퍼를 초기화
        self.reset_log_buffer()
        
        # S3에 업데이트된 로그 파일 저장
        self.s3.put_object(Bucket=self.BUCKET_NAME, Key=self.LOGFILE_KEY, Body=updated_log_content.encode('utf-8'))

    # 메인 로직에 추가하는 데코레이터
    def log_and_upload(self):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                self.reset_log_buffer()
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    self.log_message('ERROR', f"failed with error: {e}")
                    raise e
                finally:
                    self.put_log()
                return result
            return wrapper
        return decorator
