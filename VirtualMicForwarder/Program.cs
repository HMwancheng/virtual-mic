using System;
using System.Diagnostics;
using System.Security.Principal;
using System.Windows.Forms;

namespace VirtualMicForwarder
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            // 管理员权限检查
            if (!IsRunningAsAdmin())
            {
                RestartAsAdmin();
                return;
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
            Application.ThreadException += (s, e) => ShowError("全局异常", e.Exception);
            AppDomain.CurrentDomain.UnhandledException += (s, e) => ShowError("域异常", e.ExceptionObject as Exception);
            
            Application.Run(new MainForm());
        }

        private static bool IsRunningAsAdmin()
        {
            using var identity = WindowsIdentity.GetCurrent();
            var principal = new WindowsPrincipal(identity);
            return principal.IsInRole(WindowsBuiltInRole.Administrator);
        }

        private static void RestartAsAdmin()
        {
            var exePath = Process.GetCurrentProcess().MainModule.FileName;
            var startInfo = new ProcessStartInfo
            {
                FileName = exePath,
                UseShellExecute = true,
                Verb = "runas"
            };

            try
            {
                Process.Start(startInfo);
            }
            catch (System.ComponentModel.Win32Exception)
            {
                MessageBox.Show("必须使用管理员权限运行本程序！", 
                    "权限错误", 
                    MessageBoxButtons.OK, 
                    MessageBoxIcon.Error);
            }
            Environment.Exit(0);
        }

        static void ShowError(string title, Exception ex)
        {
            MessageBox.Show($"严重错误：{ex?.Message ?? "未知错误"}", 
                title, 
                MessageBoxButtons.OK, 
                MessageBoxIcon.Error);
        }
    }
}
