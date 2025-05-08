using NAudio.CoreAudioApi;
using NAudio.Wave;
using System;
using System.Drawing;
using System.Windows.Forms;

namespace VirtualMicForwarder
{
    public partial class MainForm : Form
    {
        private NotifyIcon trayIcon;
        private ContextMenuStrip trayMenu;
        private WasapiCapture audioInput;
        private WasapiOut audioOutput;

        public MainForm()
        {
            InitializeTrayIcon();
            InitializeAudioDevices();
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
        }

        private void InitializeAudioDevices()
        {
            // 自动选择第一个可用输入设备
            var inputDevices = new MMDeviceEnumerator()
                .EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);
            if (inputDevices.Count > 0)
            {
                StartForwarding(inputDevices[0]);
            }
        }

        private void StartForwarding(MMDevice inputDevice)
        {
            audioInput?.StopRecording();
            audioOutput?.Stop();

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

        private void OnSelectInput(object sender, EventArgs e)
        {
            var dialog = new DeviceSelectorForm(DataFlow.Capture);
            if (dialog.ShowDialog() == DialogResult.OK)
            {
                StartForwarding(dialog.SelectedDevice);
            }
        }

        private void OnExit(object sender, EventArgs e)
        {
            audioInput?.Dispose();
            audioOutput?.Dispose();
            trayIcon.Dispose();
            Application.Exit();
        }

        protected override void OnLoad(EventArgs e)
        {
            Visible = false;
            ShowInTaskbar = false;
            base.OnLoad(e);
        }
    }
}
