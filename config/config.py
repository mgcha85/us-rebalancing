import os
import yaml

# 기본 설정 (config.yaml 파일이 없거나 일부 값이 누락된 경우에 대비)
DEFAULT_CONFIG = {
    "stocks": {
        "TSLA": 0.2,
        "JPM": 0.2,
        "JNJ": 0.2,
        "PG": 0.2,
        "PLTR": 0.2
    }
}

def load_config(config_file: str = "config.yaml") -> dict:
    """
    config.yaml 파일을 로드하여, 기본 설정(DEFAULT_CONFIG)과 병합한 후 반환합니다.
    
    :param config_file: 설정 파일 경로 (기본값: "config.yaml")
    :return: 설정 dict
    """
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f)
        if user_config:
            # 상위 키가 딕셔너리인 경우 기본값과 병합 (예: stocks)
            for key, value in user_config.items():
                if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                    config[key].update(value)
                else:
                    config[key] = value
    return config

# 모듈 단독 실행 테스트
if __name__ == "__main__":
    cfg = load_config()
    print("Loaded configuration:")
    print(cfg)
