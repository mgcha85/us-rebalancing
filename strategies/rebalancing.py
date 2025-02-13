import math
import logging

class RebalancingStrategy:
    """
    리밸런싱 전략:
      - 전체 포트폴리오 투자금액(portfolio_value)에 대해, config에 정의된 각 종목의 목표 비중에 맞게
        각 종목별 목표 투자금액을 산출합니다.
      - 해외주식 시세 조회 API(quotation_service)를 사용해 현재가를 받아오고,
        목표 투자금액을 현재가로 나눈 후 내림(floor)하여 주문 수량을 계산합니다.
      - 계산된 주문 수량이 0보다 크면, 해외주식 주문 API(order_service)를 통해 시장가 주문을 실행합니다.
    """
    def __init__(self, config: dict, order_service, quotation_service, portfolio_value: float):
        """
        :param config: config.yaml에서 로드한 설정 dict (예: {'stocks': {'TSLA': 0.2, 'JPM': 0.2, ...}})
        :param order_service: 해외주식 주문 API 서비스를 제공하는 인스턴스 (services/order_service.py)
        :param quotation_service: 해외주식 시세 조회 API 서비스를 제공하는 인스턴스 (services/quotation_service.py)
        :param portfolio_value: 전체 포트폴리오 투자금액 (예: 1,000,000)
        """
        self.config = config
        self.order_service = order_service
        self.quotation_service = quotation_service
        self.portfolio_value = portfolio_value
        self.logger = logging.getLogger(__name__)
        if not self.logger.hasHandlers():
            logging.basicConfig(level=logging.INFO)

    def calculate_orders(self) -> dict:
        """
        각 종목별 목표 투자금액과 현재 시세를 기반으로 주문할 수량을 산출합니다.
        
        계산 공식:
            target_quantity = floor((portfolio_value * weight) / current_price)
        
        :return: {종목코드: 주문수량, ...}
        """
        orders = {}
        stocks_config = self.config.get("stocks", {})
        for symbol, weight in stocks_config.items():
            target_investment = self.portfolio_value * weight
            # 시세 조회 API 호출
            quote = self.quotation_service.get_quote(symbol)
            try:
                # 응답 JSON에 'price' 키가 현재가를 담고 있다고 가정합니다.
                price = float(quote.get("price", 0))
            except (ValueError, TypeError) as e:
                self.logger.error(f"가격 데이터 오류 for {symbol}: {quote.get('price')} ({e})")
                continue

            if price <= 0:
                self.logger.error(f"{symbol}의 가격이 유효하지 않습니다: {price}")
                continue

            quantity = math.floor(target_investment / price)
            if quantity > 0:
                orders[symbol] = quantity
                self.logger.info(
                    f"[{symbol}] 목표 투자금액: ${target_investment:.2f}, 현재가: ${price:.2f}, 주문수량: {quantity}"
                )
            else:
                self.logger.info(f"[{symbol}] 주문 수량이 0입니다. (목표 투자금액 ${target_investment:.2f} / 가격 ${price:.2f})")
        return orders

    def execute(self) -> dict:
        """
        리밸런싱 전략 실행:
          - calculate_orders()를 통해 산출된 주문 수량에 대해, 시장가 주문을 실행합니다.
        
        :return: {종목코드: API 주문 응답, ...}
        """
        orders_to_place = self.calculate_orders()
        results = {}
        for symbol, quantity in orders_to_place.items():
            self.logger.info(f"시장가 주문 실행: {symbol}, 수량 {quantity}")
            # 주문 서비스의 place_order()를 통해 주문 실행 (order_type은 "market"으로 지정)
            order_response = self.order_service.place_order(symbol, order_type="market", quantity=quantity)
            results[symbol] = order_response
            self.logger.info(f"{symbol} 주문 결과: {order_response}")
        return results

# 만약 이 모듈을 단독으로 실행한다면, 아래와 같이 간단한 테스트를 할 수 있습니다.
if __name__ == "__main__":
    # 예시: config는 직접 딕셔너리로 정의 (실제 사용 시 config 모듈을 통해 로드)
    example_config = {
        "stocks": {
            "TSLA": 0.2,
            "JPM": 0.2,
            "JNJ": 0.2,
            "PG": 0.2,
            "PLTR": 0.2
        }
    }
    # 주문/시세 서비스 인스턴스는 실제 API 호출 모듈을 사용하여 생성해야 합니다.
    # 여기서는 목업(mock) 예시로 간단한 람다 함수를 사용합니다.
    mock_order_service = type("MockOrderService", (), {
        "place_order": lambda self, symbol, order_type, quantity, price=None: {"symbol": symbol, "order_type": order_type, "quantity": quantity, "status": "success"}
    })()
    mock_quotation_service = type("MockQuotationService", (), {
        "get_quote": lambda self, symbol: {"price": "100"}  # 모든 종목의 현재가를 $100으로 가정
    })()

    portfolio_value = 1000000  # 예: 1,000,000 달러 투자
    strategy = RebalancingStrategy(example_config, mock_order_service, mock_quotation_service, portfolio_value)
    order_results = strategy.execute()
    print("주문 결과:", order_results)
