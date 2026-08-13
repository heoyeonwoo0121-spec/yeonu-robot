import streamlit as st
from audiorecorder import audiorecorder
from google import genai
import os
from datetime import datetime
from gtts import gTTS
import base64


##### 기능 구현 함수 #####
def STT(audio, client):
    """녹음된 오디오를 Gemini로 전사(음성 -> 텍스트)."""
    filename = "input.mp3"
    audio.export(filename, format="mp3")

    uploaded = client.files.upload(file=filename)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
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


##### 메인 함수 #####
def main():
    st.set_page_config(
        page_title="음성 비서 프로그램",
        layout="wide",
    )

    st.header("음성 비서 프로그램")
    st.markdown("---")

    with st.expander("음성비서 프로그램에 관하여", expanded=True):
        st.write(
            """
            - 음성비서 프로그램의 UI는 스트림릿을 활용하여 만들었습니다.
            - STT(Speech-To-Text)는 Google Gemini를 활용하였습니다.
            - 답변은 Google Gemini 모델을 활용하였습니다.
            - TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용하였습니다.
            """
        )
        st.markdown("")

    SYSTEM_INSTRUCTION = (
        "너는 사려 깊은 비서야. 모든 질문에 25단어 이내로, 한국어로 답해."
    )

    # session state 초기화
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    if "GEMINI_API" not in st.session_state:
        st.session_state["GEMINI_API"] = ""

    if "messages" not in st.session_state:
        st.session_state["messages"] = [("user", SYSTEM_INSTRUCTION)]

    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False

    # 사이드바
    with st.sidebar:
        st.session_state["GEMINI_API"] = st.text_input(
            label="GEMINI API 키",
            placeholder="Enter Your API Key",
            value="",
            type="password",
        )

        st.markdown("---")

        model = st.radio(
            label="Gemini 모델",
            options=["gemini-2.5-flash", "gemini-2.5-pro"],
        )

        st.markdown("---")

        if st.button(label="초기화"):
            st.session_state["chat"] = []
            st.session_state["messages"] = [("user", SYSTEM_INSTRUCTION)]
            st.session_state["check_reset"] = True

    # API 키가 없으면 안내 후 종료
    if not st.session_state["GEMINI_API"]:
        st.warning("왼쪽 사이드바에 Gemini API 키를 입력해 주세요.")
        return

    client = genai.Client(api_key=st.session_state["GEMINI_API"])

    # 기능 구현 공간
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("질문하기")
        audio = audiorecorder("클릭하여 녹음하기", "녹음 중...")
        if (audio.duration_seconds > 0) and (st.session_state["check_reset"] == False):
            st.audio(audio.export().read())
            question = STT(audio, client)

            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("user", now, question)]
            st.session_state["messages"] = st.session_state["messages"] + [("user", question)]

    with col2:
        st.subheader("질문/답변")
        if (audio.duration_seconds > 0) and (st.session_state["check_reset"] == False):
            response = ask_gemini(st.session_state["messages"], model, client)

            st.session_state["messages"] = st.session_state["messages"] + [("model", response)]

            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("bot", now, response)]

            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(
                        f'<div style="display:flex;align-items:center;">'
                        f'<div style="background-color:#007AFF;color:white;border-radius:12px;'
                        f'padding:8px 12px;margin-right:8px;">{message}</div>'
                        f'<div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                        unsafe_allow_html=True,
                    )
                    st.write("")
                else:
                    st.write(
                        f'<div style="display:flex;align-items:center;justify-content:flex-end;">'
                        f'<div style="background-color:lightgray;border-radius:12px;'
                        f'padding:8px 12px;margin-left:8px;">{message}</div>'
                        f'<div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                        unsafe_allow_html=True,
                    )
                    st.write("")

            TTS(response)
        else:
            st.session_state["check_reset"] = False


if __name__ == "__main__":
    main()