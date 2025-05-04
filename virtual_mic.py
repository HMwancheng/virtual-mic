import sounddevice as sd
import numpy as np

def callback(indata, outdata, frames, time, status):
    outdata[:] = indata  # 转发麦克风数据到输出

print("🎤 虚拟麦克风运行中... 按 Ctrl+C 停止")
with sd.Stream(
    channels=1,          # 单声道
    callback=callback,
    samplerate=44100,    # 采样率
):
    sd.sleep(1000000)    # 持续运行
