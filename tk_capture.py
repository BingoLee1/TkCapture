# encoding=utf-8
# Copyright 2023-2024 Bingo(LiBin). All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
A lightweight screenshot and screen recording tool developed based on python tkinter.
"""
import os
import time
import json
import shutil
import threading
import pyautogui
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageGrab, ImageTk, ImageDraw


class Style:
    """
    global settings
    """
    version = '2.0.1'
    font = '黑体'   # 'Sans Serif'
    tool_bg = 'Snow'
    shot_types = ('PNG', 'GIF')
    settings_file = 'settings.json'
    theme_color = 'Lime'            # 默认主题色
    lines_color = 'Red'             # 截屏X Y辅助线颜色
    theme_colors = ['Lime', 'Cyan', 'Orange', 'HotPink']
    text_colors = ['Red', 'Yellow', 'Green', 'Blue', 'Black', 'Grey', 'Snow']
    rectangle_style = {}            # 截图矩形选框样式
    rectangle_limit = 30            # 矩形选框的X Y最小像素
    dot_offset = 7                  # 矩形选框调整圆点的半径
    default_cursor = 'arrow'        # 默认鼠标样式
    rect_cursor = 'crosshair'       # 选框开始时鼠标样式
    hand_cursor = 'hand2'           # 按钮提示鼠标样式
    dot_cursors = [
        'top_left_corner',          # 左上角鼠标样式
        'top_right_corner',         # 右上角鼠标样式
        'bottom_left_corner',       # 左下角鼠标样式
        'bottom_right_corner',      # 右下角鼠标样式
        'sb_h_double_arrow',        # 左边鼠标样式
        'sb_h_double_arrow',        # 右边鼠标样式
        'sb_v_double_arrow',        # 上边鼠标样式
        'sb_v_double_arrow',        # 下边鼠标样式
        'fleur'                     # 选框移动鼠标样式
    ]
    tool_window_size = {            # 工具栏的宽高
        "pic": (640, 70),
        "gif": (390, 40)
    }
    text_pt_values = ('10pt', '14pt', '18pt', '24pt', '36pt', '48pt', '60pt', '72pt', '96pt')
    mark_pi_values = ('1pi', '2pi', '4pi', '6pi', '8pi', '10pi', '12pi', '14pi')
    choose_color = text_colors[0]   # 工具栏选择的颜色
    choose_pt = text_pt_values[2]   # 工具栏选择的字号
    choose_pi = mark_pi_values[2]   # 工具栏选择的线框粗细（像素）
    mask_switch = True
    tips_switch = True
    tip = f'TkCapture v{version}\n\n%s'
    choose_lang = 'EN'
    languages = ('EN', 'CN')

    @classmethod
    def get_pt(cls):
        return int(cls.choose_pt.strip('pt'))

    @classmethod
    def get_pi(cls):
        return int(cls.choose_pi.strip('pi'))

    @classmethod
    def get_language(cls, key):
        return {
            'TIP': ('Tip:\n    Right click to exit.', "提示:\n    鼠标右键退出"),
            'SET': ("SET", "设置"),
            'Rectangle': ("Rectangle", "矩形"),
            'Circular': ("Circular", "椭圆"),
            'Line': ("Line", "直线"),
            'Arrow': ("Arrow", "箭头"),
            'Pen': ('Pen', "画笔"),
            'Text': ("Text", "文本"),
            'Mosaic': ("Mosaic", "马赛克"),
            'Revoke': ("Revoke", "撤销"),
            'Exit': ("Exit", "退出"),
            'Hang': ("Hang", "悬浮"),
            'To Clipboard': ("To Clipboard", "保存到剪切板"),
            'Theme': ("Theme", "主题色"),
            'Font Size': ('Font Size', "字体大小"),
            'Line Thickness': ('Line Thickness', "线条粗细"),
            'Save File': ('Save File', "保存文件"),
            'Start/Stop': ('Start/Stop', "开始/结束"),
            'Turn On Prompt': ('Turn On Prompt', "开启提示语"),
            'Turn Off Prompt': ('Turn Off Prompt', "关闭提示语"),
            'Outer Mask': ('Outer Mask', "外部遮罩"),
            'Too small range': ('Too small range', "截图区域过小"),
            'Language': ('Language', "语言")
        }.get(key, ('', ''))[cls.languages.index(cls.choose_lang)]

    @classmethod
    def load_settings(cls):
        if not os.path.isfile(Style.settings_file):
            cls.write_settings({})
        with open(cls.settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cls.theme_color = data.get('theme_color', 'Lime')
        cls.mask_switch = data.get('mask_switch', True)
        cls.tips_switch = data.get('tips_switch', True)
        cls.choose_pt = data.get('default_pt', '16pt')
        cls.choose_pi = data.get('default_pi', '4pi')
        cls.rectangle_style = {'width': 2, 'outline': cls.theme_color}
        cls.choose_lang = data.get('language', 'EN')

    @classmethod
    def write_settings(cls, data):
        with open(cls.settings_file, 'w+', encoding='utf-8') as f:
            f.write(json.dumps(data))


def create_thread(func, args=()):
    th = threading.Thread(target=func, args=args)
    th.daemon = True
    th.start()


class Event:
    """
    模拟tkinter event类，只需要x, y坐标
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Tip:
    """
    触碰控件后的提示小窗实现
    """
    _toplevel = None

    @classmethod
    def enter_tips(cls, widget, text, width=0, height=25):
        def enter(event):
            if cls._toplevel:
                return
            x, y, cx, cy = widget.bbox("insert")
            x = x + widget.winfo_rootx() + width
            y = y + widget.winfo_rooty() - height
            cls._toplevel = tw = tk.Toplevel(widget)
            tw.overrideredirect(True)
            tw.wm_attributes('-topmost', 1)
            tw.geometry("+%d+%d" % (x, y))
            tk.Label(tw, text=text, font=(Style.font, 10), justify='left', bg="Gray30", fg='Snow').pack(ipadx=1)

        def leave(event):
            if cls._toplevel:
                cls._toplevel.destroy()
                cls._toplevel = None

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)


