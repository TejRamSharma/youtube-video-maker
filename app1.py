import streamlit as st
import yt_dlp
import subprocess
import os

st.set_page_config(page_title="Video Auto Merger", layout="centered")
st.title("🎬 YouTube Audio + Custom Background Video Merger")

# Inputs
youtube_url = st.text_input("1. YouTube Video Link डालें (Audio के लिए):")
uploaded_video = st.file_uploader("2. Background Video अपलोड करें (.mp4 / .mov):", type=["mp4", "mov", "mkv"])
custom_title = st.text_input("3. Title (वैकल्पिक):")

if st.button("Generate Final Video"):
    if not youtube_url:
        st.warning("कृपया YouTube लिंक डालें!")
    elif not uploaded_video:
        st.warning("कृपया बैकग्राउंड वीडियो फ़ाइल अपलोड करें!")
    else:
        # Step 1: Uploaded Video को Local Save करें
        bg_video_path = "uploaded_bg.mp4"
        with open(bg_video_path, "wb") as f:
            f.write(uploaded_video.read())
        st.info("✅ बैकग्राउंड वीडियो अपलोड हो गई।")

        # Step 2: YouTube से Audio Extract करना (403 Error Fix के साथ)
        with st.spinner("🎵 YouTube से Audio डाउनलोड हो रहा है..."):
            audio_file = "downloaded_audio.mp3"
            if os.path.exists(audio_file):
                os.remove(audio_file)

            ydl_opts = {
    'format': 'ba/b',
    'outtmpl': 'downloaded_audio.%(ext)s',
    # YouTube Cloud IP blocks bypass karne ke liye Android client:
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'mweb'],
            'player_skip': ['webpage', 'configs'],
        }
    },
    'http_headers': {
        'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
    },
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '128',
    }],
}

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)
                    video_title = custom_title if custom_title.strip() else info.get('title', 'Video')
                st.success(f"ऑडियो तैयार: {video_title}")
            except Exception as e:
                st.error(f"डाउनलोड एरर: {e}")
                st.stop()

        # Step 3: FFmpeg Merge (Loop Background Video + Replace Audio)
        with st.spinner("⚙️ वीडियो प्रोसेस हो रही है (यह बहुत तेज़ होगी)..."):
            output_video = "final_output.mp4"
            if os.path.exists(output_video):
                os.remove(output_video)

            # FFmpeg Command:
            # -stream_loop -1 : वीडियो छोटी हो तो ऑडियो के खत्म होने तक लूप करेगा
            # -map 0:v:0 : सिर्फ अपलोडेड वीडियो का विजुअल लेगा
            # -map 1:a:0 : सिर्फ यूट्यूब वाला ऑडियो लेगा (ओरिजिनल वीडियो का साउंड हटा देगा)
            # -shortest : जैसे ही ऑडियो खत्म होगा, वीडियो रुक जाएगी
            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-i", bg_video_path,
                "-i", audio_file,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "copy",          # वीडियो को री-एन्कोड नहीं करेगा (Super Fast!)
                "-c:a", "copy",          # ऑडियो को भी डायरेक्ट कॉपी करेगा
                "-shortest", output_video
            ]

            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            st.success("🎉 आपकी वीडियो तैयार हो गई!")

        # Step 4: Preview और Download Button
        st.video(output_video)
        with open(output_video, "rb") as file:
            st.download_button(
                label="📥 Download Merged Video",
                data=file,
                file_name="final_merged_video.mp4",
                mime="video/mp4"
            )