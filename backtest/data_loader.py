import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from data_downloader import download_data, save_data_to_db, DB_PATH

def load_data(symbol: str, db_path: str = DB_PATH) -> pd.DataFrame:
    """
    SQLite3 데이터베이스에서 symbol 데이터를 불러옵니다.
    데이터가 없으면 다운로드 후 저장하며, 최신 데이터(어제까지)가 누락된 경우 추가 다운로드하여 업데이트합니다.
    :param symbol: 종목 코드 (예: 'TSLA')
    :param db_path: SQLite DB 파일 경로
    :return: 최신 데이터가 반영된 DataFrame (index: Date)
    """
    conn = sqlite3.connect(db_path)
    query = f"SELECT * FROM '{symbol}'"
    try:
        df = pd.read_sql(query, conn, index_col='Date')
        df.index = pd.to_datetime(df.index)
    except Exception as e:
        print(f"Error loading data for {symbol}: {e}")
        df = pd.DataFrame()
    conn.close()
    
    today = datetime.today() - timedelta(hours=9)
    yesterday = today - timedelta(days=1)
    
    if df.empty:
        # 데이터가 없으면 전체 데이터를 다운로드 후 저장
        df = download_data(symbol)
        save_data_to_db(df, symbol, db_path)
    else:
        last_date = df.index.max()
        # 만약 마지막 날짜가 어제보다 이전이면, 누락된 기간 데이터 다운로드
        if last_date < yesterday.replace(hour=0, minute=0, second=0, microsecond=0):
            start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = yesterday.strftime('%Y-%m-%d')
            new_df = download_data(symbol, start_date=start_date, end_date=end_date)
            if not new_df.empty:
                # 기존 데이터와 합치기 전에 중복 제거
                df = pd.concat([df, new_df])
                df = df[~df.index.duplicated(keep='last')]
                df.sort_index(inplace=True)
                # 새로운 데이터만 DB에 저장 (중복은 기본키 제약에 의해 무시됨)
                save_data_to_db(new_df, symbol, db_path)
    return df
