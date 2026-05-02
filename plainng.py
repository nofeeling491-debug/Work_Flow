import sys
import os
import json
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QPushButton, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QTextEdit, QInputDialog, QMessageBox, QLineEdit)
from PyQt6.QtCore import QTimer, Qt

# Drag & Drop ရအောင် ListWidget ကို Customize လုပ်ခြင်း
class TodoListWidget(QListWidget):
    def __init__(self, start_path, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(False) # Folder အပြင်က ဆွဲသွင်းမှာဖြစ်လို့ False ထားပါ
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.start_path = start_path

    def dragEnterEvent(self, event):
        # Folder သို့မဟုတ် File ဆွဲလာရင် လက်ခံမယ်
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            src_path = url.toLocalFile()
            if os.path.exists(src_path):
                folder_name = os.path.basename(src_path)
                dst_path = os.path.join(self.start_path, folder_name)
                try:
                    # Folder ဆိုရင် copytree၊ File ဆိုရင် copy2 သုံးမယ်
                    if os.path.isdir(src_path):
                        if not os.path.exists(dst_path):
                            shutil.copytree(src_path, dst_path)
                    else:
                        shutil.copy2(src_path, dst_path)
                except Exception as e:
                    print(f"Drop Error: {e}")
        
        # Parent Window ကို Refresh လုပ်ခိုင်းခြင်း
        window = self.window()
        if hasattr(window, 'refresh_data'):
            window.refresh_data()
        event.acceptProposedAction()

class SharedWorkflowApp(QMainWindow):
    def __init__(self, user_name):
        super().__init__()
        self.user_name = user_name
        self.base_path = r"Y:\#昌\#H2\11" 
        self.today_str = datetime.now().strftime("%Y-%m-%d")
        self.work_dir = os.path.join(self.base_path, self.today_str)
        self.db_file = os.path.join(self.work_dir, "shared_stats.json")
        
        self.setup_folders()
        self.init_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(5000)
        self.refresh_data()
    def open_progress_folder(self, item):
        raw_text = item.text()
        # Icon ကို အရင်ဖယ်မယ်
        clean_text = raw_text.replace("⏳", "").strip()
        
        try:
            if "(" in clean_text:
                folder_name = clean_text.split(" (")[0].strip()
                worker_name = clean_text.split("(")[1].replace(")", "").strip()
                
                folder_path = os.path.abspath(os.path.join(self.work_dir, "In-Progress", worker_name, folder_name))
                
                # ၁။ Folder ဖွင့်ခြင်း
                if os.path.exists(folder_path):
                    os.startfile(folder_path)
                
                # ၂။ ကိုယ့် Project ဖြစ်ရင် Window ပြန်ဖော်ခြင်း
                if worker_name == self.user_name:
                    # TaskWindow က ဒီ file ထဲမှာတင် ရှိနေရင် direct ခေါ်လို့ရပါတယ်
                    self.work_win = TaskWindow(self, [folder_name])
                    self.work_win.show()
                    self.work_win.raise_()
                    self.work_win.activateWindow()
        except Exception as e:
            print(f"Error: {e}")
    def setup_folders(self):
        try:
            os.makedirs(self.work_dir, exist_ok=True)
            for sub in ["Start", "In-Progress", "Finished"]:
                os.makedirs(os.path.join(self.work_dir, sub), exist_ok=True)
            os.makedirs(os.path.join(self.work_dir, "In-Progress", self.user_name), exist_ok=True)
        except Exception as e:
            print(f"Folder Setup Error: {e}")

    def init_ui(self):
        self.setWindowTitle(f"Workflow Dashboard - User: {self.user_name}")
        self.setGeometry(100, 100, 1200, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_layout = QVBoxLayout()
        self.stat_label = QLabel("📊 Loading stats...")
        self.stat_label.setStyleSheet("font-size: 18px; font-weight: bold; background: #34495e; color: white; padding: 15px; border-radius: 5px;")
        left_layout.addWidget(self.stat_label)

        cols_layout = QHBoxLayout()
        
        # TO-DO Column
        todo_vbox = QVBoxLayout()
        todo_vbox.addWidget(QLabel("📂 TO-DO (Drop Folders Here)"))
        
        # သေချာအောင် path ကို ထည့်ပေးပါ
        start_folder_path = os.path.join(self.work_dir, "Start")
        self.todo_list = TodoListWidget(start_folder_path)
        
        # Selection Mode ကို ပြင်မယ် (Double click အလုပ်လုပ်ဖို့ SingleSelection က ပိုကောင်းပါတယ်)
        self.todo_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        
        # Double Click Signal ချိတ်ဆက်ခြင်း
        self.todo_list.itemDoubleClicked.connect(self.open_todo_folder)
        
        todo_vbox.addWidget(self.todo_list)
        cols_layout.addLayout(todo_vbox)
        # IN-PROGRESS Column
        self.progress_list = self.create_list_group(cols_layout, "⏳ IN-PROGRESS", is_special=True)
        # In-Progress list မှာ double click signal ချိတ်ဆက်ခြင်း
        self.progress_list.itemDoubleClicked.connect(self.open_progress_folder)
        # FINISHED Column
        finished_vbox = QVBoxLayout()
        finished_vbox.addWidget(QLabel("✅ FINISHED (Files Only)"))
        self.done_list = QListWidget()
        finished_vbox.addWidget(self.done_list)
        
        # View Files Button
        self.btn_view_finished = QPushButton("📂 VIEW ALL FINISHED FILES")
        self.btn_view_finished.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; height: 35px;")
        self.btn_view_finished.clicked.connect(self.open_finished_folder)
        finished_vbox.addWidget(self.btn_view_finished)
        cols_layout.addLayout(finished_vbox)

        left_layout.addLayout(cols_layout)

        self.btn_open_work = QPushButton("🚀 START SELECTED PROJECTS")
        self.btn_open_work.setStyleSheet("background-color: #2ecc71; color: white; height: 50px; font-weight: bold; font-size: 16px;")
        self.btn_open_work.clicked.connect(self.open_work_window)
        left_layout.addWidget(self.btn_open_work)
        main_layout.addLayout(left_layout, stretch=7)

        # Right Column
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("💬 Team Activity Logs:"))
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        right_layout.addWidget(self.chat_display)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Say something...")
        self.chat_input.returnPressed.connect(self.send_chat)
        right_layout.addWidget(self.chat_input)

        self.rank_table = QTableWidget(0, 2)
        self.rank_table.setHorizontalHeaderLabels(["User Name", "Completed"])
        self.rank_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(QLabel("🏆 Today's Leaderboard:"))
        right_layout.addWidget(self.rank_table)
        main_layout.addLayout(right_layout, stretch=3)

    def create_list_group(self, parent_layout, title, is_special=False):
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel(title))
        lw = QListWidget()
        lw.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        if is_special: lw.setStyleSheet("border: 2px solid #3498db; background-color: #ebf5fb;")
        vbox.addWidget(lw)
        parent_layout.addLayout(vbox)
        return lw

    def open_todo_folder(self, item):
        # Start folder ထဲက အဲ့ဒီ folder ရဲ့ လမ်းကြောင်းကို ယူမယ်
        folder_path = os.path.abspath(os.path.join(self.work_dir, "Start", item.text()))
        
        if os.path.exists(folder_path):
            # Windows Explorer နဲ့ ဖွင့်ပေးမှာဖြစ်ပါတယ်
            os.startfile(folder_path)
        else:
            print(f"Folder not found: {folder_path}")

    def open_finished_folder(self):
        f_path = os.path.join(self.work_dir, "Finished")
        if os.path.exists(f_path):
            os.startfile(f_path)

    def refresh_data(self):
        data = self.load_db()
        self.stat_label.setText(f"📊 Total Completed Today: {data.get('total', 0)} Projects")

        # Update Todo
        selected = [i.text() for i in self.todo_list.selectedItems()]
        self.todo_list.clear()
        start_path = os.path.join(self.work_dir, "Start")
        if os.path.exists(start_path):
            items = [f for f in os.listdir(start_path) if os.path.isdir(os.path.join(start_path, f))]
            self.todo_list.addItems(items)
        for i in range(self.todo_list.count()):
            if self.todo_list.item(i).text() in selected:
                self.todo_list.item(i).setSelected(True)

        # Update In-Progress
        self.progress_list.clear()
        p_root = os.path.join(self.work_dir, "In-Progress")
        if os.path.exists(p_root):
            for worker in os.listdir(p_root):
                w_path = os.path.join(p_root, worker)
                if os.path.isdir(w_path):
                    for t in os.listdir(w_path):
                        item = f"{t} ({worker})"
                        self.progress_list.addItem(item)

        # Update Finished (Files Only - Flattened)
        self.done_list.clear()
        f_path = os.path.join(self.work_dir, "Finished")
        if os.path.exists(f_path):
            for f in os.listdir(f_path):
                self.done_list.addItem(f"📄 {f}")

        self.chat_display.setText("\n".join(data.get("logs", [])))
        self.update_leaderboard(data.get("users", {}))

    def update_leaderboard(self, users_dict):
        sorted_users = sorted(users_dict.items(), key=lambda x: x[1][0], reverse=True)
        self.rank_table.setRowCount(len(sorted_users))
        for row, (name, stats) in enumerate(sorted_users):
            self.rank_table.setItem(row, 0, QTableWidgetItem(name))
            self.rank_table.setItem(row, 1, QTableWidgetItem(str(stats[0])))

    def open_work_window(self):
        selected_items = self.todo_list.selectedItems()
        if not selected_items: return
        
        selected_names = [i.text() for i in selected_items]
        data = self.load_db()
        user_p_path = os.path.join(self.work_dir, "In-Progress", self.user_name)
        
        from __main__ import TaskWindow # Ensure TaskWindow is accessible
        success_list = []
        for folder in selected_names:
            src = os.path.join(self.work_dir, "Start", folder)
            dst = os.path.join(user_p_path, folder)
            try:
                shutil.move(src, dst)
                data["logs"].insert(0, f"[{datetime.now().strftime('%H:%M')}] 🚀 {self.user_name} started: {folder}")
                os.startfile(dst)
                success_list.append(folder)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error: {e}")

        self.save_db(data)
        self.refresh_data()
        if success_list:
            self.work_win = TaskWindow(self, success_list)
            self.work_win.show()

    def process_done(self, folders):
        data = self.load_db()
        finished_dir = os.path.join(self.work_dir, "Finished")
        os.makedirs(finished_dir, exist_ok=True) 
        
        for folder in folders:
            src_folder = os.path.join(self.work_dir, "In-Progress", self.user_name, folder)
            if not os.path.exists(src_folder): continue
            try:
                for item_name in os.listdir(src_folder):
                    full_item_path = os.path.join(src_folder, item_name)
                    dst_item_path = os.path.join(finished_dir, item_name)
                    if os.path.exists(dst_item_path):
                        now = datetime.now().strftime("%H%M%S")
                        name, ext = os.path.splitext(item_name)
                        dst_item_path = os.path.join(finished_dir, f"{name}_{now}{ext}")
                    shutil.move(full_item_path, dst_item_path)
                
                shutil.rmtree(src_folder, ignore_errors=True)
                data["total"] += 1
                user_info = data["users"].get(self.user_name, [0, []])
                user_info[0] += 1
                user_info[1].append(folder)
                data["users"][self.user_name] = user_info
                data["logs"].insert(0, f"[{datetime.now().strftime('%H:%M')}] ✅ {self.user_name} finished: {folder}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Save Error: {e}")

        self.save_db(data)
        self.refresh_data()

    def send_chat(self):
        msg = self.chat_input.text().strip()
        if msg:
            data = self.load_db()
            data["logs"].insert(0, f"💬 {self.user_name}: {msg}")
            self.save_db(data)
            self.chat_input.clear()
            self.refresh_data()

    def load_db(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {"total": 0, "users": {}, "logs": []}

    def save_db(self, data):
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e: print(f"DB Save Error: {e}")

# TaskWindow remains the same as your code...
class TaskWindow(QWidget):
    def __init__(self, parent_app, selected_tasks):
        super().__init__()
        self.parent_app = parent_app
        self.selected_tasks = selected_tasks
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("🔥 Active Working Session")
        self.setMinimumSize(400, 300)
        layout = QVBoxLayout()
        self.lbl = QLabel(f"Working on {len(self.selected_tasks)} items:")
        layout.addWidget(self.lbl)
        self.work_list = QListWidget()
        self.work_list.addItems(self.selected_tasks)
        layout.addWidget(self.work_list)
        self.btn_done = QPushButton("✅ MARK SELECTED AS DONE")
        self.btn_done.setFixedHeight(50)
        self.btn_done.clicked.connect(self.complete_task)
        layout.addWidget(self.btn_done)
        self.setLayout(layout)

    def complete_task(self):
        selected_items = self.work_list.selectedItems()
        if not selected_items: return
        selected_names = [item.text() for item in selected_items]
        self.parent_app.process_done(selected_names)
        for item in selected_items:
            self.work_list.takeItem(self.work_list.row(item))
        if self.work_list.count() == 0: self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    name, ok = QInputDialog.getText(None, "Login", "သင့်အမည်ကို ရိုက်ထည့်ပါ:")
    if ok and name.strip():
        window = SharedWorkflowApp(name.strip())
        window.show()
        sys.exit(app.exec())
