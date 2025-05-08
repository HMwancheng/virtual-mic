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
            // 新增管理员权限检查
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

        // 新增权限检查方法
        private static bool IsRunningAsAdmin()
        {
            using var identity = WindowsIdentity.GetCurrent();
            var principal = new WindowsPrincipal(identity);
            return principal.IsInRole(WindowsBuiltInRole.Administrator);
        }

        // 新增提权启动方法
        private static void RestartAsAdmin()
        {
            var exePath = Process.GetCurrentProcess().MainModule.FileName;
            var startInfo = new ProcessStartInfo
            {
                FileName = exePath,
                UseShellExecute = true,
                Verb = "runas" // 请求管理员权限
            };

            try
            {
                Process.Start(startInfo);
            }
            catch (System.ComponentModel.Win32Exception)
            {
                MessageBox.Show("必须使用管理员权限运行本程序！", "权限错误", 
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            Environment.Exit(0);
        }

        // 错误显示方法保持不变
        static void ShowError(string title, Exception ex) { /* 原有代码 */ }
    }
}
