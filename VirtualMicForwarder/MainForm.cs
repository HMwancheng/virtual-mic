using NAudio.CoreAudioApi;
using NAudio.Wave;
using System;
using System.Drawing;
using System.Windows.Forms;

namespace VirtualMicForwarder
{
    public partial class MainForm : Form
    {
        private NotifyIcon? trayIcon;
        private ContextMenuStrip? trayMenu;
        private WasapiCapture? audioInput;
        private WasapiOut? audioOutput;
        private bool isExiting = false; // 新增退出状态标志

        public MainForm()
        {
            InitializeTrayIcon();
            InitializeAudioDevices();
            Application.ApplicationExit += OnApplicationExit; // 注册全局退出事件
        }

        private void InitializeTrayIcon()
        {
            trayMenu = new ContextMenuStrip();
            trayMenu.Items.Add("Select Input", null, OnSelectInput);
            trayMenu.Items.Add("Exit", null, OnExit);

            trayIcon = new NotifyIcon
            {
                Text = "Virtual Mic Forwarder",
                Icon = new Icon(SystemIcons.Application, 40, 40),
                ContextMenuStrip = trayMenu,
                Visible = true
            };

            // 添加双击打开事件
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
                    ShowWarning("No active input devices found!");
                    return;
                }

                StartForwarding(inputDevices[0]);
            }
            catch (Exception ex)
            {
                ShowError($"Audio initialization failed: {ex.Message}");
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
                        ShowError($"Audio processing error: {ex.Message}");
                    }
                };

                audioInput.StartRecording();
                audioOutput.Play();
            }
            catch (Exception ex)
            {
                ShowError($"Failed to start audio forwarding: {ex.Message}");
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
            trayIcon?.Visible = false;
            trayIcon?.Dispose();
        }

        protected override void OnLoad(EventArgs e)
        {
            Visible = false;
            ShowInTaskbar = false;
            base.OnLoad(e);
        }

        // 防止窗体关闭导致程序退出
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
            MessageBox.Show(message, "Warning", 
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }

        private void ShowError(string message)
        {
            MessageBox.Show(message, "Error", 
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
