using NAudio.CoreAudioApi;
using NAudio.Wave;
using System;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace VirtualMicForwarder
{
    public partial class MainForm : Form
    {
        private NotifyIcon? trayIcon;
        private ContextMenuStrip? trayMenu;
        private WasapiCapture? audioInput;
        private WasapiOut? audioOutput;
        private bool isExiting = false;

        // COM接口声明
        [ComImport, Guid("1CB9AD4C-DBFA-4c32-B178-C2F568A703B2")]
        private class AudioClient { }

        public MainForm()
        {
            InitializeTrayIcon();
            InitializeAudioDevices();
            Application.ApplicationExit += OnApplicationExit;
        }

        private void InitializeTrayIcon()
        {
            trayMenu = new ContextMenuStrip();
            trayMenu.Items.Add("选择输入设备", null, OnSelectInput);
            trayMenu.Items.Add("退出", null, OnExit);

            trayIcon = new NotifyIcon
            {
                Text = "虚拟麦克风转发器",
                Icon = new Icon(SystemIcons.Application, 40, 40),
                ContextMenuStrip = trayMenu,
                Visible = true
            };
            trayIcon.DoubleClick += (s, e) => Visible = !Visible;
        }

        private void InitializeAudioDevices()
        {
            try
            {
                var inputDevices = new MMDeviceEnumerator()
                    .EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);

                if (inputDevices.Count == 0)
                {
                    ShowWarning("未找到可用的输入设备！");
                    return;
                }

                StartForwarding(inputDevices[0]);
            }
            catch (COMException ex) when (ex.HResult == -2147221164)
            {
                ShowError("音频组件未注册，请安装VC++运行库！");
            }
            catch (Exception ex)
            {
                ShowError($"初始化失败：{ex.Message}");
            }
        }

        private void StartForwarding(MMDevice inputDevice)
        {
            try
            {
                audioInput?.StopRecording();
                audioOutput?.Stop();
                audioInput?.Dispose();
                audioOutput?.Dispose();

                // 显式初始化COM组件
                var audioClient = inputDevice.AudioClient;
                audioClient.Initialize(
                    AudioClientShareMode.Shared,
                    AudioClientStreamFlags.None,
                    10000000,  // 10秒缓冲
                    0,
                    audioClient.MixFormat,
                    Guid.Empty);

                audioInput = new WasapiCapture(inputDevice);
                audioOutput = new WasapiOut(AudioClientShareMode.Shared, 100);

                var provider = new BufferedWaveProvider(audioInput.WaveFormat);
                audioOutput.Init(provider);

                audioInput.DataAvailable += (s, e) =>
                {
                    try
                    {
                        provider.AddSamples(e.Buffer, 0, e.BytesRecorded);
                    }
                    catch (Exception ex)
                    {
                        ShowError($"音频处理错误：{ex.Message}");
                    }
                };

                audioInput.StartRecording();
                audioOutput.Play();
            }
            catch (COMException ex) when (ex.HResult == -2147221164)
            {
                ShowError("COM组件错误，请执行以下操作：\n1. 安装VC++运行库\n2. 运行修复脚本");
            }
            catch (Exception ex)
            {
                ShowError($"启动失败：{ex.Message}");
            }
        }

        private void OnSelectInput(object? sender, EventArgs e)
        {
            using var dialog = new DeviceSelectorForm(DataFlow.Capture);
            if (dialog.ShowDialog() == DialogResult.OK && dialog.SelectedDevice != null)
            {
                StartForwarding(dialog.SelectedDevice);
            }
        }

        private void OnExit(object? sender, EventArgs e)
        {
            if (!isExiting)
            {
                isExiting = true;
                Application.Exit();
            }
        }

        private void OnApplicationExit(object? sender, EventArgs e)
        {
            audioInput?.StopRecording();
            audioOutput?.Stop();
            audioInput?.Dispose();
            audioOutput?.Dispose();

            if (trayIcon != null)
            {
                trayIcon.Visible = false;
                trayIcon.Dispose();
            }
        }

        protected override void OnLoad(EventArgs e)
        {
            Visible = false;
            ShowInTaskbar = false;
            base.OnLoad(e);
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            if (!isExiting)
            {
                e.Cancel = true;
                Visible = false;
            }
            base.OnFormClosing(e);
        }

        private void ShowWarning(string message)
        {
            MessageBox.Show(message, "警告", 
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }

        private void ShowError(string message)
        {
            MessageBox.Show(message, "错误", 
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
