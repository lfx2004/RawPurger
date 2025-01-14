import tkinter as tk
from tkinter import filedialog, messagebox
import os
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS
import exifread
from datetime import datetime
from send2trash import send2trash


class DelMode:
    DELRAW = 0  # 删除RAW
    DELJPG = 1  # 删除JPG


class PictCleaner:
    picture_list = []
    jpg_list = []
    raw_list = []
    del_list = []
    jpg_suffixes_list = [".jpg", ".jpeg"]  # 所有jpg格式后缀
    raw_suffixes_list = [".nef", ".cr2", ".cr3", ".arw", ".raf", ".orf", ".dng", ".rwl", ".pef", ".rw2",
                         ".3fr"]  # 所有raw格式后缀
    search_path = ''

    def __init__(self, root):
        self.root = root
        self.root.title("Raw Purger")
        self.root.geometry("750x600")

        # 初始化缩略图大小
        self.thumbnail_size = 120

        # 选择文件夹按钮
        self.path_frame = tk.Frame(root)
        self.path_frame.pack(padx=10, pady=10, fill=tk.X)
        self.folder_button = tk.Button(self.path_frame, text="选择文件夹", command=self.select_folder)
        self.folder_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.path_label = tk.Label(self.path_frame, text=self.search_path)
        self.path_label.pack(side=tk.LEFT, padx=5, pady=5)

        # 显示搜索到的照片总数
        self.photo_count_label = tk.Label(self.path_frame, text="找到 0 张冗余照片")
        self.photo_count_label.pack(side=tk.RIGHT, padx=5, pady=5)

        self.thumbnail_frame = tk.Frame(root)  # 用于显示缩略图的区域
        self.thumbnail_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.operate_frame = tk.Frame(root)
        self.operate_frame.pack(padx=10, pady=10, fill=tk.X, side=tk.BOTTOM)

        # 删除模式选择
        self.mode_var = tk.IntVar(value=DelMode.DELRAW)
        self.search_recursive_var = tk.BooleanVar(value=True)  # 默认勾选递归查找
        self.radio_frame = tk.Frame(self.operate_frame)
        self.radio_frame.pack(side=tk.LEFT, padx=5, pady=5)
        self.del_raw_radio = tk.Radiobutton(self.radio_frame, text="删除冗余RAW", variable=self.mode_var,
                                            value=DelMode.DELRAW, command=self.search_action)
        self.del_raw_radio.pack(side=tk.LEFT, padx=5, pady=5)
        self.del_jpg_radio = tk.Radiobutton(self.radio_frame, text="删除冗余JPG", variable=self.mode_var,
                                            value=DelMode.DELJPG, command=self.search_action)
        self.del_jpg_radio.pack(side=tk.LEFT, padx=5, pady=5)
        self.recursive_check = tk.Checkbutton(self.radio_frame, text="递归文件夹", variable=self.search_recursive_var, command=self.search_action)
        self.recursive_check.pack(side=tk.LEFT, padx=5, pady=5)

        # Clean按钮
        self.clean_button = tk.Button(self.operate_frame, text="   执行删除   ", command=self.clean_action)
        self.clean_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # 设置缩略图显示区域
        self.canvas = tk.Canvas(self.thumbnail_frame, bg='white')
        self.scrollbar = tk.Scrollbar(self.thumbnail_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 鼠标滚轮事件绑定
        self.root.bind("<Control-MouseWheel>", self.adjust_thumbnail_size)
        self.root.bind("<MouseWheel>", self.on_mouse_wheel)  # 绑定滚轮事件来滚动视图

        # 初始化按钮状态
        self.update_button_states()

    def adjust_thumbnail_size(self, event):
        """调整缩略图大小"""
        delta = 10 if event.delta > 0 else -10
        self.thumbnail_size = max(50, min(300, self.thumbnail_size + delta))
        self.display_thumbnails()

    def on_mouse_wheel(self, event):
        """滚动事件处理，控制Canvas上下滚动"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.search_path = folder_selected
            self.path_label.config(text=self.search_path)
            self.update_button_states()  # 更新按钮状态
            self.search_action()

    def search_action(self):
        if self.search_path == '':
            return
        self.update_del_list(mode=self.mode_var.get(), recursive=self.search_recursive_var.get())
        self.display_thumbnails()  # 显示待删除照片的缩略图
        self.update_button_states()  # 更新按钮状态
        self.photo_count_label.config(text=f"找到 {len(self.del_list)} 张冗余照片")
        if len(self.del_list) == 0:
            messagebox.showinfo("提示", "没有找到任何冗余照片。")

    def clean_action(self):
        num_files = len(self.del_list)
        if num_files == 0:
            messagebox.showinfo("信息", "没有文件需要删除。")
            return

        # 弹出二次确认
        response = messagebox.askyesno("确认删除", f"您确定要删除 {num_files} 个文件吗？")
        if response:
            # 开始删除文件
            for file_name in self.del_list:
                file_path = os.path.join(self.search_path, file_name)
                file_path = os.path.normpath(file_path)
                if os.path.exists(file_path):
                    send2trash(file_path)  # 将文件移动到回收站
                    print(f"File {file_name} has been moved to the recycle bin.")
            messagebox.showinfo("信息", "文件删除成功。请检查回收站！")
            self.del_list.clear()  # 清空已删除的文件列表
            self.update_button_states()  # 更新按钮状态
            self.display_thumbnails()
            self.photo_count_label.config(text="找到 0 张冗余照片")

    def display_thumbnails(self):
        # 清空当前的缩略图显示
        self.canvas.delete("all")

        # 使用Frame作为缩略图容器
        frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=frame, anchor='nw')

        # 动态计算每行显示的缩略图数量
        canvas_width = self.canvas.winfo_width() or 700  # 防止初始宽度为0
        thumbnails_per_row = max(1, canvas_width // (self.thumbnail_size + 20))

        row = 0
        col = 0

        for img_file in self.del_list:
            img_path = os.path.join(self.search_path, img_file)
            try:
                img = Image.open(img_path)
                img.thumbnail((self.thumbnail_size, self.thumbnail_size))  # 生成缩略图
                img_tk = ImageTk.PhotoImage(img)

                # 创建一个Frame来包裹缩略图和文件名标签
                thumbnail_frame = tk.Frame(frame, width=self.thumbnail_size + 20, height=self.thumbnail_size + 40)
                thumbnail_frame.grid(row=row, column=col, padx=5, pady=5)
                thumbnail_frame.grid_propagate(False)  # 固定Frame大小

                # 在Frame中显示缩略图
                label = tk.Label(thumbnail_frame, image=img_tk)
                label.image = img_tk  # 保持引用，防止图片被回收
                label.pack()

                # 在缩略图下方显示文件名
                filename_label = tk.Label(thumbnail_frame, text=img_file, wraplength=self.thumbnail_size,
                                          anchor="center")
                filename_label.pack()

                col += 1
                if col >= thumbnails_per_row:  # 如果到达每行最大缩略图数，换行
                    col = 0
                    row += 1

            except Exception as e:
                print(f"无法打开 {img_path}: {e}")

        frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def update_button_states(self):
        """更新按钮状态"""
        if not self.del_list:
            self.clean_button.config(state=tk.DISABLED)
        else:
            self.clean_button.config(state=tk.NORMAL)

    @staticmethod
    def get_exif_data(image_path):
        """提取JPG文件的EXIF数据，包括拍摄日期、修改日期"""
        exif_data = {}
        try:
            image = Image.open(image_path)
            info = image._getexif()
            if info is not None:
                for tag, value in info.items():
                    tag_name = TAGS.get(tag, tag)
                    exif_data[tag_name] = value
        except Exception as e:
            print(f"Error extracting EXIF from {image_path}: {e}")
        return exif_data

    @staticmethod
    def get_raw_metadata(raw_path):
        """提取RAW文件的元数据"""
        raw_exif_data = {}
        try:
            with open(raw_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                if "EXIF DateTimeOriginal" in tags:
                    raw_exif_data['DateTimeOriginal'] = tags["EXIF DateTimeOriginal"].values
        except Exception as e:
            print(f"Error extracting EXIF from {raw_path}: {e}")
        return raw_exif_data

    @staticmethod
    def parse_exif_datetime(date_str):
        """将EXIF中的日期时间字符串转换为datetime对象"""
        try:
            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        except Exception as e:
            print(f"Error parsing EXIF date string '{date_str}': {e}")
            return None

    def detect_accordance(self, jpg_name, raw_name):
        """判断两个照片文件是否相同，相同则返回True"""
        jpg_path1 = os.path.join(self.search_path, jpg_name)
        raw_path2 = os.path.join(self.search_path, raw_name)

        jpg_exif = self.get_exif_data(jpg_path1)
        raw_exif = self.get_raw_metadata(raw_path2)

        jpg_date = self.parse_exif_datetime(jpg_exif.get("DateTimeOriginal"))
        raw_date = self.parse_exif_datetime(raw_exif.get("DateTimeOriginal"))
        if jpg_date is None or raw_date is None:
            return False
        if abs((jpg_date - raw_date).total_seconds()) > 10:
            return False

        jpg_mod_time = os.path.getmtime(jpg_path1)
        raw_mod_time = os.path.getmtime(raw_path2)
        if abs(jpg_mod_time - raw_mod_time) > 10:
            return False
        return True

    def walk_directory(self, directory, recursive):
        """递归或非递归地遍历指定目录，收集图片文件"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in self.jpg_suffixes_list or ext in self.raw_suffixes_list:
                    yield os.path.relpath(os.path.join(root, file), directory)
            if not recursive:
                break  # 如果是非递归查找，则只遍历当前目录

    def update_del_list(self, mode=DelMode.DELRAW, recursive=True):
        self.picture_list.clear()
        self.raw_list.clear()
        self.jpg_list.clear()
        self.del_list.clear()

        # 根据是否递归查找来获取图片列表
        self.picture_list = list(self.walk_directory(self.search_path, recursive))

        self.jpg_list = [item for item in self.picture_list if
                         os.path.splitext(item)[1].lower() in self.jpg_suffixes_list]
        self.raw_list = [item for item in self.picture_list if
                         os.path.splitext(item)[1].lower() in self.raw_suffixes_list]

        if mode == DelMode.DELRAW:
            for raw_item in self.raw_list:
                same_name_jpg_list = [item for item in self.jpg_list if
                                      os.path.splitext(item)[0] == os.path.splitext(raw_item)[0]]
                if len(same_name_jpg_list) > 0:
                    for jpg_item in same_name_jpg_list:
                        if self.detect_accordance(jpg_item, raw_item):
                            self.del_list.append(raw_item)
                            break
        elif mode == DelMode.DELJPG:
            for jpg_item in self.jpg_list:
                same_name_raw_list = [item for item in self.raw_list if
                                      os.path.splitext(item)[0] == os.path.splitext(jpg_item)[0]]
                if len(same_name_raw_list) > 0:
                    for raw_item in same_name_raw_list:
                        if self.detect_accordance(jpg_item, raw_item):
                            self.del_list.append(jpg_item)
                            break
        print("del_list: " + self.del_list.__str__())


if __name__ == "__main__":
    root = tk.Tk()
    app = PictCleaner(root)
    root.mainloop()
