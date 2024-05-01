
import sys
import os

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import QLineEdit

from Ui_SCFA_Marker import Ui_MainWindow
import pandas as pd
import openpyxl
from PyQt5 import QtWidgets


class SCFA_Marker(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__() 
        self.setupUi(self)
        # resize
        self.resize(600, 400)
        self.setWindowTitle("SCFA Marker v1.1")
        
        self.lineEdit_file_path = self.make_line_edit_drag_drop(self.lineEdit_file_path, mode='file')
        self.lineEdit_save_dir_path = self.make_line_edit_drag_drop(self.lineEdit_save_dir_path, mode='folder')
        
        self.pushButton_open_file.clicked.connect(self.on_pushButton_open_file)
        self.pushButton_save_dir_path.clicked.connect(self.on_pushButton_save_dir_path)
        self.pushButton_run.clicked.connect(self.on_pushButton_run)
        
        self.filename = ""
        self.save_path = ""
        self.group_list = []
        
        
    
    def on_pushButton_open_file(self):
        file_path = QtWidgets.QFileDialog.getOpenFileName(None, 'Open file', '', 'csv files(*.csv);')[0]
        
        #set the path of the lineEdit
        self.lineEdit_file_path.setText(file_path)
        self.lineEdit_save_dir_path.setText(os.path.dirname(file_path))
        
    def on_pushButton_save_dir_path(self):
        save_dir_path = QtWidgets.QFileDialog.getExistingDirectory(None, 'Open folder', '')
        self.lineEdit_save_dir_path.setText(save_dir_path)
        
        
    def make_line_edit_drag_drop(self, old_lineEdit, mode='file', default_filename=''):
        new_line_edit = FileDragDropLineEdit(old_lineEdit.parent(), mode, default_filename)
        new_line_edit.setText(old_lineEdit.text())
        new_line_edit.setReadOnly(old_lineEdit.isReadOnly())

        # get the position of old_lineEdit in its layout
        layout = old_lineEdit.parent().layout()
        index = layout.indexOf(old_lineEdit)
        position = layout.getItemPosition(index)

        # remove old_lineEdit from its layout
        old_lineEdit.deleteLater()

        # add new_line_edit to its layout
        layout.addWidget(new_line_edit, *position[0:2])  # position is a tuple of 4 elements including (row, column, rowspan, columnspan)

        return new_line_edit
        

    def process_group(self, group_dict):
        # get the group list from the input box
        control_str = self.lineEdit_control_group.text()
        group_list_str = self.lineEdit_group_list.text()
        if not group_list_str or group_list_str == "value1, value2, value3":
            print("No group list input, skip")
            return 
        group_list = group_list_str.split(",")
        group_list = [x.strip() for x in group_list]
        res_dict = {}

        for group, dft in group_dict.items():
            if group == 'All':
                continue
            print(group)
            dft = dft[["Replicate", "Quantification"]].copy()  # 使用副本操作来避免警告
            for indi in group_list:
                dft_i = dft[dft["Replicate"].str.contains(indi)].copy()  # 对筛选结果创建副本
                # 用 split 方法分割 "Replicate" 列，并创建新列
                split_df = dft_i["Replicate"].str.split(f'_{indi}_', expand=True)
                dft_i['Group'], dft_i["Replicate"] = split_df[0], split_df[1]
                dft_i['Individual'] = indi
                dft_i["Group"] = dft_i["Group"].str.replace("d_", "") + "_" + dft_i['Individual']
                dft_i = dft_i.pivot(index='Replicate', columns='Group', values='Quantification')
                dft_i.index.name = None
                dft_i = dft_i[sorted(dft_i.columns, key=lambda x: control_str in x if x else False, reverse=True)]

                # 创建60倍的数据行
                dft_i_2 = dft_i * 60
                cols_name = dft_i_2.columns
                # 构造空行和标题行
                titles_row = pd.DataFrame([cols_name], columns=dft_i_2.columns)
                spacer_row = pd.DataFrame([[""] * dft_i_2.shape[1]], columns=dft_i_2.columns)
                
                # 合并原始数据框、空行、标题行和60倍数据
                dft_i_final = pd.concat([dft_i, spacer_row, titles_row, dft_i_2])
                
                
                # 保存到字典中
                res_dict[f"{group}_{indi}"] = dft_i_final
        
        return res_dict

                    
                    
                    
    def process_file(self):       
        try:
            df = pd.read_csv(self.filename)
            # 设置min_val和max_val的系数
            min_coeff = self.doubleSpinBox_mini_coe_value.value()
            max_coeff = self.doubleSpinBox_max_coe_value.value()

            
            # only keep 6 columns
            df = df[['Molecule', "Replicate", 'Quantification', 'Sample Type', 'Analyte Concentration',
                'Exclude From Calibration']]
            # make all str in 'Exclude From Calibration as lower case, convert to str first
            df['Exclude From Calibration'] = df['Exclude From Calibration'].astype(str).str.lower()

            group_list = df["Molecule"].value_counts().index.tolist()
            group_list = list(set(group_list))
            group_list.sort()
            print(len(group_list))
            print(group_list)            
            group_dict = {}


            for group in group_list:
                print(group)
                # 直接在原始 df 上使用条件筛选和赋值，避免 SettingWithCopyWarning 警告
                dft = df[df["Molecule"] == group].copy()  # 创建一个副本以便修改，避免在原始 df 上操作
                dft_i = dft[(dft["Sample Type"] == "Standard") & (dft["Exclude From Calibration"] == "false")]
                min_val = dft_i["Analyte Concentration"].min()
                max_val = dft_i["Analyte Concentration"].max()
                # 添加标准范围列
                # covert to int if the value is int, else keep float with 2 decimal
                min_val_str = int(min_val)  if min_val.is_integer() else round(min_val, 2)
                max_val_str = int(max_val)  if max_val.is_integer() else round(max_val, 2)
                
                dft["Standard Range"] = f"{min_val_str} - {max_val_str}"


                # Split Quantification with ' ' to 2 cols, and the new col is Quantification Unit
                dft[["Quantification", "Unit"]] = dft["Quantification"].str.split(' ', expand=True)
                # check if the Quantification can be converted to float. if not, set to na
                dft["Quantification"] = pd.to_numeric(dft["Quantification"], errors='coerce')
                #print the rows with na in Quantification
                print("Rows with na in Quantification:")
                print(dft[dft["Quantification"].isna()])
                

                # 筛选除了 Standard 之外的样本
                dft = dft[dft["Sample Type"] != "Standard"]

                # 删除不再需要的列
                dft.drop(columns=["Sample Type", "Analyte Concentration", "Exclude From Calibration"], inplace=True)


                # 根据 Quantification 值标记 Standard Status
                min_val = min_val * min_coeff
                max_val = max_val * max_coeff
                
                dft["Standard"] = dft["Quantification"].apply(lambda x: " " if (x >= min_val) & (x <= max_val) else "*")
                dft["Standard Status"] = dft["Quantification"].apply(lambda x: "In" if (x >= min_val) & (x <= max_val) else "Out")
                
                # display(dft.head())
                group_dict[group] = dft  # 将修改后的数据框保存到字典中
                

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
            
            # process group
            if self.checkBox_split_by_group.isChecked():
                res_dict = self.process_group(group_dict)
                if res_dict:
                    save_path_grouped = os.path.join(self.save_path, f"GROUP_SHEETS_{original_name}.xlsx")
                    with pd.ExcelWriter(save_path_grouped) as writer:
                        for sheet_name, dft in res_dict.items():
                            dft.to_excel(writer, sheet_name=sheet_name)
                        

            # messagebox.showinfo("Success", f"File processed and saved to [{save_path}]")
            QtWidgets.QMessageBox.information(self, 'Success', f"File processed and saved to [{self.save_path}]")
        except Exception as e:
            # show exact error location
            import traceback
            QtWidgets.QMessageBox.critical(self, 'Error', f"Error: {e}\n{traceback.format_exc()}")
         
    def on_pushButton_run(self):
        self.filename = self.lineEdit_file_path.text()
        self.save_path = self.lineEdit_save_dir_path.text()
        if self.filename == '':
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Please select a file.')
            return
        if self.save_path == '':
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Please select a folder to save the file.')
            return
        

        try:
            self.process_file()

            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f"Error: {e}")
            return
        
class FileDragDropLineEdit(QLineEdit):
    def __init__(self, parent=None, mode='file', default_filename=''):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.mode = mode  # 'file' 或 'folder'
        self.default_filename = default_filename

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toLocalFile()
            
            if self.mode == 'folder':
                if self.default_filename == '':
                    url = os.path.dirname(url)
                else:
                    # if url is a folder, append default file name
                    if os.path.isdir(url):
                        url = os.path.join(url, self.default_filename)

                    # if url is a file, append default file name to its parent folder
                    elif os.path.isfile(url):
                        url = os.path.join(os.path.dirname(url), self.default_filename)
                    

            self.setText(url)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SCFA_Marker()
    window.show()
    sys.exit(app.exec_())


