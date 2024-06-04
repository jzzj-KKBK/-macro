import ctypes
import json  # 用于保存导出我们记录的操作
import os  # 用于文件操作
import threading  # 由于键盘和鼠标事件的监听都是阻塞的,所以用两个线程实现
import time  # 用于记录每一项操作的时间
import tkinter  # 绘制操作界面
from tkinter import messagebox
import pynput  # 用于记录用户事件
def unicode_convert(input_data):
    # 将unicode转换成str
    if isinstance(input_data, dict):
        return {unicode_convert(key): unicode_convert(value) for key, value in input_data.iteritems()}
    elif isinstance(input_data, list):
        return [unicode_convert(element) for element in input_data]
    elif isinstance(input_data, str):
        return input_data
    else:
        return input_data


def ExecuteCommandsFile(path):
    # 如果命令行传入了参数,则使用命令行参数,否则提示用户输入,此变量表示操作记录文件的路径
    # 第二个不是:,也就代表路径是相对路径
    path = unicode_convert(path)
    if path[2] != ":":
        # 将其解析为从本文件开始的路径
        path = os.path.join(os.path.dirname(__file__), path)

    # 打开文件
    with open(path) as f:
        # 将记录的命令写入命令列表
        command_read = json.loads(f.read())
    command_read = unicode_convert(command_read)
    # 创建鼠标和键盘的执行器,用于模拟键盘和鼠标的操作
    mouse = pynput.mouse.Controller()
    keyboard = pynput.keyboard.Controller()
    # 鼠标的三个按钮
    buttons = {
        "Button.left": pynput.mouse.Button.left,
        "Button.right": pynput.mouse.Button.right,
    }
    # 开始后已经经过的时间
    sTime = 0
    # 执行每一条记录
    for command in command_read:
        # 如果是点击记录
        print(command[0])
        print(command[1])
        print(command[2])
        # 如果是单击
        if command[0] == "click":
            # 将鼠标移动到记录中的位置
            mouse.position = (command[1][0], command[1][1])
            # 等待一下
            time.sleep(0.1)
            # 点击
            mouse.click(buttons[command[1][2]])
        # 如果是双击
        elif command[0] == "double-click":
            # 将鼠标移动到记录中的位置
            mouse.position = (command[1][0], command[1][1])
            # 等待一下
            time.sleep(0.1)
            # 双击
            mouse.click(buttons[command[1][2]], 2)
        # 如果是按键按下
        elif command[0] == "press":
            # 如果是特殊按键,会记录成Key.xxx,这里判断是不是特殊按键
            if command[1][0][:3] == "Key":
                # 按下按键
                keyboard.press(eval(command[1][0], {}, {
                    "Key": pynput.keyboard.Key
                }))
            else:
                # 如果是普通按键,直接按下
                if "<255>" == command[1][0]:
                    continue
                print(command[1][0])
                # print(command[1][0].split("'")[1])
                # keyboard.press(command[1][0].split("'")[1])
                keyboard.press(command[1][0])
        # 如果是按键释放
        elif command[0] == "release":
            # 如果是特殊按键
            if command[1][0][:3] == "Key":
                # 按下按键
                keyboard.release(eval(command[1][0], {}, {
                    "Key": pynput.keyboard.Key
                }))
            else:
                # 普通按键直接按下
                if "<255>" == command[1][0]:
                    continue
                print(command[1][0])
                # print(command[1][0].split("'")[1])
                # keyboard.release(command[1][0].split("'")[1])
                keyboard.release(command[1][0])
        # command[2]代表此操作距离开始操作所经过的时间,用它减去已经经过的时间就是距离下一次操作的时间
        time.sleep(command[2] - sTime)
        # 更新时间
        sTime = command[2]


def on_key_press(key):  # 当按键按下时记录
    if key == pynput.keyboard.Key.esc:  # 如果是esc
        global isRunning
        isRunning = False  # 通知监听鼠标的线程
        mouse = pynput.mouse.Controller()  # 获取鼠标的控制器
        mouse.click(pynput.mouse.Button.left)  # 通过模拟点击鼠标以执行鼠标的线程,然后退出监听.
        return False  # 监听函数return False表示退出监听12
    command_list.append((
        "press",  # 操作模式
        (str(key).strip("'"),),  # 具体按下的键,传进来的参数并不是一个字符串,而是一个对象,如果按下的是普通的键,会记录下键对应的字符,否则会使一个"Key.xx"的字符串
        round(time.time() - startTime,2)  # 操作距离程序开始运行的秒数
    ))


