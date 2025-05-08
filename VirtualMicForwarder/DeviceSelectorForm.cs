using NAudio.CoreAudioApi;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Forms;

namespace VirtualMicForwarder
{
    public partial class DeviceSelectorForm : Form
    {
        // 修复可空性警告
        public MMDevice? SelectedDevice { get; private set; }

        public DeviceSelectorForm(DataFlow flowType)
        {
            // 手动初始化控件（替代InitializeComponent）
            BuildUI(flowType);
        }

        private void BuildUI(DataFlow flowType)
        {
            // 获取设备列表
            var devices = new MMDeviceEnumerator()
                .EnumerateAudioEndPoints(flowType, DeviceState.Active)
                .ToList();  // 修复ToArray错误

            // 创建列表控件
            var listBox = new ListBox
            {
                Dock = DockStyle.Fill,
                DisplayMember = "FriendlyName"
            };
            listBox.Items.AddRange(devices.ToArray());

            // 选择事件处理
            listBox.SelectedIndexChanged += (s, e) => 
            {
                SelectedDevice = listBox.SelectedItem as MMDevice;
            };

            // 确认按钮
            var okButton = new Button
            {
                Text = "OK",
                Dock = DockStyle.Bottom
            };
            okButton.Click += (s, e) => DialogResult = DialogResult.OK;

            // 布局设置
            Controls.Add(listBox);
            Controls.Add(okButton);
            Size = new System.Drawing.Size(500, 400);
        }
    }
}
