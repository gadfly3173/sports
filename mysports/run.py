import os
import sys
import tkinter as tk
import traceback

import win32api
import win32con
import win32gui
import win32gui_struct

from mysports.login import *
from mysports.no_free_run import no_free_run

Main = None


def run(account, password, rg=(2, 4), debug=False):
    try:
        print('try login...')
        userid, s, school = login(account, password)
        print('login successfully')
    except Exception as e:
        traceback.print_exc()
        print('login failed')

    try:
        print('try run...')
        dis = no_free_run(userid, s, school=school, rg=rg, debug=debug)
        print('run %s km successfully !\n' % dis)
    except Exception as e:
        traceback.print_exc()
        print('run failed')


class SysTrayIcon(object):
    QUIT = 'QUIT'
    SPECIAL_ACTIONS = [QUIT]
    FIRST_ID = 1314

    def __init__(self,
                 icon,
                 hover_text,
                 menu_options,
                 on_quit=None,
                 default_menu_index=None,
                 window_class_name=None,):
        self.icon = icon
        self.hover_text = hover_text
        self.on_quit = on_quit

        menu_options = menu_options + (('退出', None, self.QUIT),)
        self._next_action_id = self.FIRST_ID
        self.menu_actions_by_id = set()
        self.menu_options = self._add_ids_to_menu_options(list(menu_options))
        self.menu_actions_by_id = dict(self.menu_actions_by_id)
        del self._next_action_id

        self.default_menu_index = (default_menu_index or 0)
        self.window_class_name = window_class_name or "SysTrayIconPy"

        message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): self.refresh_icon,
                       win32con.WM_DESTROY: self.destroy,
                       win32con.WM_COMMAND: self.command,
                       win32con.WM_USER+20: self.notify, }
        # 注册窗口类。
        window_class = win32gui.WNDCLASS()
        window_class.hInstance = win32gui.GetModuleHandle(None)
        window_class.lpszClassName = self.window_class_name
        window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        window_class.hbrBackground = win32con.COLOR_WINDOW
        window_class.lpfnWndProc = message_map  # 也可以指定wndproc.
        self.classAtom = win32gui.RegisterClass(window_class)

    def show_icon(self):
        # 创建窗口。
        hinst = win32gui.GetModuleHandle(None)
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(self.classAtom,
                                       self.window_class_name,
                                       style,
                                       0,
                                       0,
                                       win32con.CW_USEDEFAULT,
                                       win32con.CW_USEDEFAULT,
                                       0,
                                       0,
                                       hinst,
                                       None)
        win32gui.UpdateWindow(self.hwnd)
        self.notify_id = None
        self.refresh_icon()

        win32gui.PumpMessages()

    def show_menu(self):
        menu = win32gui.CreatePopupMenu()
        self.create_menu(menu, self.menu_options)
        #win32gui.SetMenuDefaultItem(menu, 1000, 0)

        pos = win32gui.GetCursorPos()
        # See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(menu,
                                win32con.TPM_LEFTALIGN,
                                pos[0],
                                pos[1],
                                0,
                                self.hwnd,
                                None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

    def destroy(self, hwnd, msg, wparam, lparam):
        if self.on_quit:
            self.on_quit(self)  # 运行传递的on_quit
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)  # 退出托盘图标

    def notify(self, hwnd, msg, wparam, lparam):
        if lparam == win32con.WM_LBUTTONDBLCLK:  # 双击左键
            pass  # self.execute_menu_option(self.default_menu_index + self.FIRST_ID)
        elif lparam == win32con.WM_RBUTTONUP:  # 单击右键
            self.show_menu()
        elif lparam == win32con.WM_LBUTTONUP:  # 单击左键
            nid = (self.hwnd, 0)
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
            win32gui.PostQuitMessage(0)  # 退出托盘图标
            if Main:
                Main.root.deiconify()
        return True

    def _add_ids_to_menu_options(self, menu_options):
        result = []
        for menu_option in menu_options:
            option_text, option_icon, option_action = menu_option
            if callable(option_action) or option_action in self.SPECIAL_ACTIONS:
                self.menu_actions_by_id.add((self._next_action_id, option_action))
                result.append(menu_option + (self._next_action_id,))
            else:
                result.append((option_text,
                               option_icon,
                               self._add_ids_to_menu_options(option_action),
                               self._next_action_id))
            self._next_action_id += 1
        return result

    def refresh_icon(self, **data):
        hinst = win32gui.GetModuleHandle(None)
        if os.path.isfile(self.icon):  # 尝试找到自定义图标
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst,
                                       self.icon,
                                       win32con.IMAGE_ICON,
                                       0,
                                       0,
                                       icon_flags)
        else:  # 找不到图标文件 - 使用默认值
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        if self.notify_id:
            message = win32gui.NIM_MODIFY
        else:
            message = win32gui.NIM_ADD
        self.notify_id = (self.hwnd,
                       0,
                       win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                       win32con.WM_USER+20,
                       hicon,
                       self.hover_text)
        win32gui.Shell_NotifyIcon(message, self.notify_id)

    def create_menu(self, menu, menu_options):
        for option_text, option_icon, option_action, option_id in menu_options[::-1]:
            if option_icon:
                option_icon = self.prep_menu_icon(option_icon)

            if option_id in self.menu_actions_by_id:
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                wID=option_id)
                win32gui.InsertMenuItem(menu, 0, 1, item)
            else:
                submenu = win32gui.CreatePopupMenu()
                self.create_menu(submenu, option_action)
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                hSubMenu=submenu)
                win32gui.InsertMenuItem(menu, 0, 1, item)

    def prep_menu_icon(self, icon):
        # 首先加载图标。
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
        hicon = win32gui.LoadImage(
            0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

        hdcBitmap = win32gui.CreateCompatibleDC(0)
        hdcScreen = win32gui.GetDC(0)
        hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
        hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
        # 填满背景。
        brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
        win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
        # "GetSysColorBrush返回缓存的画笔而不是分配新的画笔。"
        #  - 暗示没有DeleteObject
        # 画出图标
        win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x,
                            ico_y, 0, 0, win32con.DI_NORMAL)
        win32gui.SelectObject(hdcBitmap, hbmOld)
        win32gui.DeleteDC(hdcBitmap)

        return hbm

    def command(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        self.execute_menu_option(id)

    def execute_menu_option(self, id):
        menu_action = self.menu_actions_by_id[id]
        if menu_action == self.QUIT:
            win32gui.DestroyWindow(self.hwnd)
        else:
            menu_action(self)


class _Main:
    def main(self):
        #########################      tkinter界面设定      #####################################
        window = tk.Tk()
        window.title('一键快跑')
        window.geometry('450x400')

        # user information
        tk.Label(window, text='手机号: ').place(x=50, y=50)
        tk.Label(window, text='密码: ').place(x=50, y=90)

        var_usr_name = tk.StringVar()
        entry_usr_name = tk.Entry(window, textvariable=var_usr_name)
        entry_usr_name.place(x=160, y=50)
        var_usr_pwd = tk.StringVar()
        entry_usr_pwd = tk.Entry(window, textvariable=var_usr_pwd, show='*')
        entry_usr_pwd.place(x=160, y=90)

        def usr_login():
            run(entry_usr_name.get(), entry_usr_pwd.get())

        # login button
        btn_login = tk.Button(window, text='开始', command=usr_login)
        btn_login.place(x=70, y=130)

        listbox_print = tk.Listbox(window)
        listbox_print.place(x=10, y=180, width=420, height=150)

        class TextArea(object):

            def __init__(self):
                self.buffer = []

            def write(self, outStr):
                listbox_print.insert(tk.END, outStr.rstrip().replace("\n", ""))

        sys.stdout = TextArea()

        # window.mainloop()

        ###########################     开始托盘程序嵌入     #####################################
        self.root = window
        icons = os.getcwd()+r'\favicon.ico'
        # print(icons)
        hover_text = "一键快跑"  # 悬浮于图标上方时的提示
        menu_options = ()
        self.sysTrayIcon = SysTrayIcon(
            icons, hover_text, menu_options, on_quit=self.exit, default_menu_index=1)

        self.root.bind("<Unmap>", lambda event: self.Unmap()
                    if self.root.state() == 'iconic' else False)
        self.root.protocol('WM_DELETE_WINDOW', self.exit)
        self.root.resizable(0, 0)
        self.root.mainloop()

    def switch_icon(self, _sysTrayIcon, icons='favicon.ico'):
        _sysTrayIcon.icon = icons
        _sysTrayIcon.refresh_icon()
        # 点击右键菜单项目会传递SysTrayIcon自身给引用的函数，所以这里的_sysTrayIcon = self.sysTrayIcon

    def Unmap(self):
        self.root.withdraw()
        self.sysTrayIcon.show_icon()

    def exit(self, _sysTrayIcon=None):
        self.root.destroy()
        print('exit...')


if __name__ == '__main__':
    Main = _Main()
    Main.main()
