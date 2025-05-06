import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox,
    QGroupBox, QCheckBox, QDoubleSpinBox, QSizePolicy, QProgressDialog, QDialog, QTextEdit
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import  QDragEnterEvent, QDropEvent, QDesktopServices

import pandas as pd
import openpyxl

class ModernLineEdit(QLineEdit):
    def __init__(self, parent=None, mode='file', default_filename=''):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.mode = mode
        self.default_filename = default_filename
        self.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toLocalFile()
            if self.mode == 'file':
                self.setText(url)
            elif self.mode == 'folder':
                if self.default_filename == '':
                    url = os.path.dirname(url)
                else:
                    if os.path.isdir(url):
                        url = os.path.join(url, self.default_filename)
                    elif os.path.isfile(url):
                        url = os.path.join(os.path.dirname(url), self.default_filename)
                self.setText(url)

class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)

class SCFA_Marker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_variables()
        # 监听文件路径变化，自动设置输出目录
        self.lineEdit_file_path.textChanged.connect(self._auto_set_save_dir)

    def init_variables(self):
        self.filename = ""
        self.save_path = ""
        self.group_list = []
        self.faild_group = []

    def init_ui(self):
        self.setWindowTitle("SCFA Marker v1.4")
        self.setMinimumSize(800, 600)

        # 添加菜单栏和Help菜单
        menubar = self.menuBar()
        help_menu = menubar.addMenu('Help')
        open_github_action = help_menu.addAction('Open GitHub')
        open_github_action.triggered.connect(self.open_help)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # File group
        file_group = self.create_file_group()
        main_layout.addWidget(file_group)

        # Params group
        params_group = self.create_params_group()
        main_layout.addWidget(params_group)

        # Run button
        self.run_button = ModernButton("Start Processing")
        self.run_button.clicked.connect(self.on_pushButton_run)
        self.run_button.setFixedHeight(50)
        self.run_button.setToolTip(
            "Click to start processing data.\n"
            "The program will:\n"
            "1. Read and process the CSV file\n"
            "2. Mark sample status based on standard range\n"
            "3. Generate result files\n"
            "4. If group splitting is enabled, generate grouped results"
        )
        main_layout.addWidget(self.run_button)

        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 1em;
                padding-top: 1em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                font-size: 12px;
                color: #333;
            }
            QDoubleSpinBox {
                padding: 5px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QCheckBox {
                font-size: 12px;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)

    def create_file_group(self):
        group = QGroupBox("File Settings")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        input_layout = QHBoxLayout()
        self.lineEdit_file_path = ModernLineEdit(mode='file')
        self.lineEdit_file_path.setPlaceholderText("Drag and drop CSV files here or click to select files (multi-select supported)")
        self.lineEdit_file_path.setToolTip(
            "Select the CSV files to process (multi-select supported).\n"
            "The file should contain the following columns:\n"
            "- Molecule: Molecule name\n"
            "- Replicate: Sample identifier\n"
            "- Quantification: Quantification value\n"
            "- Sample Type: Sample type\n"
            "- Analyte Concentration: Analyte concentration\n"
            "- Exclude From Calibration: Exclude from calibration or not"
        )
        input_layout.addWidget(self.lineEdit_file_path)
        select_file_btn = ModernButton("Select File")
        select_file_btn.clicked.connect(self.on_pushButton_open_files)
        select_file_btn.setToolTip("Click to select CSV files to process (multi-select supported)")
        input_layout.addWidget(select_file_btn)
        layout.addLayout(input_layout)
        output_layout = QHBoxLayout()
        self.lineEdit_save_dir_path = ModernLineEdit(mode='folder')
        self.lineEdit_save_dir_path.setPlaceholderText("Drag and drop a folder here or click to select output directory")
        self.lineEdit_save_dir_path.setToolTip(
            "Select the folder to save the processed results.\n"
            "The program will generate the following files in this folder:\n"
            "- MARKED_*.xlsx: File with marked results\n"
            "- GROUPED_*.xlsx: Grouped result file (if group splitting is enabled)"
        )
        output_layout.addWidget(self.lineEdit_save_dir_path)
        select_dir_btn = ModernButton("Select Directory")
        select_dir_btn.clicked.connect(self.on_pushButton_save_dir_path)
        select_dir_btn.setToolTip("Click to select the folder to save results")
        output_layout.addWidget(select_dir_btn)
        layout.addLayout(output_layout)
        return group

    def create_params_group(self):
        group = QGroupBox("Parameter Settings")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        # Dilution factor
        dilution_layout = QHBoxLayout()
        dilution_label = QLabel("Dilution Factor:")
        self.doubleSpinBox_dilution = QDoubleSpinBox()
        self.doubleSpinBox_dilution.setRange(0.01, 10000)
        self.doubleSpinBox_dilution.setValue(1.0)
        self.doubleSpinBox_dilution.setSingleStep(0.01)
        self.doubleSpinBox_dilution.setToolTip(
            "Set the dilution factor for the samples. All results will be automatically multiplied by this value.\n"
            "- Default is 1 (no adjustment)\n"
            "- If the sample was diluted during preprocessing, enter the actual dilution factor (e.g., 2, 5, etc.)\n"
            "- Only when the dilution factor is not 1, the result table will show additional dilution-adjusted columns\n"
        )
        dilution_layout.addWidget(dilution_label)
        dilution_layout.addWidget(self.doubleSpinBox_dilution)
        dilution_layout.addStretch()
        layout.addLayout(dilution_layout)
        # Coefficient settings
        coeff_layout = QHBoxLayout()
        min_coeff_label = QLabel("Min Coefficient:")
        self.doubleSpinBox_mini_coe_value = QDoubleSpinBox()
        self.doubleSpinBox_mini_coe_value.setRange(0, 10)
        self.doubleSpinBox_mini_coe_value.setValue(0.8)
        self.doubleSpinBox_mini_coe_value.setSingleStep(0.1)
        self.doubleSpinBox_mini_coe_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doubleSpinBox_mini_coe_value.setToolTip("Set the minimum coefficient for the standard range. Actual minimum = standard min × this coefficient.")
        coeff_layout.addWidget(min_coeff_label)
        coeff_layout.addWidget(self.doubleSpinBox_mini_coe_value)
        coeff_layout.addSpacing(20)
        max_coeff_label = QLabel("Max Coefficient:")
        self.doubleSpinBox_max_coe_value = QDoubleSpinBox()
        self.doubleSpinBox_max_coe_value.setRange(0, 10)
        self.doubleSpinBox_max_coe_value.setValue(1.5)
        self.doubleSpinBox_max_coe_value.setSingleStep(0.1)
        self.doubleSpinBox_max_coe_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doubleSpinBox_max_coe_value.setToolTip("Set the maximum coefficient for the standard range. Actual maximum = standard max × this coefficient.")
        coeff_layout.addWidget(max_coeff_label)
        coeff_layout.addWidget(self.doubleSpinBox_max_coe_value)
        layout.addLayout(coeff_layout)
        # Group options
        group_option_layout = QHBoxLayout()
        self.checkBox_split_by_group = QCheckBox("Split by Group")
        self.checkBox_split_by_group.setChecked(False)
        self.checkBox_split_by_group.setToolTip(
            "If checked, the program will split the data by group and generate separate result files.\n"
            "Each group's data will be saved in a separate sheet for further analysis.\n"
            "If not checked, only a summary result will be generated."
        )
        self.checkBox_split_by_group.stateChanged.connect(self.on_split_group_changed)
        group_option_layout.addWidget(self.checkBox_split_by_group)
        group_label = QLabel("Group List:")
        self.lineEdit_group_list = ModernLineEdit()
        self.lineEdit_group_list.setPlaceholderText("e.g.: group1, group2, group3")
        self.lineEdit_group_list.setToolTip(
            "Enter the group names to analyze, separated by commas.\n"
            "These group names should match the identifiers in the Replicate column of the CSV file.\n"
            "For example: if Replicate contains 'WT_1', 'WT_2', 'KO_1', 'KO_2',\n"
            "then the group list should be 'WT, KO'"
        )
        group_option_layout.addWidget(group_label)
        group_option_layout.addWidget(self.lineEdit_group_list)
        control_label = QLabel("Control Group:")
        self.lineEdit_control_group = ModernLineEdit()
        self.lineEdit_control_group.setPlaceholderText("Enter control group name")
        self.lineEdit_control_group.setToolTip(
            "Enter the name of the control group.\n"
            "This name should match one of the group names in the group list.\n"
            "The control group will be prioritized in the output."
        )
        group_option_layout.addWidget(control_label)
        group_option_layout.addWidget(self.lineEdit_control_group)
        group_option_layout.setSpacing(10)
        layout.addLayout(group_option_layout)
        self.lineEdit_group_list.setEnabled(False)
        self.lineEdit_control_group.setEnabled(False)
        return group

    def on_pushButton_open_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            'Select CSV files (multi-select supported)',
            '',
            'CSV files (*.csv);;All files (*.*)'
        )
        if file_paths:
            self.lineEdit_file_path.setText(';'.join(file_paths))
            # 自动设置输出目录为第一个文件的同目录
            self.lineEdit_save_dir_path.setText(os.path.dirname(file_paths[0]))
        self.selected_file_paths = file_paths

    def on_pushButton_save_dir_path(self):
        save_dir_path = QFileDialog.getExistingDirectory(
            self,
            'Select output directory',
            ''
        )
        if save_dir_path:
            self.lineEdit_save_dir_path.setText(save_dir_path)

    def show_result_dialog(self, title, content):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(700, 500)
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(content)
        layout.addWidget(text_edit)
        btn = QPushButton("OK")
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.exec_()

    def on_pushButton_run(self):
        # 支持多文件批量处理
        file_path_text = self.lineEdit_file_path.text()
        file_paths = [f.strip() for f in file_path_text.split(';') if f.strip()]
        self.save_path = self.lineEdit_save_dir_path.text()
        if not self._validate_inputs(file_paths):
            return
        all_msgs = []
        progress = QProgressDialog("Processing files...", "Cancel", 0, len(file_paths), self)
        progress.setWindowTitle("Processing progress")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        for i, file_path in enumerate(file_paths):
            progress.setValue(i)
            progress.setLabelText(f"Processing file {i+1}/{len(file_paths)}: {os.path.basename(file_path)}")
            QApplication.processEvents()
            if progress.wasCanceled():
                all_msgs.append("User canceled batch processing.")
                break
            self.filename = file_path
            try:
                msg = self.process_file(batch_mode=True)
                file_msg = f"Processed file: {os.path.basename(file_path)}\n" + msg
                all_msgs.append(file_msg)
            except Exception as e:
                all_msgs.append(f"Processed file: {os.path.basename(file_path)}\nFile processing failed: {str(e)}")
        progress.setValue(len(file_paths))
        self.show_result_dialog('Batch processing completed', '\n\n'.join(all_msgs))

    def on_split_group_changed(self, state):
        """处理分组选项状态改变事件"""
        is_enabled = state == Qt.Checked
        self.lineEdit_group_list.setEnabled(is_enabled)
        self.lineEdit_control_group.setEnabled(is_enabled)
        
        # 更新提示文本
        if is_enabled:
            self.lineEdit_group_list.setPlaceholderText("e.g.: group1, group2, group3")
            self.lineEdit_control_group.setPlaceholderText("Enter control group name")
        else:
            self.lineEdit_group_list.setPlaceholderText("Available after enabling group splitting")
            self.lineEdit_control_group.setPlaceholderText("Available after enabling group splitting")

    def _validate_inputs(self, file_paths=None):
        """验证输入数据"""
        if file_paths is None:
            file_path_text = self.lineEdit_file_path.text()
            file_paths = [f.strip() for f in file_path_text.split(';') if f.strip()]
        if not file_paths or not all(os.path.isfile(f) for f in file_paths):
            QMessageBox.warning(
                self,
                'Warning',
                'Please select files to process.'
            )
            return False
        if not self.save_path:
            QMessageBox.warning(
                self,
                'Warning',
                'Please select the output directory.'
            )
            return False
        # 只有在启用分组功能时才验证组别列表
        if self.checkBox_split_by_group.isChecked():
            if not self.lineEdit_group_list.text():
                QMessageBox.warning(
                    self,
                    'Warning',
                    'Please enter group list.'
                )
                return False
            if not self.lineEdit_control_group.text():
                QMessageBox.warning(
                    self,
                    'Warning',
                    'Please enter control group name.'
                )
                return False
        return True

    def process_file(self, batch_mode=False):
        try:
            df = pd.read_csv(self.filename)
            # 设置min_val和max_val的系数
            min_coeff = self.doubleSpinBox_mini_coe_value.value()
            max_coeff = self.doubleSpinBox_max_coe_value.value()
            dilution = self.doubleSpinBox_dilution.value()

            # only keep 6 columns
            df = df[['Molecule', "Replicate", 'Quantification', 'Sample Type', 'Analyte Concentration',
                'Exclude From Calibration']]
            # make all str in 'Exclude From Calibration as lower case, convert to str first
            df['Exclude From Calibration'] = df['Exclude From Calibration'].astype(str).str.lower()

            group_list = df["Molecule"].value_counts().index.tolist()
            group_list = list(set(group_list))
            group_list.sort()
            print(f'Start processing file: {os.path.basename(self.filename)}')
            print(f'total molecules:{len(group_list)}')
            # print(group_list)            
            group_dict = {}

            # 记录处理结果
            processed_results = {
                "success": [],
                "failed": []
            }

            for group in group_list:
                try:
                    # print(f'processing {group}...')
                    dft = df[df["Molecule"] == group].copy()
                    dft_i = dft[(dft["Sample Type"] == "Standard") & (dft["Exclude From Calibration"] == "false")]
                    min_val = dft_i["Analyte Concentration"].min()
                    max_val = dft_i["Analyte Concentration"].max()
                    # 标准范围（原始）
                    min_val_str = int(min_val)  if min_val.is_integer() else round(min_val, 2)
                    max_val_str = int(max_val)  if max_val.is_integer() else round(max_val, 2)
                    dft["Standard Range"] = f"{min_val_str} - {max_val_str}"

                    dft[["Quantification", "Unit"]] = dft["Quantification"].str.split(' ', expand=True)
                    dft["Quantification"] = pd.to_numeric(dft["Quantification"], errors='coerce')

                    # 稀释修正后列，仅当dilution!=1时生成
                    if dilution != 1.0:
                        dft["Quantification(diluted_adjusted)"] = dft["Quantification"] * dilution
                        min_val_diluted = min_val * dilution
                        max_val_diluted = max_val * dilution
                        min_val_str_dil = int(min_val_diluted) if min_val_diluted.is_integer() else round(min_val_diluted, 2)
                        max_val_str_dil = int(max_val_diluted) if max_val_diluted.is_integer() else round(max_val_diluted, 2)
                        dft["Standard Range(diluted_adjusted)"] = f"{min_val_str_dil} - {max_val_str_dil}"

                    min_val_status = min_val * min_coeff
                    max_val_status = max_val * max_coeff

                    # 筛选除了 Standard 之外的样本
                    dft = dft[dft["Sample Type"] != "Standard"]
                    dft.drop(columns=["Sample Type", "Analyte Concentration", "Exclude From Calibration"], inplace=True)

                    def status_func(x):
                        if pd.isna(x):
                            return ""
                        if x < min_val_status:
                            return "Low"
                        elif x > max_val_status:
                            return "High"
                        else:
                            return "In"
                    dft["Standard"] = dft["Quantification"].apply(lambda x: " " if status_func(x) == "In" else "*")
                    dft["Standard Status"] = dft["Quantification"].apply(status_func)

                    group_dict[group] = dft
                    processed_results["success"].append(group)
                except Exception as e:
                    print(f"Processing {group} failed: {str(e)}")
                    processed_results["failed"].append(group)

            # 将字典中的数据框合并为一个数据框, and save to dict named "All"
            group_dict["All"] = pd.concat(group_dict.values(), ignore_index=True)
            # save to all in in excel, key is the sheet name, all is the first sheet
            original_name = os.path.basename(self.filename).split(".")[0]
            save_path_marked = os.path.join(self.save_path, f"MARKED_{original_name}.xlsx")
            with pd.ExcelWriter(save_path_marked) as writer:
                group_dict["All"].to_excel(writer, sheet_name="All", index=False)
                for key in group_dict.keys():
                    if key != "All":
                        group_dict[key].to_excel(writer, sheet_name=key, index=False)
            
            saved_files = [save_path_marked]

            group_processing_results = {"success": [], "failed": []}
            save_path_grouped = None
            if self.checkBox_split_by_group.isChecked():
                try:
                    res_dict = self.process_group(group_dict, dilution)
                    if res_dict:
                        save_path_grouped = os.path.join(self.save_path, f"GROUPED_{original_name}.xlsx")
                        with pd.ExcelWriter(save_path_grouped) as writer:
                            for sheet_name, dft in res_dict.items():
                                # set index name to replicate
                                dft.index.name = "Replicate"
                                dft.to_excel(writer, sheet_name=sheet_name, index=True)
                        group_processing_results["success"].append("Group processing")
                        saved_files.append(save_path_grouped)
                except Exception as e:
                    group_processing_results["failed"].append(f"Group processing: {str(e)}")

            msg = f"File processing completed.\n"
            msg += "Saved files:\n"
            for f in saved_files:
                msg += f"{f}\n"
            msg += "\n"
            if processed_results["success"]:
                msg += f"Successfully processed molecules ({len(processed_results['success'])}):\n"
                msg += ", ".join(processed_results["success"]) + "\n\n"
            if processed_results["failed"]:
                msg += f"Failed molecules ({len(processed_results['failed'])}):\n"
                msg += ", ".join(processed_results["failed"]) + "\n\n"
            if self.checkBox_split_by_group.isChecked():
                if group_processing_results["success"]:
                    msg += "Group processing succeeded\n"
                if group_processing_results["failed"]:
                    msg += f"Group processing failed:\n{group_processing_results['failed'][0]}\n"
            if batch_mode:
                return msg
            else:
                QMessageBox.information(self, 'Processing completed', msg)
            
        except Exception as e:
            import traceback
            error_msg = f"Error occurred during processing:\n{str(e)}\n\nDetailed error information:\n{traceback.format_exc()}"
            if batch_mode:
                return error_msg
            else:
                QMessageBox.critical(self, 'Error', error_msg)
         

    def process_group(self, group_dict, dilution=1.0):
        """
        处理分组数据，将数据按照不同的组别进行拆分和重组
        Args:
            group_dict (dict): 包含所有分组数据的字典
            dilution (float): 稀释倍数
        Returns:
            dict: 处理后的分组数据字典
        """
        # 获取控制组和组别列表
        control_group = self.lineEdit_control_group.text()
        group_list = self._get_group_list()
        if not group_list:
            print("No group list input, skip")
            return {}
        result_dict = {}
        self.faild_group = []
        for sheet_name, df in group_dict.items():
            if sheet_name == 'All':
                continue
            print(f"Processing sheet: {sheet_name}")
            processed_data = self._process_sheet_data(df, group_list, control_group, sheet_name, dilution)
            if processed_data:
                result_dict.update(processed_data)
        return result_dict

    def _get_group_list(self):
        """获取并处理组别列表"""
        group_list_str = self.lineEdit_group_list.text()
        if not group_list_str or group_list_str == "value1, value2, value3":
            return []
            
        return [x.strip() for x in group_list_str.split(",")]
    
    def _process_sheet_data(self, df, group_list, control_group, sheet_name, dilution=1.0):
        """
        处理单个sheet的数据
        Args:
            df (DataFrame): 原始数据框
            group_list (list): 组别列表
            control_group (str): 控制组名称
            sheet_name (str): 当前sheet名称
            dilution (float): 稀释倍数
        Returns:
            dict: 处理后的数据字典
        """
        result_dict = {}
        df = df.copy()
        # 处理Quantification列
        df.loc[df["Standard Status"] == "Out", "Quantification"] = ""
        df["Quantification"] = pd.to_numeric(df["Quantification"], errors='coerce') * dilution
        df = df[["Replicate", "Quantification"]]
        for individual in group_list:
            processed_data = self._process_individual_data(df, individual, control_group)
            if processed_data is not None:
                result_dict[f"{sheet_name}_{individual}"] = processed_data
            else:
                self.faild_group.append(individual)
        return result_dict
    
    def _process_individual_data(self, df, individual, control_group):
        """
        处理单个组别的数据
        
        Args:
            df (DataFrame): 原始数据框
            individual (str): 组别名称
            control_group (str): 控制组名称
            
        Returns:
            DataFrame: 处理后的数据框，如果组别不存在则返回None
        """
        # 筛选特定组别的数据
        df_individual = df[df["Replicate"].str.contains(individual)].copy()
        if df_individual.empty:
            print(f"Group {individual} not found in data")
            return None
            
        # 分割Replicate列
        split_df = df_individual["Replicate"].str.split(f'_{individual}_', expand=True)
        df_individual['Group'] = split_df[0]
        df_individual['Replicate'] = split_df[1]
        df_individual['Individual'] = individual
        
        # 处理Group列
        df_individual["Group"] = df_individual["Group"].str.replace("d_", "") + "_" + df_individual['Individual']
        
        # 转换为透视表
        df_pivot = df_individual.pivot(
            index='Replicate',
            columns='Group',
            values='Quantification'
        )
        df_pivot.index.name = None
        
        # 按控制组优先排序
        df_pivot = df_pivot[sorted(
            df_pivot.columns,
            key=lambda x: control_group in x if x else False,
            reverse=True
        )]
        
        return df_pivot

    def _auto_set_save_dir(self, file_path):
        # 支持多文件时，只取第一个文件
        if file_path:
            first_file = file_path.split(';')[0]
            if os.path.isfile(first_file):
                self.lineEdit_save_dir_path.setText(os.path.dirname(first_file))

    def open_help(self):
        """Open GitHub repository in default browser"""
        url = QUrl("https://github.com/byemaxx/SCFA_Marker")
        QDesktopServices.openUrl(url)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SCFA_Marker()
    window.show()
    sys.exit(app.exec_())


