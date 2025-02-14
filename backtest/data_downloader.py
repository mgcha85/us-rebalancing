import os
import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# 데이터베이스 파일 경로 (backtest 폴더 내에 data.db)
DB_PATH = os.path.join(os.path.dirname(__file__), 'data.db')

def download_data(symbol: str, start_date: str = None, end_date: str = None, interval: str = '1d') -> pd.DataFrame:
    """
    Yahoo Finance에서 symbol의 데이터를 다운로드합니다.
    :param symbol: 종목 코드 (예: 'TSLA')
    :param start_date: 시작 날짜 (YYYY-MM-DD), None이면 기본적으로 10년 전부터 다운로드
    :param end_date: 종료 날짜 (YYYY-MM-DD), None이면 오늘 기준 어제까지 다운로드
    :param interval: 데이터 간격 (기본 '1d')
    :return: 다운로드된 데이터 DataFrame
    """
    if end_date is None:
        end_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.today() - timedelta(days=365*10)).strftime('%Y-%m-%d')
    
    df = yf.download(symbol, start=start_date, end=end_date, interval=interval, progress=False)
    df.index = pd.to_datetime(df.index)
    df.columns = [x[0] for x in df.columns]
    return df

def save_data_to_db(df: pd.DataFrame, symbol: str, db_path: str = DB_PATH) -> None:
    """
    DataFrame을 SQLite3 데이터베이스에 저장합니다.
    테이블 이름은 'stock_data'이며, Symbol과 Date를 기본 키로 사용합니다.
    :param df: 저장할 DataFrame (index는 Date여야 함)
    :param symbol: 종목 코드 (파일명에 사용)
    :param db_path: SQLite DB 파일 경로
    """
    conn = sqlite3.connect(db_path)
    df.to_sql(symbol, conn, if_exists='append')
    conn.close()
