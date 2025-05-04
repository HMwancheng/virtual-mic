import sounddevice as sd
import sys

def audio_loop():
    """极简音频转发核心"""
    def callback(indata, outdata, _, __, ___):
        outdata[:] = indata  # 原生Python实现，避免numpy依赖
    
    with sd.Stream(
        channels=1,
        callback=callback,
        samplerate=44100,
        blocksize=1024
    ):
        print("🎤 虚拟麦克风运行中...")
        while True: sd.sleep(1000)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list-devices":
        print("\n可用音频设备：")
        for i, dev in enumerate(sd.query_devices()):
            print(f"{i}: {dev['name']} (输入:{dev['max_input_channels']} 输出:{dev['max_output_channels']})")
    else:
        audio_loop()
