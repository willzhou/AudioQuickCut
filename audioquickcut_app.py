# Author: Ningbo Wise Effects, Inc. (汇视创影) & Will Zhou
# License: Apache 2.0

import streamlit as st
import os
from datetime import datetime
import tempfile
import ffmpeg
from obsws_python import ReqClient
import time
import shutil

from dotenv import load_dotenv
 
# 加载环境变量
load_dotenv()

# 创建保存音频的目录
AUDIO_HISTORY_DIR = "audio_history"
os.makedirs(AUDIO_HISTORY_DIR, exist_ok=True)

def extract_audio(input_file, output_format, start_time=0, duration=10):
    """改进版音频提取，自动回退到可用格式"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            wav_path = tmp_file.name
        
        # 先统一转为WAV（所有FFmpeg都支持）
        (
            ffmpeg
            .input(input_file, ss=start_time, t=duration)
            .output(wav_path, acodec='pcm_s16le')
            .overwrite_output()
            .run(quiet=True)
        )
        
        # 如果用户要MP3且系统支持
        if output_format == 'mp3':
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as mp3_file:
                    mp3_path = mp3_file.name
                (
                    ffmpeg
                    .input(wav_path)
                    .output(mp3_path, acodec='libmp3lame')
                    .overwrite_output()
                    .run(quiet=True)
                )
                os.unlink(wav_path)
                return mp3_path
            except:
                st.warning("系统不支持MP3编码，已自动转为WAV格式")
                return wav_path
        return wav_path
    except Exception as e:
        st.error(f"音频提取失败: {str(e)}")
        return None

def record_with_obs(duration=10):
    """通过OBS录制音频"""
    try:
        with ReqClient(
            host=os.getenv("OBS_HOST", "localhost"),
            port=int(os.getenv("OBS_PORT", 4455)),
            password=os.getenv("OBS_PASSWORD", "")
        ) as cl:
            cl.start_record()
            time.sleep(duration)
            resp = cl.stop_record()
            st.info(f"OBS录制已保存：{resp.output_path}")
            return resp.output_path
    except Exception as e:
        st.error(f"OBS录制失败: {str(e)}")
        return None

def save_to_history(file_path, source_type):
    """将音频文件保存到历史记录目录"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{source_type}_{timestamp}{os.path.splitext(file_path)[1]}"
    dest_path = os.path.join(AUDIO_HISTORY_DIR, filename)
    shutil.copy(file_path, dest_path)
    return dest_path

def main():
    st.title("AudioQuickCut")
    st.markdown("### 简单易用的音频录制与提取工具")
    
    # 初始化历史记录
    if 'audio_history' not in st.session_state:
        st.session_state.audio_history = []
    
    # 模式选择
    mode = st.radio("选择输入模式", ["上传文件", "OBS录制"])
    
    if mode == "上传文件":
        uploaded_file = st.file_uploader(
            "上传视频文件", 
            type=['mp4', 'mov', 'mkv', 'avi', 'flv', 'wmv']
        )
        
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                input_path = tmp_file.name
            
            st.video(uploaded_file)
            
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.number_input("开始时间 (秒)", min_value=0, value=0, step=1)
            with col2:
                duration = st.number_input("提取时长 (秒)", min_value=1, max_value=300, value=10, step=1)
            
            output_format = st.radio("输出格式", ['mp3', 'wav'])
            
            if st.button("🎧 提取音频"):
                with st.spinner("处理中..."):
                    output_path = extract_audio(
                        input_path,
                        output_format,
                        start_time=start_time,
                        duration=duration
                    )
                    
                    if output_path:
                        # 保存到历史记录
                        history_path = save_to_history(output_path, "extracted")
                        st.session_state.audio_history.append({
                            "path": history_path,
                            "type": "extracted",
                            "timestamp": datetime.now(),
                            "format": output_format
                        })
                        
                        with open(history_path, "rb") as f:
                            audio_bytes = f.read()
                            st.audio(audio_bytes, format=f'audio/{output_format}')
                            st.download_button(
                                "下载音频",
                                audio_bytes,
                                os.path.basename(history_path),
                                f"audio/{output_format}"
                            )
                        os.unlink(output_path)
                    os.unlink(input_path)
    
    else:  # OBS录制模式
        st.warning("请确保：\n1. OBS已运行\n2. WebSocket插件启用(设置→WebSocket→端口4455)")
        
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.number_input("开始时间 (秒)", min_value=0, value=0, step=1)
        with col2:
            duration = st.number_input("提取时长 (秒)", min_value=1, max_value=300, value=10, step=1)

        output_format = st.radio("输出格式", ['mp3', 'wav'])
        
        if st.button("● 开始录制"):
            with st.spinner(f"正在录制 {duration} 秒..."):
                video_path = record_with_obs(duration)
                
                if video_path:
                    output_path = extract_audio(
                        video_path,
                        output_format,
                        start_time=start_time,
                        duration=duration
                    )
                    
                    if output_path:
                        # 保存到历史记录
                        history_path = save_to_history(output_path, "recorded")
                        st.session_state.audio_history.append({
                            "path": history_path,
                            "type": "recorded",
                            "timestamp": datetime.now(),
                            "format": output_format
                        })
                        
                        with open(history_path, "rb") as f:
                            audio_bytes = f.read()
                            st.audio(audio_bytes, format=f'audio/{output_format}')
                            st.download_button(
                                "下载录音",
                                audio_bytes,
                                os.path.basename(history_path),
                                f"audio/{output_format}"
                            )
                        os.unlink(output_path)

    # 显示历史记录
    if st.session_state.audio_history:
        st.subheader("📚 历史记录")
        st.write("以下是您之前处理的音频文件：")
        
        for idx, item in enumerate(reversed(st.session_state.audio_history)):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"{idx+1}. {item['type']} - {item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} ({item['format']})")
            with col2:
                with open(item["path"], "rb") as f:
                    st.download_button(
                        f"下载 #{idx+1}",
                        f.read(),
                        os.path.basename(item["path"]),
                        f"audio/{item['format']}",
                        key=f"dl_{idx}"
                    )
            with col3:
                if st.button(f"删除 #{idx+1}", key=f"del_{idx}"):
                    try:
                        os.unlink(item["path"])
                        st.session_state.audio_history.remove(item)
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"删除失败: {str(e)}")

if __name__ == "__main__":
    main()