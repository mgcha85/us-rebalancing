import logging
import sys

def setup_logger(name: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    지정한 이름(name)의 Logger를 생성하여 콘솔 핸들러를 추가한 후 반환합니다.
    
    :param name: Logger 이름 (None이면 root logger 사용)
    :param level: 로그 레벨 (기본: INFO)
    :return: 설정된 Logger 객체
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 이미 핸들러가 추가되어 있다면 중복 추가 방지
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(name)s - %(message)s", 
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger

# 모듈 단독 실행 테스트
if __name__ == "__main__":
    log = setup_logger("test_logger")
    log.info("Logger가 정상적으로 설정되었습니다.")