class BaseButton(tk.Label):
    """
    通过Label模拟的按钮
    """

    def __init__(self, master=None, text=None, command=None, up=True,
                 bg='Snow', fg='Black', choo_fg='Snow', choo_bg='Black', *args, **kwargs):
        tk.Label.__init__(self, master, text=text, bg=bg, fg=fg, *args, **kwargs)
        self.command = command
        self.bg = bg
        self.fg = fg
        self.choo_fg = choo_fg
        self.choo_bg = choo_bg
        if up:
            self.bind("<ButtonRelease-1>", self.up)
        self.bind("<Button-1>", self._call)
        self.configure(cursor=Style.hand_cursor)
        self.state = 'normal'

    def _call(self, event=None):
        if self.state != 'disabled':
            self.down()
            if self.command:
                self.command()

    def down(self):
        self.configure(fg=self.choo_fg, bg=self.choo_bg)

    def up(self, event=None):
        # if self.state != 'disabled':
        self.configure(fg=self.fg, bg=self.bg)

    def configure(self, **kwargs):
        if 'state' in kwargs:
            self.state = kwargs['state']
            kwargs.update({'fg': 'Gray70' if self.state == 'disabled' else self.fg, 'bg': self.bg})
        super().configure(**kwargs)


class CanvasText:
    """
    canvas画布模拟的文本输入框，全透明背景
    """
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.cursor = 'ǀ'
        self.value = ''
        self.cursor_flag = True
        self.text = self.canvas.create_text(x + 5, y, text=self.cursor, font=(Style.font, Style.get_pt()),
                                            fill=Style.choose_color, anchor='nw')
        x2, y2 = x + 30, self.canvas.bbox(self.text)[3] + 5
        self.rect = self.canvas.create_rectangle(x, y, x2, y2, outline=Style.choose_color, dash=(5, 2))
        self.cursor_flash()

    def stop(self):
        self.cursor_flag = False

    def get(self):
        return self.value.strip(self.cursor).strip()

    def cursor_flash(self):
        if not self.cursor_flag:
            self.canvas.itemconfig(self.text, text=self.value.strip(self.cursor))
            return
        if self.value.endswith(self.cursor):
            text = self.value.strip(self.cursor)
        else:
            text = self.value + self.cursor
        self.value = text
        self.canvas.itemconfig(self.text, text=text)
        self.canvas.after(500, self.cursor_flash)

    def update_rect(self):
        pos = self.canvas.bbox(self.text)
        self.canvas.coords(self.rect, self.x, self.y, pos[2] + 10, pos[3] + 5)

    def input(self, event):
        old_text = self.canvas.itemcget(self.text, 'text').strip(self.cursor)

        if event.keysym == 'BackSpace':
            new_text = "%s" % old_text[:-1]
        elif event.keysym == 'Tab':
            new_text = "%s    " % old_text
        elif event.keysym == 'Return' or event.char == '\n':
            new_text = "%s\n" % old_text
        elif event.char.isprintable() and event.char:
            new_text = "%s%s" % (old_text, event.char)
        else:
            new_text = old_text

        self.canvas.itemconfig(self.text, text=new_text + self.cursor)
        self.value = new_text
        self.update_rect()


class UnFillRectangle(object):
    """
    用4个toplevel创建的矩形框，不会覆盖屏幕
    """
    def __init__(self, master, box, bd=2, bg='Red'):
        """
        box: 边框坐标
        bd: 外边框厚度
        bg: 边框颜色
        """
        x1, y1, x2, y2 = map(int, box)

        left = tk.Toplevel(master)
        left.configure(bg=bg)
        left.overrideredirect(True)
        left.wm_attributes("-topmost", 1)
        left.wm_geometry(f'{bd}x{y2 - y1 + bd}+{x1 - bd}+{y1}')

        right = tk.Toplevel(master)
        right.configure(bg=bg)
        right.overrideredirect(True)
        right.wm_attributes("-topmost", 1)
        right.wm_geometry(f'{bd}x{y2 - y1 + bd}+{x2}+{y1 - bd}')

        top = tk.Toplevel(master)
        top.configure(bg=bg)
        top.overrideredirect(True)
        top.wm_attributes("-topmost", 1)
        top.wm_geometry(f'{x2 - x1 + bd}x{bd}+{x1 - bd}+{y1 - bd}')

        bottom = tk.Toplevel(master)
        bottom.configure(bg=bg)
        bottom.overrideredirect(True)
        bottom.wm_attributes("-topmost", 1)
        bottom.wm_geometry(f'{(x2 + bd - x1)}x{bd}+{x1}+{y2}')

        self.widgets = (left, right, top, bottom)

    def destroy(self):
        for widget in self.widgets:
            widget.destroy()


