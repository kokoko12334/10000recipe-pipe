import os
import subprocess
import json
#람다작성 -> 테스트코드 -> build.sh 작성 -> 템플릿 추가 -> 상태머신작성
def get_session_token(mfa_serial, token_code):
    try:
        # AWS CLI 명령을 구성합니다.
        command = [
            "aws", "sts", "get-session-token",
            "--serial-number", mfa_serial,
            "--token-code", token_code
        ]

        # subprocess를 사용해 명령어 실행
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # JSON 결과를 파싱
        session_info = json.loads(result.stdout)
        return session_info

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr}")
        return None

if __name__ == "__main__":
    # 사용자로부터 입력 받기
    mfa_serial = input("MFA 기기 ARN을 입력하세요: ")
    token_code = input("MFA 기기에서 생성된 코드를 입력하세요: ")

    # 세션 토큰 요청
    session_info = get_session_token(mfa_serial, token_code)

    if session_info:
        print("세션 토큰 정보를 성공적으로 가져왔습니다.")
        print(json.dumps(session_info, indent=4))

        # 세션 토큰 정보에서 필요한 값 추출
        access_key = session_info["Credentials"]["AccessKeyId"]
        secret_key = session_info["Credentials"]["SecretAccessKey"]
        session_token = session_info["Credentials"]["SessionToken"]

        # ~ / .aws / credentials에 저장하는 과정
        from configparser import ConfigParser

        credentials_file = os.path.expanduser("~/.aws/credentials")
        config = ConfigParser()
        config.read(credentials_file)

        # 'temporary' 섹션이 없으면 생성
        if "temporary" not in config:
            config["temporary"] = {}

        # 자격 증명 저장
        config["temporary"]["aws_access_key_id"] = access_key
        config["temporary"]["aws_secret_access_key"] = secret_key
        config["temporary"]["aws_session_token"] = session_token

        # 업데이트된 파일로 저장
        with open(credentials_file, 'w') as configfile:
            config.write(configfile)

        print("AWS credentials updated successfully.")