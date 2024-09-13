#!/bin/bash

# utils 디렉토리의 파일 복사 함수
copy_utils() {
    src_dir="./utils"
    dest_dir="$1"

    # utils 디렉토리의 모든 파일을 대상 디렉토리로 복사
    cp -R "$src_dir/" "$dest_dir/"
}

# 각 함수 디렉토리에 utils 복사
copy_utils "functions/get_urls/"
copy_utils "functions/html_parsing/"
copy_utils "functions/create_batch/"
copy_utils "functions/check_embedding/"
copy_utils "functions/cancel_batch/"

# SAM 빌드 실행
sam build
