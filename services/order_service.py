import requests

class OrderService:
    """
    해외주식 주문 API 연동 모듈.
    참고: https://apiportal.koreainvestment.com/apiservice/apiservice-oversea-stock-order
    """
    def __init__(self, base_url: str, token: str, account_id: str):
        """
        :param base_url: API 기본 URL (예: "https://apiportal.koreainvestment.com/apiservice")
        :param token: API 접근 토큰(또는 approval_key)
        :param account_id: 주문에 사용할 계좌 번호
        """
        self.base_url = base_url
        self.token = token
        self.account_id = account_id

    def place_order(self, symbol: str, order_type: str, quantity: int, price: float = None) -> dict:
        """
        해외 주식 주문 실행 함수.
        
        :param symbol: 종목 코드 (예: TSLA)
        :param order_type: 주문 유형 ("market" 또는 "limit")
        :param quantity: 주문 수량
        :param price: 지정가 주문 시 단가 (order_type이 "limit"인 경우 필수)
        :return: API 응답 JSON
        """
        headers = {
            "approval_key": self.token,
            "custtype": "P",         # 개인 고객으로 가정
            "tr_type": "1",          # 주문 등록 (등록: "1")
            "content-type": "utf-8"
        }

        # 예시: 나스닥 거래소를 기준으로 'R' 접두사 사용 (실제 tr_key 형식은 문서 참고)
        tr_key = f"RNASA{symbol}"  # "R" + "NAS" + symbol

        body = {
            "input": {
                "tr_id": "HDFSASP0",  # 해외주식 주문 API 거래 ID (예시; 실제 값은 문서 확인)
                "tr_key": tr_key
            },
            "orderDetails": {
                "account": self.account_id,
                "orderType": order_type,
                "quantity": quantity
            }
        }

        if order_type == "limit":
            if price is None:
                raise ValueError("지정가 주문은 가격(price)을 입력해야 합니다.")
            body["orderDetails"]["price"] = price

        url = f"{self.base_url}/order"  # 실제 주문 API 엔드포인트 (문서 참고 후 수정)
        response = requests.post(url, json=body, headers=headers)
        return response.json()

    def cancel_order(self, order_id: str) -> dict:
        """
        해외 주식 주문 취소 실행 함수.
        
        :param order_id: 취소할 주문의 식별자
        :return: API 응답 JSON
        """
        headers = {
            "approval_key": self.token,
            "custtype": "P",
            "tr_type": "1",  # 주문 취소 관련 거래 ID를 사용 (예시)
            "content-type": "utf-8"
        }
        body = {
            "input": {
                "tr_id": "HDFSASP0",  # 주문 취소 거래 ID (예시)
                "order_id": order_id
            }
        }
        url = f"{self.base_url}/cancel_order"  # 실제 주문 취소 API 엔드포인트 (문서 참고 후 수정)
        response = requests.post(url, json=body, headers=headers)
        return response.json()
