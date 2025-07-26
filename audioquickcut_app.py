import streamlit as st
import os
from datetime import datetime
from pydub import AudioSegment
import tempfile
import ffmpeg

def extract_audio(input_file, output_format, start_time=0, duration=10):
    """从视频文件中提取音频片段"""
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}") as tmp_file:
            output_path = tmp_file.name
        
        # 使用ffmpeg提取音频
        (
            ffmpeg
            .input(input_file, ss=start_time, t=duration)
            .output(output_path, acodec='libmp3lame' if output_format == 'mp3' else 'pcm_s16le')
            .overwrite_output()
            .run(quiet=True)
        )
        
        return output_path
    except Exception as e:
        st.error(f"音频提取失败: {str(e)}")
        return None

def main():
    st.title("🎵 视频音频提取工具")
    st.markdown("从视频文件中提取音频片段 (支持MP4, MOV, MKV等格式)")
    
    # 文件上传区域
    uploaded_file = st.file_uploader(
        "上传视频文件",
        type=['mp4', 'mov', 'mkv', 'avi', 'flv', 'wmv']
    )
    
    if uploaded_file:
        # 保存上传的文件到临时位置
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            input_path = tmp_file.name
        
        # 显示视频信息
        st.video(uploaded_file)
        
        # 提取参数设置
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.number_input("开始时间 (秒)", min_value=0, value=0, step=1)
        with col2:
            duration = st.number_input("提取时长 (秒)", min_value=1, max_value=60, value=10, step=1)
        
        output_format = st.radio("输出音频格式", ['mp3', 'wav'])
        
        if st.button("🎧 提取音频"):
            with st.spinner("正在处理..."):
                # 提取音频
                output_path = extract_audio(
                    input_path,
                    output_format,
                    start_time=start_time,
                    duration=duration
                )
                
                if output_path:
                    # 读取提取的音频文件
                    with open(output_path, "rb") as f:
                        audio_bytes = f.read()
                    
                    # 显示音频播放器
                    st.audio(audio_bytes, format=f'audio/{output_format}')
                    
                    # 提供下载按钮
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    download_name = f"extracted_audio_{timestamp}.{output_format}"
                    
                    st.download_button(
                        label="下载音频",
                        data=audio_bytes,
                        file_name=download_name,
                        mime=f"audio/{output_format}"
                    )
                    
                    # 清理临时文件
                    os.unlink(output_path)
                
                # 清理上传的临时文件
                os.unlink(input_path)

if __name__ == "__main__":
    main()