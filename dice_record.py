import streamlit as st
import pandas as pd
import datetime
import csv
import base64

# アプリのタイトルと説明
st.title("サイコロ記録")
st.write("キャラクターに関するサイコロの出目を記録しておくためのアプリです")

# セッション状態の初期化
if 'records' not in st.session_state:
    st.session_state.records = []

# サイドバーでページ選択
page = st.sidebar.selectbox("ページを選択", ["新規入力", "記録を見る"])

if page == "新規入力":
    st.header("新規入力")
    
    # フォーム入力
    with st.form("input_form"):
        character_name = st.text_input("キャラクター名")
        date = st.date_input("年月日", min_value=datetime.date(2000, 1, 1))
        dice_result = st.number_input("さいころの出目", min_value=0, max_value=100, step=1)
        notes = st.text_area("備考")
        
        submitted = st.form_submit_button("記録する")
        
    if submitted:
        if character_name and date and dice_result is not None:
            st.session_state.records.append({
                "キャラクター名": character_name,
                "年月日": date,
                "さいころの出目": dice_result,
                "備考": notes
            })
            st.success("記録されました")
        else:
            st.error("必須項目が入力されていません")

elif page == "記録を見る":
    st.header("記録を見る")
    
    if not st.session_state.records:
        st.warning("記録がありません")
    else:
        df = pd.DataFrame(st.session_state.records)
        
        # フィルタリング
        unique_characters = df["キャラクター名"].unique()
        selected_characters = st.multiselect("キャラクター名でフィルタ", unique_characters)
        
        date_range = st.date_input("日付範囲", value=[df["年月日"].min(), df["年月日"].max()], key="date_range")
        
        dice_range = st.slider("さいころの出目の範囲", 0, 100, (0, 100))
        
        # フィルタの適用
        mask = pd.Series(True, index=df.index)
        if selected_characters:
            mask &= df["キャラクター名"].isin(selected_characters)
        mask &= (df["年月日"] >= date_range[0]) & (df["年月日"] <= date_range[1])
        mask &= (df["さいころの出目"] >= dice_range[0]) & (df["さいころの出目"] <= dice_range[1])
        
        filtered_df = df[mask]
        
        # 結果の表示
        st.write(filtered_df)
        
        # CSVダウンロード機能
        def get_table_download_link(df):
            csv = df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="dice_records.csv">CSVファイルをダウンロード</a>'
            return href

        st.markdown(get_table_download_link(filtered_df), unsafe_allow_html=True)