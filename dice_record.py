import os
import json
import streamlit as st
import pandas as pd
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 環境変数から認証情報を取得
json_str = st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
json_data = json.loads(json_str)
credentials = service_account.Credentials.from_service_account_info(json_data)

# Google Sheets API の設定
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = '/Users/Shared/App_development/Dice_record/complete-octane-413900-d2fdd47f8ec0.json'  # サービスアカウントキーのパスを指定
SAMPLE_SPREADSHEET_ID = '1LU7mBeBz2Nirp5H09kJMi7-dgmKLzXVVKMv_k7vCtIQ'  # スプレッドシートのIDを指定
SAMPLE_RANGE_NAME = 'Sheet1!A1:E1000'  # データを書き込む範囲を指定

# 認証とシートサービスの作成
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# アプリのタイトルと説明
st.title("サイコロ記録")
st.write("キャラクターに関するサイコロの出目を記録しておくためのアプリです")

# Google Sheetsからデータを読み込む関数
def load_data():
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])
    if not values:
        return pd.DataFrame(columns=["キャラクター名", "年月日", "さいころの出目", "備考"])
    df = pd.DataFrame(values[1:], columns=values[0])
    # 年月日列をdatetime型に変換
    df['年月日'] = pd.to_datetime(df['年月日'])
    return df

# データをGoogle Sheetsに保存する関数
def save_data(data):
    # 日付列を文字列に変換
    data_to_save = data.copy()
    data_to_save['年月日'] = data_to_save['年月日'].dt.strftime('%Y-%m-%d')
    
    values = [data_to_save.columns.tolist()] + data_to_save.values.tolist()
    body = {'values': values}
    result = service.spreadsheets().values().update(
        spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME,
        valueInputOption='USER_ENTERED', body=body).execute()

# 初期データ読み込み
if 'records' not in st.session_state:
    st.session_state.records = load_data()

# サイドバーでページ選択
page = st.sidebar.selectbox("ページを選択", ["新規入力", "記録を見る"])

if page == "新規入力":
    st.header("新規入力")
    
    character_name = st.text_input("キャラクター名")
    date = st.date_input("年月日", min_value=datetime.date(2000, 1, 1))
    dice_result = st.number_input("さいころの出目", min_value=0, max_value=100, step=1)
    notes = st.text_area("備考")
    submitted = st.button("記録する")
    
    if submitted:
        if character_name and date and dice_result is not None:
            new_record = {
                "キャラクター名": character_name,
                "年月日": pd.to_datetime(date),  # datetime型に変換
                "さいころの出目": dice_result,
                "備考": notes
            }
            st.session_state.records = pd.concat([st.session_state.records, pd.DataFrame([new_record])], ignore_index=True)
            save_data(st.session_state.records)  # Google Sheetsにデータを保存
            st.success("記録されました")
        else:
            st.error("必須項目が入力されていません")

elif page == "記録を見る":
    st.header("記録を見る")
    
    if st.session_state.records.empty:
        st.warning("記録がありません")
    else:
        # フィルタリング
        unique_characters = st.session_state.records["キャラクター名"].unique()
        selected_characters = st.multiselect("キャラクター名でフィルタ", unique_characters)

        min_date = st.session_state.records['年月日'].min().date()
        max_date = st.session_state.records['年月日'].max().date()
        date_range = st.date_input("日付範囲", value=[min_date, max_date], key="date_range")
        dice_range = st.slider("さいころの出目の範囲", 0, 100, (0, 100))
        
        # フィルタの適用
        mask = pd.Series(True, index=st.session_state.records.index)
        if selected_characters:
            mask &= st.session_state.records["キャラクター名"].isin(selected_characters)
        mask &= (st.session_state.records["年月日"].dt.date >= date_range[0]) & (st.session_state.records["年月日"].dt.date <= date_range[1])
        mask &= (st.session_state.records["さいころの出目"].astype(int) >= dice_range[0]) & (st.session_state.records["さいころの出目"].astype(int) <= dice_range[1])
        filtered_df = st.session_state.records[mask]
                
        # 結果の表示
        st.write(filtered_df)