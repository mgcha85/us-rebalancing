import logging
from config.config import load_config
from services.order_service import OrderService
from services.quotation_service import QuotationService
from strategies.rebalancing import RebalancingStrategy
from utils.logger import setup_logger

def main():
    # 로깅 설정
    logger = setup_logger("main", level=logging.INFO)
    logger.info("프로젝트 시작")

    # 설정 파일 로드 (config.yaml)
    config = load_config()
    logger.info("설정 로드 완료: %s", config)

    # API 관련 기본 정보 (실제 값은 문서를 참고하여 수정하세요)
    base_url = "https://apiportal.koreainvestment.com/apiservice"
    token = "DUMMY_APPROVAL_KEY"       # 실제 API 승인 키 또는 토큰으로 교체
    account_id = "YOUR_ACCOUNT_ID"       # 실제 계좌 번호로 교체

    # 서비스 인스턴스 생성
    order_service = OrderService(base_url, token, account_id)
    quotation_service = QuotationService(base_url, token)

    # 전체 투자 금액 설정 (예: 1,000,000)
    portfolio_value = 1000000

    # 리밸런싱 전략 인스턴스 생성
    strategy = RebalancingStrategy(config, order_service, quotation_service, portfolio_value)
    
    logger.info("리밸런싱 전략 실행 시작...")
    results = strategy.execute()
    logger.info("리밸런싱 전략 실행 완료.")

    # 각 종목별 주문 결과 출력
    for symbol, response in results.items():
        logger.info("종목: %s, 주문 결과: %s", symbol, response)

if __name__ == "__main__":
    main()
