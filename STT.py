import streamlit as st
from audiorecorder import audiorecorder
from google import genai
import os
from datetime import datetime, date
from gtts import gTTS
import base64


##### 기능 구현 함수 #####
def STT(audio, client):
    """녹음된 오디오를 Gemini로 전사(음성 -> 텍스트)."""
    filename = "input.mp3"
    audio.export(filename, format="mp3")

    uploaded = client.files.upload(file=filename)
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=[
            "이 오디오에 담긴 말을 그대로 받아써 줘. 설명이나 다른 말은 붙이지 말고 내용만 출력해.",
            uploaded,
        ],
    )

    os.remove(filename)
    return response.text.strip()


def ask_gemini(messages, model, client):
    """대화 기록을 Gemini에 넣어 답변 생성."""
    contents = []
    for role, text in messages:
        contents.append({"role": role, "parts": [{"text": text}]})

    response = client.models.generate_content(
        model=model,
        contents=contents,
    )
    return response.text


def TTS(response):
    """답변 텍스트를 gTTS로 음성 파일로 만들고 자동 재생."""
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)

    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)

    os.remove(filename)


##### 페이지 스타일(CSS) #####
def load_css():
    st.markdown(
        """
        <style>
        /* 전체 배경 */
        .stApp {
            background: linear-gradient(180deg, #fff8f2 0%, #fdeee2 100%);
        }
        /* 헤더 타이틀 카드 */
        .title-card {
            background: linear-gradient(135deg, #ff9a56 0%, #ff6a88 100%);
            padding: 28px 32px;
            border-radius: 20px;
            box-shadow: 0 8px 24px rgba(255, 106, 136, 0.25);
            margin-bottom: 8px;
        }
        .title-card h1 {
            color: white;
            margin: 0;
            font-size: 2rem;
            font-weight: 800;
        }
        .title-card p {
            color: rgba(255,255,255,0.92);
            margin: 6px 0 0 0;
            font-size: 0.95rem;
        }
        /* 섹션 소제목 */
        .section-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #d2571e;
            margin-bottom: 8px;
        }
        /* 사이드바 배경 */
        section[data-testid="stSidebar"] {
            background: #fff3ea;
        }
        /* 버튼 강조 */
        .stButton>button {
            border-radius: 12px;
            border: 1px solid #ff9a56;
            color: #d2571e;
            font-weight: 600;
        }
        .stButton>button:hover {
            background: #ff9a56;
            color: white;
            border-color: #ff9a56;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


##### 대화 처리(질문 -> 답변 -> 음성) #####
def handle_question(question, model, client):
    """질문 텍스트를 받아 답변 생성 후 세션에 저장. (날짜 포함)"""
    today = date.today().isoformat()  # 예: "2026-08-18"
    now = datetime.now().strftime("%H:%M")

    st.session_state["chat"] = st.session_state["chat"] + [("user", today, now, question)]
    st.session_state["messages"] = st.session_state["messages"] + [("user", question)]

    response = ask_gemini(st.session_state["messages"], model, client)

    st.session_state["messages"] = st.session_state["messages"] + [("model", response)]
    now = datetime.now().strftime("%H:%M")
    st.session_state["chat"] = st.session_state["chat"] + [("bot", today, now, response)]

    return response


##### 메인 함수 #####
def main():
    st.set_page_config(
        page_title="음식 추천 음성 비서",
        page_icon="🍽️",
        layout="wide",
    )

    load_css()

    # 타이틀 카드
    st.markdown(
        """
        <div class="title-card">
            <h1>🍽️ 음식 추천 음성 비서</h1>
            <p>말로 물어보거나 직접 입력하면, 딱 맞는 메뉴를 추천해드려요!</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    with st.expander("ℹ️ 음식 추천 음성 비서에 관하여", expanded=True):
        st.write(
            """
            - 이 프로그램은 음성 또는 텍스트로 질문하면 상황에 맞는 음식을 추천해주는 비서입니다.
            - 왼쪽 사이드바에서 **음식 카테고리**와 **말투(톤)**를 골라 원하는 스타일로 추천받을 수 있습니다.
            - 오른쪽 **질문/답변**에서 달력으로 날짜를 고르면 그날의 대화만 볼 수 있습니다.
            - 📱 휴대폰에서는 마이크 녹음이 어려울 수 있으니 **텍스트 입력**을 이용해 주세요.
            - UI는 스트림릿(Streamlit)을 활용하여 만들었습니다.
            - STT(Speech-To-Text)는 Google Gemini를 활용하였습니다.
            - 음식 추천 답변은 Google Gemini 모델을 활용하였습니다.
            - TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용하였습니다.
            """
        )
        st.markdown("")

    # session state 초기화
    if "chat" not in st.session_state:
        st.session_state["chat"] = []  # (sender, date, time, message)

    if "GEMINI_API" not in st.session_state:
        st.session_state["GEMINI_API"] = ""

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False

    # 카테고리별 추천 지침
    CATEGORY_GUIDE = {
        "전체 (아무거나)": "특정 종류에 구애받지 말고 상황에 가장 잘 맞는 메뉴를 추천해.",
        "한식": "한식 메뉴 위주로 추천해.",
        "중식": "중식(중국요리) 메뉴 위주로 추천해.",
        "일식": "일식(일본요리) 메뉴 위주로 추천해.",
        "양식": "양식(서양요리) 메뉴 위주로 추천해.",
        "분식": "분식 메뉴 위주로 추천해.",
        "디저트/카페": "디저트, 음료, 카페 메뉴 위주로 추천해.",
        "야식": "야식으로 좋은 메뉴 위주로 추천해.",
    }

    # 톤(말투)별 지침
    TONE_GUIDE = {
        "친근함": "친구에게 말하듯 편하고 다정한 반말 섞인 말투로 답해.",
        "정중함": "격식 있고 예의 바른 존댓말로 정중하게 답해.",
        "유머러스": "위트 있고 유쾌하게, 가벼운 농담을 섞어 재미있게 답해.",
        "간결함": "군더더기 없이 핵심만 아주 짧고 간결하게 답해.",
    }

    # 사이드바
    with st.sidebar:
        st.markdown("### 🔑 설정")
        st.session_state["GEMINI_API"] = st.text_input(
            label="GEMINI API 키",
            placeholder="Enter Your API Key",
            value="",
            type="password",
        )

        st.markdown("---")

        st.markdown("### 🍜 음식 카테고리")
        category = st.radio(
            label="추천받을 음식 종류를 골라주세요",
            options=list(CATEGORY_GUIDE.keys()),
        )

        st.markdown("---")

        st.markdown("### 🗣️ 말투(톤)")
        tone = st.radio(
            label="답변 말투를 골라주세요",
            options=list(TONE_GUIDE.keys()),
        )

        st.markdown("---")

        st.markdown("### 🤖 Gemini 모델")
        model = st.radio(
            label="모델 선택",
            options=["gemini-flash-latest", "gemini-pro-latest"],
        )

        st.markdown("---")

        reset_clicked = st.button(label="🔄 대화 초기화")

    # 선택한 카테고리 + 톤을 반영한 시스템 지침 구성
    SYSTEM_INSTRUCTION = (
        "너는 음식 추천 전문 비서야. 사용자의 상황, 기분, 가진 재료, 취향을 고려해 "
        "구체적인 음식이나 메뉴를 한국어로 추천해. "
        f"{CATEGORY_GUIDE[category]} "
        f"{TONE_GUIDE[tone]} "
        "답변은 50단어 이내로 해."
    )

    # 초기화 버튼 동작
    if reset_clicked:
        st.session_state["chat"] = []
        st.session_state["messages"] = []
        st.session_state["check_reset"] = True

    # 매 실행마다 첫 지침을 현재 선택된 카테고리/톤으로 최신화
    if len(st.session_state["messages"]) == 0:
        st.session_state["messages"] = [("user", SYSTEM_INSTRUCTION)]
    else:
        st.session_state["messages"][0] = ("user", SYSTEM_INSTRUCTION)

    # API 키가 없으면 안내 후 종료
    if not st.session_state["GEMINI_API"]:
        st.warning("왼쪽 사이드바에 Gemini API 키를 입력해 주세요.")
        return

    client = genai.Client(api_key=st.session_state["GEMINI_API"])

    new_response = None  # 이번 실행에서 새로 만들어진 답변(있으면 음성 재생)

    # 기능 구현 공간
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">🎤 질문하기</div>', unsafe_allow_html=True)
        st.caption(f"현재 카테고리: **{category}** / 말투: **{tone}**")

        # (1) 음성 녹음으로 질문
        audio = audiorecorder("클릭하여 녹음하기", "녹음 중...")
        if (audio.duration_seconds > 0) and (st.session_state["check_reset"] == False):
            st.audio(audio.export().read())
            question = STT(audio, client)
            new_response = handle_question(question, model, client)

        st.markdown("###### ⌨️ 또는 텍스트로 질문 (컴퓨터/휴대폰 공통)")
        # (2) 텍스트로 질문 - 폼으로 묶어 엔터/버튼 모두 전송 가능
        with st.form(key="text_form", clear_on_submit=True):
            text_question = st.text_input(
                label="질문 입력",
                placeholder="예: 비 오는 날 먹기 좋은 메뉴 추천해줘",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("전송하기")

        if submitted and text_question.strip() and (st.session_state["check_reset"] == False):
            new_response = handle_question(text_question.strip(), model, client)

    with col2:
        st.markdown('<div class="section-title">💬 질문/답변</div>', unsafe_allow_html=True)

        # 달력으로 날짜 선택
        selected_date = st.date_input("📅 날짜를 선택하면 그날의 대화를 볼 수 있어요", value=date.today())
        selected_str = selected_date.isoformat()

        # 선택한 날짜의 대화만 필터링
        day_chat = [c for c in st.session_state["chat"] if c[1] == selected_str]

        if len(day_chat) == 0:
            st.info("이 날짜에 나눈 대화가 없어요. 왼쪽에서 질문해 보세요! 🍽️")
        else:
            for sender, day, time, message in day_chat:
                if sender == "user":
                    st.write(
                        f'<div style="display:flex;align-items:center;margin-bottom:4px;">'
                        f'<div style="background-color:#ff6a88;color:white;border-radius:14px;'
                        f'padding:8px 14px;margin-right:8px;box-shadow:0 2px 6px rgba(255,106,136,0.25);">{message}</div>'
                        f'<div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                        unsafe_allow_html=True,
                    )
                    st.write("")
                else:
                    st.write(
                        f'<div style="display:flex;align-items:center;justify-content:flex-end;margin-bottom:4px;">'
                        f'<div style="background-color:#fff;border:1px solid #ffd9c2;border-radius:14px;'
                        f'padding:8px 14px;margin-left:8px;box-shadow:0 2px 6px rgba(0,0,0,0.06);">🍽️ {message}</div>'
                        f'<div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                        unsafe_allow_html=True,
                    )
                    st.write("")

        # 이번에 새로 생성된 답변이 있으면 음성으로 재생
        if new_response is not None:
            TTS(new_response)

        st.session_state["check_reset"] = False


if __name__ == "__main__":
    main()
