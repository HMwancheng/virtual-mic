import sounddevice as sd
import numpy as np

def print_devices():
    """打印所有可用的音频设备"""
    print("可用的音频设备：")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']} (输入通道: {device['max_input_channels']}, 输出通道: {device['max_output_channels']})")

def find_vb_cable():
    """查找VB-CABLE设备索引"""
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if "CABLE Input" in device["name"] and device["max_input_channels"] > 0:
            return i
    return None

print_devices()  # 打印可用设备

# 自动查找VB-CABLE设备
vb_cable_index = find_vb_cable()
if vb_cable_index is None:
    print("\n错误：未找到VB-CABLE设备！请确保已安装VB-CABLE驱动。")
    print("可以从 https://vb-audio.com/Cable/ 下载安装")
    exit(1)

# 获取默认输入设备(物理麦克风)
default_input = sd.default.device[0]

print(f"\n使用设备配置：")
print(f"输入设备: {sd.query_devices(default_input)['name']}")
print(f"输出设备(VB-CABLE): {sd.query_devices(vb_cable_index)['name']}")

def callback(indata, outdata, frames, time, status):
    """音频回调函数，将输入直接转发到输出"""
    if status:
        print(f"音频状态: {status}")
    outdata[:] = indata  # 转发音频数据

try:
    print("\n🎤 虚拟麦克风正在运行... (按Ctrl+C停止)")
    with sd.Stream(
        device=(default_input, vb_cable_index),  # 输入→输出设备
        channels=1,          # 单声道
        callback=callback,
        samplerate=44100,    # 采样率
        blocksize=1024       # 缓冲区大小
    ):
        while True:
            sd.sleep(1000)  # 持续运行
            
except KeyboardInterrupt:
    print("\n停止虚拟麦克风")
except Exception as e:
    print(f"发生错误: {e}")