class GifRecorder(object):
    mode_info = {
        # 模式名: (转换的色彩格式，png压缩级别/jpeg的质量，帧率，时长限制)
        'Normal': ('P', 0, 10, 600),
        'High Quality': ('RGBA', 6, 5, 300),
        'High Frame Rate': ('', 75, 25, 120)}

    def __init__(self, master):
        self.master = master
        self.area_box = None
        self.mode = None
        self.rect = None
        self.frame_sleep = None
        self.run_time = 0
        self.stop_flag = False
        self.cancel_flag = False
        self.is_recording = False
        self.is_asking = False
        self.is_saving = False
        self.progress = 0

    def record(self, sec=0):
        """
        录屏实现
        sec: 录制时长限制（秒）
        return: 录制的临时目录，录制帧数
        """
        start_time = time.time()
        tmp_dir = str(int(start_time))
        os.mkdir(tmp_dir)
        x1, y1, x2, y2 = self.area_box
        mode, lvl, _, limit = self.mode_info[self.mode]
        limit = sec or limit
        index = 0
        while (not self.stop_flag) and (not self.cancel_flag) and (time.time() - start_time <= limit):
            pos = pyautogui.position()
            image = ImageGrab.grab(self.area_box)
            ImageDraw.Draw(image).polygon(
                (pos[0] - x1, pos[1] - y1, pos[0] - x1, pos[1] - y1 + 18, pos[0] - x1 + 13, pos[1] - y1 + 13),
                fill=(0, 0, 0, 150), outline=(200, 200, 200), width=2)
            if mode:
                image.convert(mode).save(f'{tmp_dir}/{index}', format='png', compress_level=lvl)
            else:
                image.save(f'{tmp_dir}/{index}', format='jpeg', quality=lvl)
            index += 1
            if self.frame_sleep:
                time.sleep(self.frame_sleep)
            self.run_time = time.time() - start_time
        return tmp_dir, index

    def init(self, area_box, mode):
        """
        录屏初始化，画矩形范围辅助框
        area_box: 录屏的区域坐标
        mode: 录制质量
            清晰度优先: png格式图片，清晰度高，但帧率低
            高帧率优先: jpg格式图片，清晰度低有噪点，但帧率高
        """
        self.area_box = area_box
        self.mode = mode
        self.rect = UnFillRectangle(self.master, area_box, bg=Style.theme_color)

    def prepare(self):
        """
        预录制，计算出每帧的大致休眠时间，保证相对准确的帧率
        """
        sec = 4
        speed = self.mode_info[self.mode][2]
        path, num = self.record(sec)
        self.frame_sleep = max(0, (1000 / speed - 1000 * sec / num) / 1000)
        shutil.rmtree(path)
        # print(f"{self.mode}: speed: {speed}, per sleep: {self.frame_sleep}")

    def start(self):
        """
        正式开始录制并选择保存的路径
        """
        self.is_recording = True
        path, num = self.record()
        # print(f"frame number: {num}, except number: {int(self.run_time * self.mode_info[self.mode][2])}")
        self.rect.destroy()
        self.is_recording = False

        if not self.cancel_flag:
            def image_generator():
                for i in range(1, num):
                    self.progress = i * 100 // num
                    yield Image.open(f"{path}/{i}").convert('P')

            self.is_asking = True
            file_name = filedialog.asksaveasfilename(
                filetypes=[('Save Gif File', '*.gif')],
                initialfile='%s.gif' % time.strftime('%Y%m%d%H%M%S', time.localtime()))
            self.is_asking = False
            self.is_saving = True
            if file_name:
                st = time.time()
                Image.open(f'{path}/0').convert('P').save(
                    file_name, format='gif', save_all=True, append_images=image_generator(), optimize=True,
                    duration=self.run_time * 1000 // num, loop=0)
                # print(f'frame to gif cost time: {int(time.time()-st)}s')
            self.is_saving = False
        shutil.rmtree(path)

    def stop(self):
        self.stop_flag = True

    def cancel(self):
        self.cancel_flag = True

    def is_prepare(self):
        return self.frame_sleep is not None


class ScreenShot(object):
    """
    截屏工具实现类
    """

    def __init__(self):
        self.root = tk.Tk()
        self.set_headless(self.root)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        if os.name == 'posix' and self.screen_width > 3000:
            self.screen_width = self.screen_width // 2
        # 初次截全屏，创建主画布，并将截屏显示在主画布的image控件
        self.image = ImageTk.PhotoImage(ImageGrab.grab((0, 0, self.screen_width, self.screen_height)))
        self.mask = ImageTk.PhotoImage(Image.new("RGBA", (self.screen_width, self.screen_height), (40, 40, 40, 120)))
        self.canvas = tk.Canvas(self.root, width=self.screen_width, height=self.screen_height, cursor=Style.rect_cursor)
        self.canvas.create_image(0, 0, image=self.image, anchor='nw')
        self.canvas.pack(fill='both', expand=1)
        self.canvas.bind('<Motion>', self.reference_line_event)           # 绑定鼠标移动事件，画开始截图辅助线
        self.canvas.bind('<Button-1>', self.rectangle_start_event)        # 绑定鼠标左键事件，启动截图
        self.canvas.bind('<Button-3>', self.cancel_process_event)         # 绑定鼠标右键事件，取消截图
        self.canvas.bind('<B1-Motion>', self.rectangle_move_event)        # 绑定鼠标按下拖动事件，画截图区域选框
        self.canvas.bind('<ButtonRelease-1>', self.rectangle_end_event)   # 绑定鼠标释放事件，结束截图区域
        self.gif_record = GifRecorder(self.root)

        self.rectangle_start_pos = [None] * 2    # 矩形选框的启动坐标位置 (x_start, y_start)
        self.rectangle_move_pos = [None] * 2     # 选框内按住鼠标左键时的坐标，用于计算并整体移动选框
        self.rectangle_instance = None           # 截图范围矩形选框的实例
        self.mask_instance = [None] * 4          # 矩形选框之外的灰色遮罩实例
        self.refer_line_instance = [None] * 2    # 截图X Y辅助线实例列表
        self.adjust_dot_instance = [None] * 8    # 矩形选框各角各边画的圆点实例列表
        self.in_adjust_dot_id = None             # 0:左上  1:右上  2:左下  3:右下  4/5:上下  6/7:左右  8:选框内  None:选框外
        self.tool_window = None                  # 工具栏窗口
        self.tool_master = None                  # 截屏界面工具栏窗口的master
        self.tool_gif_master = None              # gif录屏界面工具栏窗口的master
        self.tool_set_master = None              # 工具栏窗口中设置界面的master
        self.tool_widgets = [[], [], []]         # 截屏工具栏控件实例列表
        self.tool_mark_type = 0                  # 当前选择的标记类型
        self.mark_position = [None] * 2          # 当前标记实例的坐标位置
        self.mark_instance = None                # 标记的画图实例
        self.mark_widgets = []                   # 标记的画图列表，用于撤回操作
        self.tool_window_pos = [None] * 2        # 工具栏手动移动前的坐标

    def hand_move_tool_window(self, widget):
        def start_pos(event):
            self.tool_window_pos[0] = event.x
            self.tool_window_pos[1] = event.y

        def end_pos(event):
            x, y = list(map(int, self.tool_window.geometry().replace('x', '+').split('+')))[2:]
            x = x + event.x - self.tool_window_pos[0]
            y = y + event.y - self.tool_window_pos[1]
            self.tool_window.geometry(f'+{x}+{y}')

        widget.configure(cursor=Style.dot_cursors[8])
        widget.bind('<Button-1>', start_pos)
        widget.bind('<B1-Motion>', end_pos)
        widget.bind('<ButtonRelease-1>', end_pos)

    def pack_pic_tool_window(self):
        """
        截屏工具栏窗口布局
        """
        x, y, width, height = self.calc_tool_window_position('pic')
        x_start, y_start, x_end, y_end = self.canvas.coords(self.rectangle_instance)
        area_txt = f'{int(x_end) - int(x_start)}*{int(y_end) - int(y_start)}'
        if self.tool_window is not None:
            self.tool_window.geometry(f'{width}x{height}+{x}+{y}')
            self.tool_widgets[0][1].configure(text=area_txt)
            return

        def pack_left():
            label = tk.Label(self.tool_master, text='⣿', font=(Style.font, 18), bg=Style.tool_bg, fg='Gray70')
            label.place(x=0, y=0, width=30, height=height)
            type_box = ttk.Combobox(
                self.tool_master, font=(Style.font, 13), values=Style.shot_types, state='readonly')
            type_box.set(Style.shot_types[0])
            type_box.place(x=30, y=(height - type_height) // 2 + 3, width=80, height=type_height)
            type_box.bind("<<ComboboxSelected>>", self.choose_screenshot_type_event)
            txt_label = tk.Label(self.tool_master, text=area_txt, font=(Style.font, 10), bg=Style.tool_bg, fg='Gray70')
            txt_label.place(x=120, y=0, width=70, height=type_height)
            set_btn = BaseButton(
                self.tool_master, text=f"۞ {Style.get_language('SET')}", width=5, bg=Style.tool_bg, fg='Gray50',
                font=(Style.font, 11), command=self.pack_settings_window_event)
            set_btn.place(x=120, y=type_height, width=70, height=opt_height)
            self.tool_widgets[0] = (type_box, txt_label)
            self.hand_move_tool_window(label)

        def pack_type():
            self.tool_widgets[1] = []
            index = 0
            for txt, item in {
                '□': ('Rectangle', False, lambda c=0: self.prepare_mark_view(c)),
                '◯': ('Circular', False, lambda c=1: self.prepare_mark_view(c)),
                '―': ('Line', False, lambda c=2: self.prepare_mark_view(c)),
                '→': ('Arrow', False, lambda c=3: self.prepare_mark_view(c)),
                '✎': ('Pen', False, lambda c=4: self.prepare_mark_view(c)),
                'T': ('Text', False, lambda c=5: self.prepare_mark_view(c)),
                '▨': ('Mosaic', False, lambda c=6: self.prepare_mark_view(c)),
                '⟲': ('Revoke', True, self.undo_mark_event),
                '✕': ('Exit', True, self.cancel_process_event),
                '▣': ('Hang', True, self.float_show_screenshot_event),
                '✓': ('To Clipboard', True, self.start_set_clipboard_event)
            }.items():
                btn = BaseButton(
                    self.tool_master, text=txt, fg='Black', bg=Style.tool_bg, choo_fg='Red', choo_bg=Style.theme_color,
                    width=2, height=1, font=(Style.font, 18), up=item[1], command=item[2])
                btn.place(x=40 * index + 190, y=0, width=40, height=type_height)
                Tip.enter_tips(btn, Style.get_language(item[0]))
                self.tool_widgets[1].append(btn)
                index += 1

        def pack_option():
            def pt_select(event=None):
                Style.choose_pt = pt_box.get()

            def pi_select(event=None):
                Style.choose_pi = pi_box.get()

            pt_box = ttk.Combobox(
                self.tool_master, width=5, font=(Style.font, 11), values=Style.text_pt_values, state='readonly')
            pt_box.set(Style.choose_pt)
            pt_box.place(x=200, y=type_height, width=55, height=opt_height)
            pt_box.bind("<<ComboboxSelected>>", pt_select)
            pi_box = ttk.Combobox(
                self.tool_master, width=5, font=(Style.font, 11), values=Style.mark_pi_values, state='readonly')
            pi_box.set(Style.choose_pi)
            pi_box.place(x=260, y=type_height, width=55, height=opt_height)
            pi_box.bind("<<ComboboxSelected>>", pi_select)
            color_btns = []
            for index, color in enumerate(Style.text_colors):
                btn = BaseButton(self.tool_master, text='■', font=(Style.font, 13), bg='Gray70',
                                 fg=color, choo_fg=color, choo_bg=Style.theme_color, up=False,
                                 command=lambda c=color: self.change_global_color_event(c))
                btn.place(x=index * opt_height + 320, y=type_height, width=opt_height, height=opt_height)
                color_btns.append(btn)
            save_btn = BaseButton(
                self.tool_master, text='SAVE', font=(Style.font, 14), bg='Gray40', width=6,
                command=self.start_save_file_event)
            save_btn.place(x=len(Style.text_colors) * opt_height + 330, y=type_height, width=120, height=opt_height)
            Tip.enter_tips(pt_box, Style.get_language('Font Size'))
            Tip.enter_tips(pi_box, Style.get_language('Line Thickness'))
            Tip.enter_tips(save_btn, Style.get_language('Save File'))
            self.tool_widgets[2] = color_btns

        self.tool_window = tk.Toplevel(self.root, bg=Style.tool_bg)
        self.tool_window.geometry(f'{width}x{height}+{x}+{y}')
        self.set_headless(self.tool_window, full=False)
        self.tool_master = tk.Frame(self.tool_window, width=width, height=height, bg=Style.tool_bg)
        self.tool_master.place(x=0, y=0, width=width, height=height)
        type_height, opt_height = height // 2 + 5, height // 2 - 9
        pack_left()
        pack_type()
        pack_option()
        self.change_global_color_event(Style.choose_color)

    def pack_gif_tool_window(self):
        def choose_mode_event(event=None):
            limit_time = self.gif_record.mode_info[mode_box.get()][3]
            _txt = f'-/{limit_time // 60:02}:{limit_time % 60:02}'
            txt_label.configure(text=_txt)

        def modify_time():
            limit_time = self.gif_record.mode_info[mode_box.get()][3]
            time.sleep(1)
            while self.gif_record.is_recording:
                _txt = (f'{int(self.gif_record.run_time // 60):02}:{int(self.gif_record.run_time % 60):02}/'
                        f'{limit_time // 60:02}:{limit_time % 60:02}')
                txt_label.configure(text=_txt)

        def modify_state():
            while 1:
                if self.gif_record.is_recording:
                    save_btn.configure(text='SAVE')   # ⬇
                if self.gif_record.is_asking:
                    exit_btn.configure(state='disabled')
                    save_btn.configure(text='Archiving', state='disabled')
                elif self.gif_record.is_saving:
                    exit_btn.configure(state='disabled')
                    save_btn.configure(font=(Style.font, 9), text=f'Archiving\n{self.gif_record.progress}%',
                                       state='disabled')
                else:
                    exit_btn.configure(state='normal')
                    if not self.gif_record.is_recording:
                        save_btn.configure(text='▶')
                        cancel_gif_event()
                time.sleep(0.4)

        def gif_start():
            def start():
                create_thread(modify_state)
                create_thread(modify_time)
                create_thread(self.gif_record.start)

            for _ in range(2):
                if self.gif_record.is_prepare():
                    break
            else:
                messagebox.showerror("Screen record initialization failed")
                return
            self.root.withdraw()
            self.canvas.destroy()
            self.root.update()
            self.root.after(500, start)

        def gif_init(mode):
            x_start, y_start, x_end, y_end = self.canvas.coords(self.rectangle_instance)
            x1, y1 = (x_start + x_end) // 2 - 70, (y_start + y_end) // 2 - 70
            x2, y2 = (x_start + x_end) // 2 + 70, (y_start + y_end) // 2 + 70
            self.canvas.create_oval(x1, y1, x2, y2, fill=Style.theme_color)
            text = self.canvas.create_text((x_start + x_end) // 2, (y_start + y_end) // 2 - 8, text='',
                                           font=(Style.font, 80, 'bold'), fill='Snow', anchor='center')

            def countdown(num):
                self.canvas.itemconfig(text, text=str(num))
                if num:
                    self.canvas.after(1000, countdown, num - 1)
                else:
                    gif_start()

            self.gif_record.init((int(x_start), int(y_start), int(x_end), int(y_end)), mode=mode)
            create_thread(lambda: countdown(5))
            create_thread(self.gif_record.prepare)

        def start_stop_event(event=None):
            if self.gif_record.is_recording:
                # 已经开始，即当前正在录屏，再次点击后停止并保存
                self.gif_record.stop()
            else:
                mode_box.configure(state='disabled')
                gif_init(mode_box.get())

        def cancel_gif_event(event=None):
            self.gif_record.cancel()
            self.root.after(500, self.cancel_process_event)

        width, height = Style.tool_window_size['gif']
        self.tool_gif_master = tk.Frame(self.tool_window, bg=Style.tool_bg)
        self.tool_gif_master.place(x=0, y=0, width=width, height=height)
        label = tk.Label(self.tool_gif_master, text='⣿', font=(Style.font, 14),
                         bg=Style.tool_bg, fg='Gray70', anchor='e')
        label.place(x=0, y=0, width=30, height=height)
        self.hand_move_tool_window(label)
        txt_label = tk.Label(self.tool_gif_master, text='', font=(Style.font, 10), bg=Style.tool_bg, fg='Gray70')
        txt_label.place(x=40, y=5, width=90, height=height - 10)
        mode_list = list(self.gif_record.mode_info.keys())
        mode_box = ttk.Combobox(self.tool_gif_master, width=20, values=mode_list, font=(Style.font, 9), state='readonly')
        mode_box.set(mode_list[0])
        mode_box.place(x=140, y=5, width=120, height=height - 10)
        mode_box.bind("<<ComboboxSelected>>", choose_mode_event)
        exit_btn = BaseButton(
            self.tool_gif_master, text='✕', font=(Style.font, 18), bg=Style.tool_bg, width=2, command=cancel_gif_event)
        exit_btn.place(x=270, y=2, width=40, height=height - 6)
        save_btn = BaseButton(
            self.tool_gif_master, text='▶', font=(Style.font, 14), bg=Style.tool_bg, width=4, command=start_stop_event)
        save_btn.place(x=320, y=5, width=40, height=height - 10)
        Tip.enter_tips(exit_btn, Style.get_language('Exit'))
        Tip.enter_tips(save_btn, Style.get_language('Start/Stop'))
        choose_mode_event()

    def pack_settings_window_event(self):
        """
        设置窗口布局
        """
        def modify_settings():
            Style.theme_color = theme_box.get()
            Style.mask_switch = True if mask_box.get() == 'YES' else False
            Style.choose_pt = pt_box.get()
            Style.choose_pi = pi_box.get()
            Style.choose_lang = lang_box.get()
            Style.write_settings({
                'theme_color': Style.theme_color,
                'mask_switch': Style.mask_switch,
                'tips_switch': Style.tips_switch,
                'default_pt': Style.choose_pt,
                'default_pi': Style.choose_pi,
                'language': Style.choose_lang
            })
            self.tool_set_master.place_forget()

        def change_tips_switch(click=True):
            if click:
                Style.tips_switch = not Style.tips_switch
            tips_switch.configure(
                text=Style.get_language('Turn Off Prompt') if Style.tips_switch else Style.get_language('Turn On Prompt'),
                bg=Style.theme_color if Style.tips_switch else 'Gray80',
                fg='Black'
            )

        width, height = Style.tool_window_size['pic']
        if self.tool_set_master is not None:
            self.tool_set_master.place(x=30, y=0, width=width, height=height)
            return
        self.tool_set_master = tk.Frame(self.tool_window, bg=Style.tool_bg)
        self.tool_set_master.place(x=30, y=0, width=width, height=height)
        widget_height = (height - 15) // 2
        theme_box = ttk.Combobox(self.tool_set_master, width=4, values=Style.theme_colors, state='readonly')
        theme_box.place(x=10, y=5, width=80, height=widget_height)
        mask_box = ttk.Combobox(self.tool_set_master, width=4, values=('YES', 'NO'), state='readonly')
        mask_box.place(x=110, y=5, width=80, height=widget_height)
        pt_box = ttk.Combobox(self.tool_set_master, width=4, values=Style.text_pt_values, state='readonly')
        pt_box.place(x=10, y=widget_height + 10, width=80, height=widget_height)
        pi_box = ttk.Combobox(self.tool_set_master, width=4, values=Style.mark_pi_values, state='readonly')
        pi_box.place(x=110, y=widget_height + 10, width=80, height=widget_height)
        lang_box = ttk.Combobox(self.tool_set_master, width=4, values=Style.languages, state='readonly')
        lang_box.place(x=210, y=5, width=80, height=widget_height)
        tips_switch = BaseButton(self.tool_set_master, text='', width=11, up=False, command=change_tips_switch)
        tips_switch.place(x=450, y=5, width=120, height=widget_height)
        change_tips_switch(click=False)
        BaseButton(self.tool_set_master, text='OK', bg='Black', fg='Snow', width=11,
                   command=modify_settings).place(x=450, y=widget_height + 10, width=120, height=widget_height)
        theme_box.set(Style.theme_color)
        mask_box.set('YES' if Style.mask_switch else 'NO')
        pt_box.set(Style.choose_pt)
        pi_box.set(Style.choose_pi)
        lang_box.set(Style.choose_lang)
        Tip.enter_tips(theme_box, Style.get_language('Theme'))
        Tip.enter_tips(mask_box, Style.get_language('Outer Mask'))
        Tip.enter_tips(pt_box, Style.get_language('Font Size'))
        Tip.enter_tips(pi_box, Style.get_language('Line Thickness'))
        Tip.enter_tips(lang_box, Style.get_language('Language'))

    def choose_screenshot_type_event(self, event):
        """
        选择截屏/录屏类型回调
        """
        index = Style.shot_types.index(self.tool_widgets[0][0].get())
        if index == 1:  # 录制gif
            x, y, width, height = self.calc_tool_window_position('gif')
            self.tool_window.geometry(f'{width}x{height}+{x}+{y}')
            self.tool_master.place_forget()
            self.delete_adjust_dots()
            self.canvas.unbind('<Motion>')
            self.canvas.unbind('<Button-1>')
            self.canvas.unbind('<Button-3>')
            self.canvas.unbind('<B1-Motion>')
            self.canvas.unbind('<ButtonRelease-1>')
            self.canvas.unbind('<Double-Button-1>')
            self.canvas.configure(cursor=Style.default_cursor)
            self.pack_gif_tool_window()

    def show_tip(self, text):
        """
        显示截图工具启动提示
        """
        if not Style.tips_switch:
            return

        def hide():
            self.canvas.delete(text1)
            self.canvas.delete(text2)

        x, y = self.screen_width // 2, self.screen_height // 2
        text1 = self.canvas.create_text(x + 1, y + 1, text=text, font=(Style.font, 18, 'bold'), fill='Gray')
        text2 = self.canvas.create_text(x, y, text=text, font=(Style.font, 18, 'bold'), fill=Style.theme_color)
        self.root.after(5000, hide)

    def run(self):
        """
        启动app主程序
        """
        self.show_tip(Style.tip % Style.get_language('TIP'))
        self.root.mainloop()

    @classmethod
    def set_headless(cls, widget, full=True):
        """
        设置窗体指定及全屏
        """
        widget.attributes("-topmost", 1)
        if full:
            widget.attributes('-fullscreen', True)    # 多屏时无法显示全部屏幕
            # widget.attributes('-type', 'dock')      # 工具栏输入子控件无法获取焦点
        else:
            widget.overrideredirect(True)

    def cancel_process_event(self, event=None):
        """
        取消截图
        """
        self.canvas.destroy()
        self.root.quit()
        self.root.destroy()

    def calc_tool_window_position(self, which):
        """
        获取当前工具窗体的位置坐标并计算屏幕边界，不超过屏幕边界
        """
        gap = 10
        width, height = Style.tool_window_size[which]
        if self.tool_window_pos[0] is None:
            x_start, y_start, x_end, y_end = self.canvas.coords(self.rectangle_instance)
            x, y = x_end - width, y_end + gap
            if x < 0:
                x = 0
            if y + height > self.screen_height:      # 底部超出屏幕
                if y_start - gap - height > 0:       # 顶部可以放下
                    y = y_start - gap - height
                else:
                    y = self.screen_height - height  # 顶部也放不下，那就底部挤着
        else:
            x, y = self.tool_window.geometry().replace('x', '+').split('+')[2:]
        return int(x), int(y), width, height

    def check_in_widget(self, x, y, widget=None):
        """
        判断坐标是否在控件(canvas子控件)内部，控件为None时，判断是否在整个屏幕内
        """
        if widget:
            x_start, y_start, x_end, y_end = self.canvas.coords(widget)
        else:   # 判断整个屏幕
            x_start, y_start, x_end, y_end = 0, 0, self.screen_width, self.screen_height
        return x_start < x < x_end and y_start < y < y_end

    def reference_line_event(self, event):
        """
        跟随鼠标划线，用于辅助开始截图
        """
        pos1 = event.x, 0, event.x, self.screen_height
        pos2 = 0, event.y, self.screen_width, event.y
        if self.refer_line_instance[0] is None:
            self.refer_line_instance[0] = self.canvas.create_line(pos1, dash=(3, 2), fill=Style.lines_color)
            self.refer_line_instance[1] = self.canvas.create_line(pos2, dash=(3, 2), fill=Style.lines_color)
        else:
            self.canvas.coords(self.refer_line_instance[0], pos1)
            self.canvas.coords(self.refer_line_instance[1], pos2)

    def delete_reference_lines(self):
        """
        删除截屏辅助线
        """
        for i, line in enumerate(self.refer_line_instance):
            if line is not None:
                self.canvas.delete(line)
                self.refer_line_instance[i] = None

    def delete_adjust_dots(self):
        """
        删除选框的调整圆点
        """
        for i, dot in enumerate(self.adjust_dot_instance):
            if dot is not None:
                self.canvas.delete(dot)
                self.adjust_dot_instance[i] = None

    def delete_mask_instance(self):
        """
        删除选框外部遮罩
        """
        for mask in self.mask_instance:
            if mask is not None:
                self.canvas.delete(mask)

    def rectangle_start_event(self, event):
        """
        点击鼠标左键，记录截图开始位置
        """
        self.rectangle_start_pos[0] = event.x
        self.rectangle_start_pos[1] = event.y

    def rectangle_move_event(self, event):
        """
        按住鼠标左键后拖动，画矩形选框及灰色半透明遮罩
        """
        if self.rectangle_start_pos[0] is None:
            return
        coords = *self.rectangle_start_pos, event.x, event.y
        if self.rectangle_instance is None:
            self.rectangle_instance = self.canvas.create_rectangle(coords, **Style.rectangle_style)
        else:
            self.canvas.coords(self.rectangle_instance, coords)
        if not Style.mask_switch:
            return
        # 画遮罩
        x_start, y_start, x_end, y_end = self.canvas.coords(self.rectangle_instance)
        w, h = self.screen_width, self.screen_height
        if self.mask_instance[0] is None:
            self.mask_instance[0] = self.canvas.create_image(0, 0, image=self.mask, anchor='nw')
            self.mask_instance[1] = self.canvas.create_image(0, 0, image=self.mask, anchor='nw')
            self.mask_instance[2] = self.canvas.create_image(0, 0, image=self.mask, anchor='nw')
            self.mask_instance[3] = self.canvas.create_image(0, 0, image=self.mask, anchor='nw')
        self.canvas.moveto(self.mask_instance[0], x_end - w, y_start - h)
        self.canvas.moveto(self.mask_instance[1], x_end, y_end - h)
        self.canvas.moveto(self.mask_instance[2], x_start, y_end)
        self.canvas.moveto(self.mask_instance[3], x_start - w, y_start)
        self.canvas.tag_raise(self.rectangle_instance)

    def rectangle_end_event(self, event=None):
        """
        鼠标左键释放，结束截图选框
        """
        if self.rectangle_instance is None:
            return
        x_start, y_start, x_end, y_end = self.canvas.coords(self.rectangle_instance)
        if x_end - x_start < Style.rectangle_limit and y_end - y_start < Style.rectangle_limit:
            self.show_tip(Style.get_language('Too small range'))
            return
        self.canvas.unbind('<ButtonRelease-1>')
        self.canvas.bind('<Motion>', self.change_cursor_in_range_event)
        self.canvas.bind('<Button-1>', self.move_rectangle_start_event)
        self.canvas.bind('<B1-Motion>', self.adjust_rectangle_event)
        self.canvas.bind('<Double-Button-1>', self.start_set_clipboard_event)
        self.delete_reference_lines()
        offset = Style.dot_offset
        left_top_coords = x_start - offset, y_start - offset, x_start + offset, y_start + offset
        right_top_coords = x_end - offset, y_start - offset, x_end + offset, y_start + offset
        left_bottom_coords = x_start - offset, y_end - offset, x_start + offset, y_end + offset
        right_bottom_coords = x_end - offset, y_end - offset, x_end + offset, y_end + offset
        x_center, y_center = (x_start + x_end) // 2, (y_start + y_end) // 2
        left_center_coords = x_start - offset, y_center - offset, x_start + offset, y_center + offset
        right_center_coords = x_end - offset, y_center - offset, x_end + offset, y_center + offset
        top_center_coords = x_center - offset, y_start - offset, x_center + offset, y_start + offset
        bottom_canter_coords = x_center - offset, y_end - offset, x_center + offset, y_end + offset
        style = {'fill': Style.theme_color, 'outline': Style.theme_color}
        if self.adjust_dot_instance[0] is None:
            # 4个角画圆，可以调整选框X和Y
            self.adjust_dot_instance[0] = self.canvas.create_oval(left_top_coords, **style)
            self.adjust_dot_instance[1] = self.canvas.create_oval(right_top_coords, **style)
            self.adjust_dot_instance[2] = self.canvas.create_oval(left_bottom_coords, **style)
            self.adjust_dot_instance[3] = self.canvas.create_oval(right_bottom_coords, **style)
            # 4个边的中心画圆，可以调整选框X或Y
            self.adjust_dot_instance[4] = self.canvas.create_oval(left_center_coords, **style)
            self.adjust_dot_instance[5] = self.canvas.create_oval(right_center_coords, **style)
            self.adjust_dot_instance[6] = self.canvas.create_oval(top_center_coords, **style)
            self.adjust_dot_instance[7] = self.canvas.create_oval(bottom_canter_coords, **style)
        else:
            self.canvas.coords(self.adjust_dot_instance[0], left_top_coords)
            self.canvas.coords(self.adjust_dot_instance[1], right_top_coords)
            self.canvas.coords(self.adjust_dot_instance[2], left_bottom_coords)
            self.canvas.coords(self.adjust_dot_instance[3], right_bottom_coords)
            self.canvas.coords(self.adjust_dot_instance[4], left_center_coords)
            self.canvas.coords(self.adjust_dot_instance[5], right_center_coords)
            self.canvas.coords(self.adjust_dot_instance[6], top_center_coords)
            self.canvas.coords(self.adjust_dot_instance[7], bottom_canter_coords)

        self.pack_pic_tool_window()

    def move_rectangle_start_event(self, event):
        """
        记录矩形选框开始移动时的鼠标坐标，用于后续计算移动的距离
        """
        if self.in_adjust_dot_id != 8:
            return
        self.rectangle_move_pos[0] = event.x
        self.rectangle_move_pos[1] = event.y

    def adjust_rectangle_event(self, event):
        """
        调整矩形选框的边界
        0___6___1
        |       |
        4       5
        |       |
        2___7___3
        """
        if self.in_adjust_dot_id is None:
            return
        x_end, y_end = event.x, event.y
        coords = self.canvas.coords(self.rectangle_instance)
        if self.in_adjust_dot_id == 0:
            x_start, y_start = coords[2], coords[3]
        elif self.in_adjust_dot_id == 1:
            x_start, y_start = coords[0], coords[3]
        elif self.in_adjust_dot_id == 2:
            x_start, y_start = coords[2], coords[1]
        elif self.in_adjust_dot_id == 3:
            x_start, y_start = coords[0], coords[1]
        elif self.in_adjust_dot_id == 4:
            x_start, y_start = coords[2], coords[3]
            y_end = coords[1]
        elif self.in_adjust_dot_id == 5:
            x_start, y_start = coords[0], coords[1]
            y_end = coords[3]
        elif self.in_adjust_dot_id == 6:
            x_start, y_start = coords[2], coords[3]
            x_end = coords[0]
        elif self.in_adjust_dot_id == 7:
            x_start, y_start = coords[0], coords[1]
            x_end = coords[2]
        elif self.in_adjust_dot_id == 8:
            x_offset = event.x - self.rectangle_move_pos[0]
            y_offset = event.y - self.rectangle_move_pos[1]
            x_start = coords[0] + x_offset
            y_start = coords[1] + y_offset
            x_end = coords[2] + x_offset
            y_end = coords[3] + y_offset
            # 屏幕边界限制处理，两个对角都在屏幕内，则整体都在屏幕内
            if not (self.check_in_widget(x_start, y_start) and self.check_in_widget(x_end, y_end)):
                return
        else:
            return
        self.rectangle_move_pos[0] = event.x
        self.rectangle_move_pos[1] = event.y
        self.rectangle_start_event(Event(x_start, y_start))
        self.rectangle_move_event(Event(x_end, y_end))
        self.rectangle_end_event()

    def change_cursor_in_range_event(self, event):
        """
        检查鼠标位置，如果在边界的圆点上，则变化为方向指针，在矩形选框内则为可移动指针
        """
        for i, dot in enumerate(self.adjust_dot_instance):
            if dot is None:
                continue
            if self.check_in_widget(event.x, event.y, dot):
                self.in_adjust_dot_id = i
                self.canvas.configure(cursor=Style.dot_cursors[i])
                break
        else:
            if self.check_in_widget(event.x, event.y, self.rectangle_instance):
                self.in_adjust_dot_id = 8
                self.canvas.configure(cursor=Style.dot_cursors[8])
            else:
                self.in_adjust_dot_id = None
                self.canvas.configure(cursor=Style.default_cursor)

    def prepare_mark_view(self, index):
        """
        准备标记, 固定画布：
            1. 标记按钮恢复
            2. 选框上圆点去除
            3. 主画布解绑事件并重新绑定
        """
        self.mark_text_done()
        self.tool_mark_type = index
        for i, widget in enumerate(self.tool_widgets[1]):
            if i == index:
                widget.down()
            else:
                widget.up()
        if self.adjust_dot_instance[0] is not None:
            self.delete_adjust_dots()
            self.canvas.bind('<Button-1>', self.mark_create_event)
            self.canvas.bind('<B1-Motion>', self.mark_move_event)
            self.canvas.bind('<ButtonRelease-1>', self.mark_end_event)
            self.canvas.bind('<Motion>', lambda event: self.tool_window.attributes("-topmost", 1))
        self.canvas.configure(cursor=Style.rect_cursor)

    def mark_text_done(self):
        """
        文本标记结束，删除文本辅助框
        """
        if self.tool_mark_type == 5 and self.mark_instance:
            text_inst, text_text, text_rect = self.mark_instance
            text_inst.stop()
            if text_inst.get():
                self.mark_widgets.append(text_text)
            else:
                self.canvas.delete(text_text)
            self.canvas.delete(text_rect)
            self.mark_instance = []
            self.root.unbind('<Any-Key>')

    def mark_factory(self, index, x_start, y_start, x_end, y_end):
        """
        标记创建工厂
        """
        coords = x_start, y_start, x_end, y_end
        if self.mark_instance and index in (0, 1, 2, 3, 6):
            self.canvas.coords(self.mark_instance, coords)
            return
        pi = Style.get_pi()
        if index == 0:      # 矩形
            self.mark_instance = self.canvas.create_rectangle(coords, width=pi, outline=Style.choose_color)
        elif index == 1:    # 椭圆
            self.mark_instance = self.canvas.create_oval(coords, width=pi, outline=Style.choose_color)
        elif index == 2:    # 直线
            self.mark_instance = self.canvas.create_line(coords, width=pi, fill=Style.choose_color)
        elif index == 3:    # 箭头
            self.mark_instance = self.canvas.create_line(
                coords, arrow='last', arrowshape=(24, 28, 10), width=pi, fill=Style.choose_color)
        elif index == 4:    # 画笔
            self.mark_instance.append(self.canvas.create_line(coords, width=pi, fill=Style.choose_color))
            self.mark_position[0] = x_end
            self.mark_position[1] = y_end
        elif index == 5:    # 文本
            if self.mark_instance:
                self.mark_text_done()
            else:
                text = CanvasText(self.canvas, x_start, y_start)
                self.root.bind('<Any-Key>', text.input)
                self.mark_instance = [text, text.text, text.rect]
        elif index == 6:    # 马赛克
            self.mark_instance = self.canvas.create_rectangle(
                coords, width=pi, outline=Style.choose_color, fill=Style.choose_color)

    def mark_create_event(self, event):
        """
        记录开始创建标记的起点坐标
        """
        if self.tool_mark_type == 4:
            self.mark_instance = []
        elif self.tool_mark_type == 5:
            # 文本mark实例在mark_factory中清空
            self.mark_factory(self.tool_mark_type, event.x, event.y, 0, 0)
        else:
            self.mark_instance = None
        if self.check_in_widget(event.x, event.y, self.rectangle_instance):
            self.mark_position[0] = event.x
            self.mark_position[1] = event.y
        else:
            self.mark_position[0] = None
            self.mark_position[1] = None

    def mark_move_event(self, event):
        """
        创建标记拖动鼠标
        """
        if self.tool_mark_type == 5 or self.mark_position[0] is None:
            return
        pi = Style.get_pi() // 2
        coords = self.canvas.coords(self.rectangle_instance)
        x_start, y_start = self.mark_position[0], self.mark_position[1]
        x_end = min(max(coords[0] + pi, event.x), coords[2] - pi)   # 限制x在矩形框范围+-pi内
        y_end = min(max(coords[1] + pi, event.y), coords[3] - pi)   # 限制y在矩形框范围+-pi内
        self.mark_factory(self.tool_mark_type, x_start, y_start, x_end, y_end)

    def mark_end_event(self, event):
        """
        标记结束，记录标记的实例
        """
        if self.tool_mark_type == 5 or self.mark_position[0] is None:
            return
        if self.mark_instance:
            self.mark_widgets.append(self.mark_instance)
            self.mark_instance = None

    def undo_mark_event(self):
        """
        撤销上一次的标记
        """
        if not self.mark_widgets:
            return
        latest_widget = self.mark_widgets.pop(-1)
        if isinstance(latest_widget, list):
            for widget in latest_widget:
                self.canvas.delete(widget)
        else:
            self.canvas.delete(latest_widget)

    def change_global_color_event(self, color):
        """
        点击工具栏颜色，实时修改标记颜色
        """
        index = Style.text_colors.index(color)
        for i, widget in enumerate(self.tool_widgets[2]):
            if i == index:
                widget.down()
            else:
                widget.up()
        Style.choose_color = color

    def set_clipboard_and_save(self):
        x_start, y_start, x_end, y_end = self.canvas.coords(self.rectangle_instance)
        self.mark_text_done()
        self.delete_mask_instance()
        self.delete_adjust_dots()
        self.canvas.delete(self.rectangle_instance)
        self.tool_window.destroy()
        self.root.update()
        time.sleep(0.2)
        os.makedirs('img', exist_ok=True)
        img_file = 'img/%s.png' % time.strftime('%Y%m%d%H%M%S', time.localtime())
        image = ImageGrab.grab((x_start + 1, y_start + 1, x_end, y_end))
        image.save(img_file)
        set_clipboard_image(img_file)
        return img_file

    def start_set_clipboard_event(self, destroy=True):
        """
        开始截取最终屏幕并保存到系统剪切板
        """
        self.set_clipboard_and_save()
        self.cancel_process_event()

    def start_save_file_event(self, event=None):
        """
        另存为截图文件
        """
        init_name = '%s.png' % time.strftime('%Y%m%d%H%M%S', time.localtime())
        if file_name := filedialog.asksaveasfilename(filetypes=[('Save Image file', '*.png')], initialfile=init_name):
            shutil.move(self.set_clipboard_and_save(), file_name)
        self.cancel_process_event()

    def float_show_screenshot_event(self):
        """
        悬浮显示截图
        """
        _s_m_x = tk.IntVar()  # 鼠标开始x位置 #
        _s_m_y = tk.IntVar()  # 鼠标开始y位置 #
        _s_r_x = tk.IntVar()  # 窗体开始x位置 #
        _s_r_y = tk.IntVar()  # 窗体开始y位置 #
        _e_m_x = tk.IntVar()  # 鼠标结束x位置 #
        _e_m_y = tk.IntVar()  # 鼠标结束y位置 #

        def _start_pos(event):
            _s_m_x.set(event.x_root)
            _s_m_y.set(event.y_root)
            _s_r_x.set(top.winfo_x())
            _s_r_y.set(top.winfo_y())

        def _end_pos(event):
            _e_m_x.set(event.x_root)
            _e_m_y.set(event.y_root)
            new_x = _e_m_x.get() - _s_m_x.get() + _s_r_x.get()
            new_y = _e_m_y.get() - _s_m_y.get() + _s_r_y.get()
            top.geometry('+{}+{}'.format(new_x, new_y))

        def _destroy(event):
            top.destroy()

        img_file = self.set_clipboard_and_save()
        self.cancel_process_event()
        top = tk.Tk()
        self.float_img = ImageTk.PhotoImage(Image.open(img_file))
        tk.Label(top, image=self.float_img).pack()
        top.bind('<Button-1>', _start_pos)
        top.bind('<B1-Motion>', _end_pos)
        top.bind('<ButtonRelease-1>', _end_pos)
        top.bind('<Button-3>', _destroy)
        self.set_headless(top, full=False)
        top.mainloop()


def set_clipboard_image(image_file):
    """
    复制图片到系统剪切板实现
    """
    if os.name == 'posix':
        cmd = f"xclip -selection clipboard -target image/png {image_file}"
        os.system(cmd)
    else:
        import io
        import win32clipboard
        image = Image.open(image_file)
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()


def main():
    if _dir := os.path.dirname(__file__):
        os.chdir(_dir)
    Style.load_settings()
    shot = ScreenShot()
    shot.run()


if __name__ == '__main__':
    main()

