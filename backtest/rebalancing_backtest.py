import pandas as pd
import numpy as np
from datetime import timedelta
import yaml
from data_loader import load_data

def multi_stock_rebalancing_backtest(symbols: list, weights: dict, 
                                       initial_capital: float = 100000,
                                       rebalance_freq: str = 'W') -> pd.DataFrame:
    """
    여러 종목에 대해, config에 정의된 비중에 맞춰 리밸런싱 백테스트를 수행합니다.
    각 종목의 데이터는 개별 DataFrame(data_dict에 저장)으로 불러오며,
    공통 날짜(inner join)를 기준으로 백테스트를 진행합니다.
    
    :param symbols: 종목 코드 리스트 (예: ['TSLA', 'JPM', 'JNJ', 'PG', 'PLTR'])
    :param weights: 종목별 비중 dict (예: {'TSLA':0.2, 'JPM':0.2, ...}); 합은 1.0 이어야 함
    :param initial_capital: 초기 투자금
    :param rebalance_freq: 리밸런싱 주기 ('d', 'w', 'm')
    :return: 날짜별 포트폴리오 가치 DataFrame (index: Date, 컬럼: 'Portfolio Value')
    """
    # 리밸런싱 주기 매핑: 입력은 'd', 'w', 'm'을 대문자로 변환하여 사용
    freq_map = {'d': 'D', 'w': 'W', 'm': 'M'}
    rebalance_freq = rebalance_freq.lower()
    if rebalance_freq not in freq_map:
        raise ValueError("rebalance_freq는 'd', 'w', 'm' 중 하나여야 합니다.")
    freq_alias = freq_map[rebalance_freq]
    
    # 각 종목의 데이터를 load_data를 통해 불러오고 'Close' 컬럼만 사용
    data_dict = {}
    for symbol in symbols:
        df = load_data(symbol)  # load_data 함수는 DB에서 불러온 데이터를 반환
        # 'Close' 컬럼만 사용하고, 컬럼명을 symbol로 변경
        df = df[['Close']].rename(columns={'Close': symbol})
        df.sort_index(inplace=True)
        data_dict[symbol] = df

    # 공통 날짜(inner join): 각 종목의 index 교집합
    common_dates = None
    for df in data_dict.values():
        if common_dates is None:
            common_dates = set(df.index)
        else:
            common_dates = common_dates.intersection(set(df.index))
    common_dates = sorted(common_dates)
    common_index = pd.DatetimeIndex(common_dates)
    
    # 각 종목 DataFrame을 공통 날짜로 subset
    for symbol in symbols:
        data_dict[symbol] = data_dict[symbol].loc[common_index]
    
    # 리밸런싱 날짜: 공통 날짜에서 선택 (각 기간의 첫 거래일)
    rebalance_dates = common_index[~common_index.to_period(freq_alias).duplicated()]
    
    # 포트폴리오 시뮬레이션
    capital = initial_capital
    shares = {}
    # 초기 리밸런싱: 첫 공통 날짜에 초기 자본을 각 종목에 target 비중에 맞게 배분
    first_date = common_index[0]
    for symbol in symbols:
        price = data_dict[symbol].loc[first_date, symbol]
        target_alloc = weights[symbol] * capital
        shares[symbol] = target_alloc / price

    portfolio_values = []
    for date in common_index:
        if date in rebalance_dates:
            current_value = sum(shares[sym] * data_dict[sym].loc[date, sym] for sym in symbols)
            for symbol in symbols:
                price = data_dict[symbol].loc[date, symbol]
                target_value = weights[symbol] * current_value
                shares[symbol] = target_value / price
        daily_value = sum(shares[sym] * data_dict[sym].loc[date, sym] for sym in symbols)
        portfolio_values.append(daily_value)
    
    result = pd.DataFrame(data=portfolio_values, index=common_index, columns=['Portfolio Value'])
    return result, data_dict  # data_dict도 반환하여 각 종목의 홀딩 성과 계산에 활용

