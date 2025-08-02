import streamlit as st
from faster_whisper import WhisperModel
import tempfile
import os
import json

# إعداد الصفحة
st.set_page_config(page_title="تفريغ صوت وترجمة", layout="centered")
st.title("🎧 تفريغ صوت - يدعم العربية + ترجمة + حفظ بصيغ متعددة")

@st.cache_resource
def load_model():
    return WhisperModel("medium", device="cpu", compute_type="int8")

model = load_model()

uploaded_file = st.file_uploader("📤 اختر ملف صوتي", type=["mp3", "wav", "m4a", "flac", "ogg"])

# خيارات المستخدم
translate_to_english = st.checkbox("🌍 ترجمة تلقائية إلى الإنجليزية")
output_format = st.selectbox("💾 اختر صيغة الإخراج", ["TXT", "SRT", "JSON"])

def format_srt(segments):
    srt_output = ""
    for i, seg in enumerate(segments, 1):
        start = format_time(seg.start)
        end = format_time(seg.end)
        srt_output += f"{i}\n{start} --> {end}\n{seg.text.strip()}\n\n"
    return srt_output

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.read())
        audio_path = tmp.name

    st.success("✅ تم رفع الملف.")

    if st.button("🔍 ابدأ التفريغ"):
        with st.spinner("جاري التفريغ..."):
            segments, info = model.transcribe(
                audio_path,
                language="ar",
                task="translate" if translate_to_english else "transcribe"
            )

            segment_list = list(segments)

            if output_format == "TXT":
                full_text = "\n".join([seg.text.strip() for seg in segment_list])
                st.text_area("📄 النص الناتج:", full_text, height=300)
                st.download_button("📥 تحميل TXT", full_text, file_name="transcript.txt")

            elif output_format == "SRT":
                srt_text = format_srt(segment_list)
                st.text_area("📄 ملف SRT:", srt_text, height=300)
                st.download_button("📥 تحميل SRT", srt_text, file_name="transcript.srt")

            elif output_format == "JSON":
                json_data = [{
                    "start": float(seg.start),
                    "end": float(seg.end),
                    "text": seg.text.strip()
                } for seg in segment_list]
                json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
                st.download_button("📥 تحميل JSON", json_str, file_name="transcript.json")

        os.remove(audio_path)
