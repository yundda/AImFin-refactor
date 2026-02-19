import os

INPUT_FILE = 'data.json'
OUTPUT_FILE = 'data_utf8.json'

def convert_encoding():
    try:
        # CP949 (Windows Korean)로 읽기 시도
        with open(INPUT_FILE, 'r', encoding='cp949') as f:
            content = f.read()
        
        # UTF-8로 쓰기
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Successfully converted {INPUT_FILE} to {OUTPUT_FILE} (CP949 -> UTF-8)")
    except Exception as e:
        print(f"Failed to convert with CP949: {e}")
        # 실패 시 Latin-1 시도 (바이너리 덤프일 경우)
        try:
            with open(INPUT_FILE, 'r', encoding='latin-1') as f:
                content = f.read()
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Successfully converted {INPUT_FILE} to {OUTPUT_FILE} (Latin-1 -> UTF-8)")
        except Exception as e2:
             print(f"Failed to convert with Latin-1: {e2}")

if __name__ == "__main__":
    convert_encoding()