def compute_stock_performance(df: pd.DataFrame, symbol: str) -> dict:
    """
    단순 홀딩 시, 해당 종목의 수익률과 최대 낙폭(MDD)을 계산합니다.
    :param df: 종목 데이터 DataFrame (index: Date, 컬럼: symbol)
    :param symbol: 종목 코드
    :return: {'return': %, 'MDD': %}
    """
    prices = df[symbol]
    holding_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
    # 최대 낙폭(MDD) 계산: 가격 / 누적 최고가 - 1
    running_max = prices.cummax()
    drawdown = (prices / running_max - 1)
    max_drawdown = drawdown.min() * 100  # 음수값
    return {'return': holding_return, 'MDD': max_drawdown}

def compute_portfolio_performance(portfolio_df: pd.DataFrame, initial_capital: float) -> dict:
    """
    포트폴리오 전체의 수익률 및 최대 낙폭(MDD)을 계산합니다.
    :param portfolio_df: 날짜별 포트폴리오 가치 DataFrame
    :param initial_capital: 초기 투자금
    :return: {'return': %, 'MDD': %}
    """
    final_value = portfolio_df['Portfolio Value'].iloc[-1]
    portfolio_return = (final_value / initial_capital - 1) * 100
    running_max = portfolio_df['Portfolio Value'].cummax()
    drawdown = (portfolio_df['Portfolio Value'] / running_max - 1)
    max_drawdown = drawdown.min() * 100
    return {'return': portfolio_return, 'MDD': max_drawdown}

def generate_report(symbols: list, weights: dict, portfolio_df: pd.DataFrame, 
                    data_dict: dict, initial_capital: float, rebalance_freq: str) -> None:
    """
    최종 리포트를 생성합니다.
      - 투자 기간, 종목 개수, 리밸런싱 주기
      - 포트폴리오 수익률 및 MDD
      - 각 종목 단순 홀딩 시의 수익률 및 MDD
      - 리밸런싱 결과 대비 홀딩 결과 비교
    """
    start_date = portfolio_df.index[0].strftime('%Y-%m-%d')
    end_date = portfolio_df.index[-1].strftime('%Y-%m-%d')
    num_stocks = len(symbols)
    portfolio_perf = compute_portfolio_performance(portfolio_df, initial_capital)
    
    print("========== 최종 백테스트 리포트 ==========")
    print(f"투자 기간       : {start_date} ~ {end_date}")
    print(f"종목 개수       : {num_stocks}")
    print(f"리밸런싱 주기   : {rebalance_freq.upper()}")
    print(f"포트폴리오 수익률: {portfolio_perf['return']:.2f}%")
    print(f"포트폴리오 MDD : {portfolio_perf['MDD']:.2f}%")
    print("\n[개별 종목 단순 홀딩 성과]")
    for symbol in symbols:
        perf = compute_stock_performance(data_dict[symbol], symbol)
        print(f"{symbol}: 수익률 {perf['return']:.2f}%, MDD {perf['MDD']:.2f}%")
    print("=========================================")

if __name__ == "__main__":
    # 예시: config.yaml에서 종목 및 비중 로드 (예: TSLA, JPM, JNJ, PG, PLTR)
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    stocks_config = config.get('stocks', {})
    symbols = list(stocks_config.keys())
    weights = stocks_config  # 합계 1.0이라고 가정

    # 리밸런싱 주기: 'd', 'w', 'm' (여기서는 주간 'W' 사용)
    rebalance_period = 'M'
    initial_capital = 10000

    portfolio_df, data_dict = multi_stock_rebalancing_backtest(symbols, weights, 
                                                                 initial_capital=initial_capital,
                                                                 rebalance_freq=rebalance_period)
    print("날짜별 포트폴리오 가치 (마지막 5일):")
    print(portfolio_df.tail())
    
    # 최종 리포트 생성
    generate_report(symbols, weights, portfolio_df, data_dict, initial_capital, rebalance_period)
