import requests

class QuotationService:
    """
    해외주식 시세 조회 API 연동 모듈.
    참고: https://apiportal.koreainvestment.com/apiservice/apiservice-oversea-stock-quotations
    """
    def __init__(self, base_url: str, token: str):
        """
        :param base_url: API 기본 URL (예: "https://apiportal.koreainvestment.com/apiservice")
        :param token: API 접근 토큰(또는 approval_key)
        """
        self.base_url = base_url
        self.token = token

    def get_quote(self, symbol: str) -> dict:
        """
        해외 주식의 현재체결가(시세)를 조회합니다.
        
        :param symbol: 종목 코드 (예: TSLA)
        :return: API 응답 JSON
        """
        headers = {
            "approval_key": self.token,
            "custtype": "P",
            "tr_type": "1",
            "content-type": "utf-8"
        }
        # 예시: 'D' 접두사로 시세 조회 시, 거래소 구분(NAS: 나스닥)을 사용 (실제 형식은 문서 참고)
        tr_key = f"DNASA{symbol}"  # "D" + "NAS" + symbol

        body = {
            "input": {
                "tr_id": "HDFSCNT0",  # 해외주식 시세 조회 API 거래 ID (예시)
                "tr_key": tr_key
            }
        }
        url = f"{self.base_url}/quotation"  # 실제 시세 조회 API 엔드포인트 (문서 참고 후 수정)
        response = requests.post(url, json=body, headers=headers)
        return response.json()
