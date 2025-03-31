from acrylic_window import AcrylicWindow, AcrylicEffect
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QScrollArea, QTextEdit, QMenu, QFileDialog,
                               QApplication, QInputDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QIcon, QAction


class KnowledgeManager(AcrylicWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("知库管理")
        self.resize(1000, 600)

        # 亚克力效果设置
        self.acrylic.set_blur_radius(20)
        self.acrylic.set_tint_color(QColor(255, 255, 255, 200))
        self.acrylic.set_opacity(100)

        # 初始化数据
        self.tabs = []
        self.current_tab_id = -1
        self._init_ui()

    def _init_ui(self):
        # 主布局
        main_widget = QWidget()
        main_widget.setStyleSheet("background: transparent;")
        layout = self.layout()  # 获取AcrylicWindow的布局
        layout.addWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部标题栏
        self._init_title_bar(main_layout)

        # 主体布局
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # 左侧标签栏
        self._init_sidebar(body_layout)

        # 右侧内容区
        self._init_content_area(body_layout)

        main_layout.addLayout(body_layout)

    def _init_title_bar(self, parent_layout):
        # 标题栏容器
        title_bar = QWidget()
        title_bar.setFixedHeight(48)
        title_bar.setStyleSheet("""
            background: rgba(255,255,255,0.1);
            border-bottom: 1px solid rgba(0,0,0,0.1);
        """)

        # 标题栏布局
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 0, 16, 0)

        # 左侧操作按钮
        btn_group = QHBoxLayout()
        self.new_btn = self._create_tool_btn("＋ 新建", self.create_note_tab)
        # self.save_btn = self._create_tool_btn("💾 保存", self.save_content)
        btn_group.addWidget(self.new_btn)
        # btn_group.addWidget(self.save_btn)

        # 中间标题
        self.title_label = QLabel("未命名文档")
        self.title_label.setStyleSheet("""
            QLabel {
                color: rgba(0,0,0,0.8);
                font: 14px 'Microsoft Yahei';
                qproperty-alignment: AlignCenter;
            }
        """)

        # 右侧工具
        tool_group = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("搜索内容...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 4px;
                padding: 4px 12px;
                min-width: 200px;
            }
        """)

        title_layout.addLayout(btn_group)
        title_layout.addWidget(self.title_label, 1)
        title_layout.addWidget(self.search_bar)

        parent_layout.addWidget(title_bar)

    def _init_sidebar(self, parent_layout):
        # 左侧标签栏
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("""
            background: rgba(255,255,255,0.1);
            border-right: 1px solid rgba(0,0,0,0.1);
        """)

        # 标签列表
        self.tab_list = QScrollArea()
        self.tab_list.setWidgetResizable(True)
        self.tab_list.setStyleSheet("border: none; background: transparent;")

        tab_container = QWidget()
        self.tab_layout = QVBoxLayout(tab_container)
        self.tab_layout.setSpacing(4)

        self.tab_list.setWidget(tab_container)

        # 布局
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.addWidget(self.tab_list)
        parent_layout.addWidget(sidebar)

    def _init_content_area(self, parent_layout):
        # 右侧内容区
        content_area = QWidget()
        content_area.setStyleSheet("background: transparent;")

        # 编辑器
        self.editor = QTextEdit()
        self.editor.setStyleSheet("""
            QTextEdit {
                background: transparent;
                color: rgba(0,0,0,0.8);
                font: 14px 'Microsoft Yahei';
                padding: 24px;
                border: none;
            }
        """)

        # 状态栏
        self.status_bar = QLabel("就绪")
        self.status_bar.setStyleSheet("""
            color: rgba(0,0,0,0.6);
            padding: 8px 16px;
            border-top: 1px solid rgba(0,0,0,0.1);
        """)

        # 布局
        layout = QVBoxLayout(content_area)
        layout.addWidget(self.editor, 1)
        layout.addWidget(self.status_bar)
        parent_layout.addWidget(content_area, 1)

    def _create_tool_btn(self, text, callback):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(0,0,0,0.7);
                padding: 6px 12px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background: rgba(0,0,0,0.05);
            }
            QPushButton:pressed {
                background: rgba(0,0,0,0.1);
            }
        """)
        btn.clicked.connect(callback)
        return btn

    def _create_tab_widget(self):
        """现代风格标签控件"""
        tab = QPushButton()
        tab.setCheckable(True)
        tab.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(0,0,0,0.8);
                padding: 8px 20px;
                text-align: left;
                border-radius: 4px;
                font: 13px 'Microsoft Yahei';
            }
            QPushButton:hover {
                background: rgba(0,0,0,0.05);
            }
            QPushButton:checked {
                background: rgba(0,0,0,0.08);
                font-weight: 500;
                border-right: 3px solid rgba(0,120,215,0.8);
            }
        """)
        return tab

    def create_note_tab(self):
        """创建新笔记标签"""
        tab_id = len(self.tabs)
        new_tab = {
            "id": tab_id,
            "title": f"未命名笔记 {tab_id + 1}",
            "content": "",
            "widget": self._create_tab_widget()
        }
        self.tabs.append(new_tab)
        self._update_tab_display()
        self.switch_tab(tab_id)

    def _create_tab_widget(self):
        """创建标签控件"""
        tab = QPushButton()
        tab.setCheckable(True)
        tab.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(0,0,0,0.8);
                padding: 8px 16px;
                text-align: left;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(0,0,0,0.05);
            }
            QPushButton:checked {
                background: rgba(0,0,0,0.1);
                font-weight: 500;
            }
        """)
        tab.setContextMenuPolicy(Qt.CustomContextMenu)
        tab.customContextMenuRequested.connect(self.show_tab_menu)
        return tab

    def show_tab_menu(self, pos):
        """显示标签右键菜单"""
        widget = self.sender()
        menu = QMenu()

        actions = [
            ("重命名", lambda: self.rename_tab(widget)),
            ("删除", lambda: self.delete_tab(widget)),
            ("导出", lambda: self.export_tab(widget))
        ]

        for text, callback in actions:
            action = QAction(text, self)
            action.triggered.connect(callback)
            menu.addAction(action)

        menu.exec(widget.mapToGlobal(pos))

    def _update_tab_display(self):
        """安全更新标签显示"""
        # 清理旧控件
        while self.tab_layout.count():
            item = self.tab_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 重建所有标签
        for index, tab in enumerate(self.tabs):
            widget = self._create_tab_widget()
            widget.setText(tab["title"])
            widget.setChecked(index == self.current_tab_id)
            widget.clicked.connect(lambda _, idx=index: self.switch_tab(idx))
            self.tab_layout.addWidget(widget)
            tab["widget"] = widget  # 更新引用

    def switch_tab(self, tab_id):
        """增强版标签切换"""
        if 0 <= tab_id < len(self.tabs):
            # 保存旧标签内容
            if self.current_tab_id != -1:
                self.tabs[self.current_tab_id]["content"] = self.editor.toPlainText()

            # 更新当前标签
            self.current_tab_id = tab_id
            current_tab = self.tabs[tab_id]

            # 更新界面
            self.editor.setText(current_tab["content"])
            self.title_label.setText(current_tab["title"])

            # 更新选中状态
            for i, tab in enumerate(self.tabs):
                if tab["widget"]:
                    tab["widget"].setChecked(i == tab_id)

            self._update_status(f"已切换到：{current_tab['title']}")

    # 以下是需要补充的关联方法
    def rename_tab(self, widget):
        """重命名标签"""
        tab = next((t for t in self.tabs if t["widget"] == widget), None)
        if tab:
            new_name, ok = QInputDialog.getText(
                self, "重命名", "新名称：", text=tab["title"])
            if ok and new_name:
                tab["title"] = new_name
                self._update_tab_display()
                self._update_status(f"已重命名为：{new_name}")

    def delete_tab(self, widget):
        """增强版删除逻辑"""
        try:
            delete_index = next(i for i, t in enumerate(self.tabs) if t["widget"] == widget)
        except StopIteration:
            return

        confirm = QMessageBox.question(
            self, "确认删除",
            f"确定删除 {self.tabs[delete_index]['title']} 吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            # 保存当前内容
            if delete_index == self.current_tab_id:
                self.save_content()

            # 调整索引
            if self.current_tab_id >= delete_index:
                self.current_tab_id -= 1

            # 执行删除
            del self.tabs[delete_index]
            widget.deleteLater()

            # 自动切换
            if self.tabs:
                new_index = max(0, min(delete_index, len(self.tabs) - 1))
                self.switch_tab(new_index)
            else:
                self.current_tab_id = -1
                self.editor.clear()
                self.title_label.setText("未命名文档")

            self._update_tab_display()
            self._update_status(f"已删除标签")

    def export_tab(self, widget):
        """导出标签内容"""
        tab = next((t for t in self.tabs if t["widget"] == widget), None)
        if tab:
            path, _ = QFileDialog.getSaveFileName(
                self, "导出内容", "", "文本文件 (*.txt)")
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(tab["content"])
                    self._update_status(f"已导出到：{path}", "#64B5F6")
                except Exception as e:
                    QMessageBox.critical(self, "导出错误", str(e))

    def _update_status(self, message, color="rgba(0,0,0,0.6)"):
        """更新状态栏"""
        self.status_bar.setText(message)
        self.status_bar.setStyleSheet(f"color: {color}; padding: 8px 16px;")
        QTimer.singleShot(5000, lambda: self.status_bar.setText("就绪"))



if __name__ == "__main__":
    app = QApplication([])
    app.setFont(QFont("微软雅黑"))
    window = KnowledgeManager()
    window.show()

    app.exec()