def on_key_release(key):  # 但按键松开时记录
    command_list.append((
        "release",  # 操作模式
        (str(key).strip("'"),),  # 键信息,参见on_key_press中的相同部分
        round(time.time() - startTime,2)  # 操作距离程序开始运行的秒数
    ))

def on_mouse_click(x, y, button, pressed):
    global mouse_x_old
    global mouse_y_old
    global mouse_t_old
    if not isRunning:  # 如果已经不在运行了
        return False  # 退出监听
    if not pressed:  # 如果是松开事件
        return True  # 不记录

    if mouse_x_old == x and mouse_y_old == y:
        if time.time() - mouse_t_old > 0.2:  # 如果两次点击时间小于0.3秒就会判断为双击 否则就是单击
            command_list.append((
                "click",  # 操作模式
                (x, y, str(button)),  # 分别是鼠标的坐标和按下的按键
                round(time.time() - startTime,2)  # 操作距离程序开始运行的秒数
            ))
        else:
            command_list.pop(0)  # 删除前一个
            command_list.append((
                "double-click",  # 操作模式
                (x, y, str(button)),  # 分别是鼠标的坐标和按下的按键
                round(time.time() - startTime,2)  # 操作距离程序开始运行的秒数
            ))
    else:
        command_list.append((
            "click",  # 操作模式
            (x, y, str(button)),  # 分别是鼠标的坐标和按下的按键
            round(time.time() - startTime,2)  # 操作距离程序开始运行的秒数
        ))
    mouse_x_old = x
    mouse_y_old = y
    mouse_t_old = time.time()
def on_scroll(x, y, dx, dy):
    command_list.append((
            "updown",  # 操作模式
            (dy),  # 分别是鼠标的坐标和按下的按键
            round(time.time() - startTime,2)  # 操作距离程序开始运行的秒数
        ))

def start_key_listen():  # 用于开始按键的监听
    # 进行监听
    with pynput.keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as listener:
        listener.join()
def start_mouse_listen():  # 用于开始鼠标的监听
    # 进行监听
    with pynput.mouse.Listener(on_click=on_mouse_click,on_scroll=on_scroll) as listener:
        listener.join()


def toFile(command_list, path):  # 保存为文件,参数分别为操作记录和保存位置
    with open(path, "w") as f:
        f.write(json.dumps(command_list))  # 使用json格式写入

PROCESS_PER_MONITOR_DPI_AWARE = 2  # 解决由于屏幕分辨率缩放导致的，pynput监听鼠标位置不准的问题
ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)

command_list = []  # 用来存储用户的操作
command_read = []  # 用来读取录制的操作
isRunning = True  # 是否在运行,用于实现在按esc后退出的功能
startTime = 0  # 开始时间,会在之后main函数中进行初始化
mouse_x_old = 0
mouse_y_old = 0
mouse_t_old = 0


# 插入录制部分代码

# 插入执行部分代码
def keyboard(kkey):
    if kkey == "Key.ctrl_l":
        return "^"
    elif kkey == "Key.space":
        return " "
    elif kkey == "Key.enter":
        return "{enter}"
    elif kkey == "caps_lock":
        return "{CAPSLOCK}"
    elif kkey == "Key.backspace":
        return "{backspace}"
    elif kkey == "Key.shift":
        return "+"
    elif kkey == "Key.cmd":
        return "(^{esc})"
    elif kkey == "Key.alt":
        return "%"
    elif kkey == "\\x03":
        return "^c"
    elif kkey == "\\x18":
        return "^x"
    elif kkey == "\\x16":
        return "^v"
    elif kkey == "Key.left":
        return "{left}"
    elif kkey == "Key.right":
        return "{right}"
    elif kkey == "Key.up":
        return "{up}"
    elif kkey == "Key.down":
        return '{down}'
    else:
        return kkey

