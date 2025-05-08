using System;
using System.Windows.Forms;

namespace VirtualMicForwarder
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            
            // 添加全局异常处理
            Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
            Application.ThreadException += (s, e) => 
                ShowError("Global Exception", e.Exception);
            AppDomain.CurrentDomain.UnhandledException += (s, e) => 
                ShowError("Domain Exception", e.ExceptionObject as Exception);

            Application.Run(new MainForm());
        }

        static void ShowError(string title, Exception? ex)
        {
            MessageBox.Show($"Critical Error: {ex?.Message ?? "Unknown"}", title,
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
