using NAudio.CoreAudioApi;
using NAudio.Wave;
using System;
using System.Drawing;
using System.Windows.Forms;

namespace VirtualMicForwarder
{
    public partial class MainForm : Form
    {
        // 可空字段声明
        private NotifyIcon? trayIcon;
        private ContextMenuStrip? trayMenu;
        private WasapiCapture? audioInput;
        private WasapiOut? audioOutput;

        public MainForm()
        {
            InitializeTrayIcon();
            InitializeAudioDevices();
        }

        private void InitializeTrayIcon()
        {
            trayMenu = new ContextMenuStrip();
            
            // 添加菜单项（带图标占位符）
            trayMenu.Items.Add("Select Input", null, OnSelectInput);
            trayMenu.Items.Add("Exit", null, OnExit);

            trayIcon = new NotifyIcon
            {
                Text = "Virtual Mic Forwarder",
                Icon = new Icon(SystemIcons.Application, 40, 40),
                ContextMenuStrip = trayMenu,
                Visible = true
            };
        }

        private void InitializeAudioDevices()
        {
            // 安全检查设备存在性
            var inputDevices = new MMDeviceEnumerator()
                .EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);
            
            if (inputDevices.Count > 0)
            {
                StartForwarding(inputDevices[0]);
            }
            else
            {
                MessageBox.Show("No active input devices found!", "Warning", 
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        private void StartForwarding(MMDevice inputDevice)
        {
            // 清理旧资源
            audioInput?.StopRecording();
            audioOutput?.Stop();
            audioInput?.Dispose();
            audioOutput?.Dispose();

            // 初始化新设备
            audioInput = new WasapiCapture(inputDevice);
            audioOutput = new WasapiOut(AudioClientShareMode.Shared, 100);

            var provider = new BufferedWaveProvider(audioInput.WaveFormat);
            audioOutput.Init(provider);

            audioInput.DataAvailable += (s, e) =>
            {
                provider.AddSamples(e.Buffer, 0, e.BytesRecorded);
            };

            audioInput.StartRecording();
            audioOutput.Play();
        }

        // 修改参数类型为可空
        private void OnSelectInput(object? sender, EventArgs e)
        {
            using var dialog = new DeviceSelectorForm(DataFlow.Capture);
            if (dialog.ShowDialog() == DialogResult.OK && dialog.SelectedDevice != null)
            {
                StartForwarding(dialog.SelectedDevice);
            }
        }

        // 修改参数类型为可空
        private void OnExit(object? sender, EventArgs e)
        {
            audioInput?.StopRecording();
            audioOutput?.Stop();
            audioInput?.Dispose();
            audioOutput?.Dispose();
            
            trayIcon?.Dispose();
            Application.Exit();
        }

        protected override void OnLoad(EventArgs e)
        {
            Visible = false;
            ShowInTaskbar = false;
            base.OnLoad(e);
        }

        // 重写Dispose方法确保资源释放
        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                audioInput?.Dispose();
                audioOutput?.Dispose();
                trayIcon?.Dispose();
                trayMenu?.Dispose();
            }
            base.Dispose(disposing);
        }
    }
}