class TKDemo:
    def __init__(self):
        self.top = tkinter.Tk()
        self.top.title('宏录制工具')
        self.top.geometry('300x600')
        #self.top.iconbitmap('logo01.ico')
        frame1 = tkinter.Frame(self.top)
        frame1.pack(side='top')
        l1 = tkinter.Label(frame1,
                           text='【1----录制操作】\n注意：按Esc退出录制，暂不支持键盘组合键')
        l1.pack()
        b1 = tkinter.Button(frame1,
                            text='录制',
                            width=15, height=2,
                            command=self.recordOp)
        b1.pack()
        frame3 = tkinter.Frame(self.top)
        frame3.pack(side='top')
        l3 = tkinter.Label(frame1,
                            text='\n\n【2----vbs】\n将程序转换成VBS并可以在装有office的电脑上使用\n使用灵活、方便')
        l3.pack()
        b3 = tkinter.Button(frame1,
                            text='编译成VBS',
                            width=15, height=2,
                            command=self.vbs)
        b3.pack()
        self.cc = tkinter.StringVar()
        e2 = tkinter.Entry(frame3, textvariable=self.cc)
        l4 = tkinter.Label(frame1,
        text='请在下列框内输入时间系数time乘上的数字')
        l4.pack()
        e2.pack()

        frame2 = tkinter.Frame(self.top)
        frame2.pack(side='bottom')
        l2 = tkinter.Label(frame2,
                           text='【3----执行操作】')
        l2.pack()
        b2 = tkinter.Button(frame2,
                            text='执行',
                            width=15, height=2,
                            command=self.execOp)
        b2.pack()
        l3 = tkinter.Label(frame2,
                           text='请输入执行次数，默认为1次')
        l3.pack()
        self.count = tkinter.StringVar()
        e1 = tkinter.Entry(frame2, textvariable=self.count)
        e1.pack()
        self.top.mainloop()

    def vbs(self):
        loop = 0
        d = 0
        with open('commands.json', 'r') as file:
            content = file.read()
            list = json.loads(content)
            vbs_code = """  Set WshShell = WScript.CreateObject("WScript.Shell")
Set mouse=New SetMouse"""
            xs = self.cc.get()
            for i in list:
                n = i[0]
                time = int((int(i[2] * 1000) - int(d * 1000)+5)*eval(xs))
                if time <= 0 :
                    time = 1
                d = i[2]
                if n == "click":
                    m = i[1][2]
                    vbs_code = vbs_code + '\nWScript.Sleep ' + str(time)
                    if m == "Button.left":
                        vbs_code = vbs_code + "\n" + "mouse.move " + str(i[1][0]) + "," + str(
                            i[1][1]) + '\nmouse.clik "LEFT"'
                    elif m == "Button.right":
                        vbs_code = vbs_code + "\n" + "mouse.move " + str(i[1][0]) + "," + str(
                            i[1][1]) + '\nmouse.clik "RIGHT"'
                elif n == "double-click":
                    vbs_code = vbs_code + "\n" + "mouse.move " + str(i[1][0]) + "," + str(
                        i[1][1]) + '\nmouse.clik "DBCLICK"'
                elif n == "press" and loop == 1:
                    vbs_code = vbs_code + '\nWScript.Sleep ' + str(time)
                    vbs_code = vbs_code + '\nWshShell.sendKeys "' + "+" + str(keyboard(i[1][0])) + '"'
                elif n == "press":
                    if i[1][0]=="Key.shift":
                        loop = 1
                    else:
                        vbs_code = vbs_code + '\nWScript.Sleep ' + str(time)
                        vbs_code = vbs_code + '\nWshShell.sendKeys "' + str(keyboard(i[1][0])) + '"'
                elif n == "release":
                    if i[1][0] == "Key.shift":
                        loop = 0
            vbss = """
Class SetMouse
private S
private xls, wbk, module1
private reg_key, xls_code, x, y
Private Sub Class_Initialize()
Set xls = CreateObject("Excel.Application") 
Set S = CreateObject("wscript.Shell")
reg_key = "HKEY_CURRENT_USER\Software\Microsoft\Office\$\Excel\Security\AccessVBOM"
reg_key = Replace(reg_key, "$", xls.Version)
S.RegWrite reg_key, 1, "REG_DWORD"
xls_code = _
"Private Type POINTAPI : X As Long : Y As Long : End Type" & vbCrLf & _
"Private Declare Function SetCursorPos Lib ""user32"" (ByVal x As Long, ByVal y As Long) As Long" & vbCrLf & _
"Private Declare Function GetCursorPos Lib ""user32"" (lpPoint As POINTAPI) As Long" & vbCrLf & _
"Private Declare Sub mouse_event Lib ""user32"" Alias ""mouse_event"" " _
& "(ByVal dwFlags As Long, ByVal dx As Long, ByVal dy As Long, ByVal cButtons As Long, ByVal dwExtraInfo As Long)" & vbCrLf & _
"Public Function getx() As Long" & vbCrLf & _
"Dim pt As POINTAPI : GetCursorPos pt : getx = pt.X" & vbCrLf & _
"End Function" & vbCrLf & _
"Public Function gety() As Long" & vbCrLf & _
"Dim pt As POINTAPI: GetCursorPos pt : gety = pt.Y" & vbCrLf & _
"End Function"
Set wbk = xls.Workbooks.Add 
Set module1 = wbk.VBProject.VBComponents.Add(1)
module1.CodeModule.AddFromString xls_code 
End Sub
Private Sub Class_Terminate
xls.DisplayAlerts = False
wbk.Close
xls.Quit
End Sub
Public Sub getpos( x, y) 
x = xls.Run("getx") 
y = xls.Run("gety") 
End Sub
Public Sub move(x,y)
xls.Run "SetCursorPos", x, y
End Sub
Public Sub clik(keydown)
Select Case UCase(keydown)
Case "LEFT"
xls.Run "mouse_event", &H2 + &H4, 0, 0, 0, 0
Case "RIGHT"
xls.Run "mouse_event", &H8 + &H10, 0, 0, 0, 0
Case "MIDDLE"
xls.Run "mouse_event", &H20 + &H40, 0, 0, 0, 0
Case "DBCLICK"
xls.Run "mouse_event", &H2 + &H4, 0, 0, 0, 0
xls.Run "mouse_event", &H2 + &H4, 0, 0, 0, 0
End Select
End Sub
End Class
msgbox "OK",0,"END"
"""
            output_file = "script.vbs"
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(vbs_code)
                file.write(vbss)
            print(f"VBScript代码已写入文件：{output_file}")

        return 0

    def recordOp(self):
        self.top.iconify()  # 窗口隐藏
        global startTime
        startTime = time.time()  # 初始化开始时间
        key_listen_thread = threading.Thread(target=start_key_listen)  # 创建用于监听按键的线程
        mouse_listen_thread = threading.Thread(target=start_mouse_listen)  # 创建用于监听鼠标的线程
        # 运行线程
        key_listen_thread.start()
        mouse_listen_thread.start()
        # 等待线程结束,也就是等待用户按下esc
        key_listen_thread.join()
        mouse_listen_thread.join()
        # 记录成功之后执行下列操作
        toFile(command_list, "./commands.json")  # 保存文件

        global isRunning
        isRunning = True  # 初始化记录状态
        command_list.clear()  # 清空列表
        self.top.deiconify()  # 窗口显现
        print("记录成功！")
        tkinter.messagebox.showinfo('提示', '记录成功！')

    def execOp(self):
        self.top.iconify()  # 窗口隐藏
        path = 'commands.json'
        count = self.count.get()
        if count.isdigit():
            for i in range(int(count)):
                ExecuteCommandsFile(path)
            print("执行成功%d次!" % (int(count)))
            tkinter.messagebox.showinfo('提示', "执行完毕！\n共%d次！" % (int(count)))
        elif len(count) == 0:
            ExecuteCommandsFile(path)
            print("执行成功1次!")
            tkinter.messagebox.showinfo('提示', '执行完毕！\n共1次！')
        else:
            print("执行失败！请键入数字")
            tkinter.messagebox.showerror('提示', '执行失败！\n请键入数字！')
        self.top.deiconify()  # 窗口显现


def main():  # 主函数
    TKDemo()


if __name__ == "__main__":
    main()