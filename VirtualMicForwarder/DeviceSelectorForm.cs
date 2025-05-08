using NAudio.CoreAudioApi;
using System.Windows.Forms;

namespace VirtualMicForwarder
{
    public partial class DeviceSelectorForm : Form
    {
        public MMDevice SelectedDevice { get; private set; }

        public DeviceSelectorForm(DataFlow flowType)
        {
            InitializeComponent();

            var devices = new MMDeviceEnumerator()
                .EnumerateAudioEndPoints(flowType, DeviceState.Active);

            var listBox = new ListBox
            {
                Dock = DockStyle.Fill
            };
            listBox.Items.AddRange(devices.ToArray());
            listBox.SelectedIndexChanged += (s, e) => 
            {
                SelectedDevice = (MMDevice)listBox.SelectedItem;
            };

            var okButton = new Button
            {
                Text = "OK",
                Dock = DockStyle.Bottom
            };
            okButton.Click += (s, e) => DialogResult = DialogResult.OK;

            Controls.Add(listBox);
            Controls.Add(okButton);
            Height = 400;
        }
    }
}
