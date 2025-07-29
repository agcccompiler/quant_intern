# gui.py
"""
因子回测框架图形用户界面

现代化的GUI界面，支持可视化配置和执行回测
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import threading
from datetime import datetime
from typing import Dict, Any, Optional
import logging

try:
    from .config.config import FrameworkConfig, get_config
    from .main import FactorBacktestPipeline
except ImportError:
    from factor_backtest_framework.config.config import FrameworkConfig, get_config
    from factor_backtest_framework.main import FactorBacktestPipeline

class FactorBacktestGUI:
    """因子回测框架GUI界面"""
    
    def __init__(self):
        """初始化GUI"""
        self.root = tk.Tk()
        self.root.title("因子回测框架 v2.0")
        self.root.geometry("900x700")
        
        # 配置和状态
        self.config = get_config()
        self.pipeline = None
        self.is_running = False
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 初始化日志重定向
        self.setup_logging()
    
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置颜色
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
    
    def create_widgets(self):
        """创建主界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置grid权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="因子回测框架", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 左侧配置面板
        self.create_config_panel(main_frame)
        
        # 右侧控制和日志面板
        self.create_control_panel(main_frame)
    
    def create_config_panel(self, parent):
        """创建配置面板"""
        config_frame = ttk.LabelFrame(parent, text="配置设置", padding="10")
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        row = 0
        
        # DolphinDB配置
        ttk.Label(config_frame, text="DolphinDB配置", style='Title.TLabel').grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # 服务器地址
        ttk.Label(config_frame, text="服务器:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.host_var = tk.StringVar(value=self.config.dolphindb.host)
        ttk.Entry(config_frame, textvariable=self.host_var, width=20).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        row += 1
        
        # 端口
        ttk.Label(config_frame, text="端口:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.port_var = tk.StringVar(value=str(self.config.dolphindb.port))
        ttk.Entry(config_frame, textvariable=self.port_var, width=20).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        row += 1
        
        # 分隔线
        ttk.Separator(config_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # 因子配置
        ttk.Label(config_frame, text="因子配置", style='Title.TLabel').grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # 脚本路径
        ttk.Label(config_frame, text="脚本路径:").grid(row=row, column=0, sticky=tk.W, pady=2)
        script_frame = ttk.Frame(config_frame)
        script_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        script_frame.columnconfigure(0, weight=1)
        
        self.script_var = tk.StringVar(value=self.config.factor.script_path)
        ttk.Entry(script_frame, textvariable=self.script_var).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(script_frame, text="浏览...", command=self.browse_script, width=8).grid(row=0, column=1, padx=(5, 0))
        row += 1
        
        # 日期配置
        date_frame = ttk.Frame(config_frame)
        date_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(date_frame, text="开始日期:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.start_date_var = tk.StringVar(value=self.config.factor.start_date)
        ttk.Entry(date_frame, textvariable=self.start_date_var, width=12).grid(row=0, column=1, padx=5)
        
        ttk.Label(date_frame, text="结束日期:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.end_date_var = tk.StringVar(value=self.config.factor.end_date)
        ttk.Entry(date_frame, textvariable=self.end_date_var, width=12).grid(row=0, column=3, padx=5)
        row += 1
        
        # 其他参数
        params_frame = ttk.Frame(config_frame)
        params_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(params_frame, text="时间桶(秒):").grid(row=0, column=0, sticky=tk.W)
        self.seconds_var = tk.StringVar(value=str(self.config.factor.seconds))
        ttk.Entry(params_frame, textvariable=self.seconds_var, width=8).grid(row=0, column=1, padx=5)
        
        ttk.Label(params_frame, text="信号占比:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.portion_var = tk.StringVar(value=str(self.config.factor.portion))
        ttk.Entry(params_frame, textvariable=self.portion_var, width=8).grid(row=0, column=3, padx=5)
        row += 1
        
        # 分隔线
        ttk.Separator(config_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # 收益率文件
        ttk.Label(config_frame, text="收益率文件", style='Title.TLabel').grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row += 1
        
        return_frame = ttk.Frame(config_frame)
        return_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        return_frame.columnconfigure(0, weight=1)
        
        self.return_file_var = tk.StringVar()
        ttk.Entry(return_frame, textvariable=self.return_file_var).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(return_frame, text="浏览...", command=self.browse_return_file, width=8).grid(row=0, column=1, padx=(5, 0))
        row += 1
        
        # 平滑配置
        ttk.Label(config_frame, text="平滑设置", style='Title.TLabel').grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.smooth_enable_var = tk.BooleanVar(value=self.config.smoothing.enable)
        ttk.Checkbutton(config_frame, text="启用因子平滑", variable=self.smooth_enable_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1
        
        ttk.Label(config_frame, text="滚动窗口:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.window_var = tk.StringVar(value=str(self.config.smoothing.rolling_window))
        ttk.Entry(config_frame, textvariable=self.window_var, width=8).grid(row=row, column=1, sticky=tk.W, pady=2)
        
        # 配置grid权重
        config_frame.columnconfigure(1, weight=1)
    
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        control_frame.columnconfigure(0, weight=1)
        control_frame.rowconfigure(1, weight=1)
        
        # 控制按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.run_button = ttk.Button(button_frame, text="开始回测", command=self.start_backtest)
        self.run_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.batch_button = ttk.Button(button_frame, text="批量回测", command=self.start_batch_backtest)
        self.batch_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_backtest, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=(0, 5))
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(button_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.RIGHT)
        
        # 进度条
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 日志显示
        log_frame = ttk.LabelFrame(control_frame, text="执行日志", padding="5")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=50, height=20, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 结果显示
        result_frame = ttk.LabelFrame(control_frame, text="回测结果", padding="5")
        result_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        result_frame.columnconfigure(0, weight=1)
        
        self.result_text = tk.Text(result_frame, height=8, wrap=tk.WORD)
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        result_scroll = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        result_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.result_text.configure(yscrollcommand=result_scroll.set)
    
    def setup_logging(self):
        """设置日志重定向"""
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            
            def emit(self, record):
                try:
                    msg = self.format(record)
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                    self.text_widget.update()
                except Exception:
                    pass
        
        # 创建日志处理器
        handler = TextHandler(self.log_text)
        handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        
        # 获取根日志记录器并添加处理器
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    def browse_script(self):
        """浏览脚本文件"""
        try:
            # 使用简化的文件对话框，避免macOS兼容性问题
            filename = filedialog.askopenfilename(title="选择DolphinDB脚本文件")
            if filename:
                self.script_var.set(filename)
        except Exception as e:
            messagebox.showerror("错误", f"文件选择失败: {str(e)}\n请手动输入文件路径")
    
    def browse_return_file(self):
        """浏览收益率文件"""
        try:
            # 使用简化的文件对话框，避免macOS兼容性问题
            filename = filedialog.askopenfilename(title="选择收益率数据文件")
            if filename:
                self.return_file_var.set(filename)
        except Exception as e:
            messagebox.showerror("错误", f"文件选择失败: {str(e)}\n请手动输入文件路径")
    
    def validate_config(self) -> bool:
        """验证配置"""
        try:
            # 验证必填字段
            if not self.script_var.get().strip():
                raise ValueError("请选择DolphinDB脚本文件")
            
            if not self.return_file_var.get().strip():
                raise ValueError("请选择收益率数据文件")
            
            # 验证文件存在
            if not os.path.exists(self.script_var.get()):
                raise ValueError("DolphinDB脚本文件不存在")
            
            if not os.path.exists(self.return_file_var.get()):
                raise ValueError("收益率数据文件不存在")
            
            # 验证数值参数
            int(self.port_var.get())
            int(self.seconds_var.get())
            float(self.portion_var.get())
            int(self.window_var.get())
            
            return True
            
        except ValueError as e:
            messagebox.showerror("配置错误", str(e))
            return False
    
    def get_current_config(self) -> FrameworkConfig:
        """获取当前配置"""
        config = get_config()
        
        # 更新DolphinDB配置
        config.dolphindb.host = self.host_var.get()
        config.dolphindb.port = int(self.port_var.get())
        
        # 更新因子配置
        config.factor.script_path = self.script_var.get()
        config.factor.start_date = self.start_date_var.get()
        config.factor.end_date = self.end_date_var.get()
        config.factor.seconds = int(self.seconds_var.get())
        config.factor.portion = float(self.portion_var.get())
        
        # 更新平滑配置
        config.smoothing.enable = self.smooth_enable_var.get()
        config.smoothing.rolling_window = int(self.window_var.get())
        
        return config
    
    def start_backtest(self):
        """开始回测"""
        if not self.validate_config():
            return
        
        if self.is_running:
            messagebox.showwarning("警告", "回测正在进行中")
            return
        
        # 更新界面状态
        self.is_running = True
        self.run_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress.start(10)
        self.status_var.set("正在执行回测...")
        
        # 清空结果显示
        self.result_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, f"\n{'='*50}\n开始新的回测任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}\n")
        
        # 在新线程中运行回测
        thread = threading.Thread(target=self.run_backtest_thread)
        thread.daemon = True
        thread.start()
    
    def run_backtest_thread(self):
        """回测线程"""
        try:
            # 获取配置
            config = self.get_current_config()
            
            # 创建流水线
            self.pipeline = FactorBacktestPipeline(config)
            
            # 运行回测
            results = self.pipeline.run_full_pipeline(
                return_file_path=self.return_file_var.get(),
                save_results=True
            )
            
            # 显示结果
            self.root.after(0, self.show_results, results)
            
        except Exception as e:
            self.root.after(0, self.show_error, str(e))
        finally:
            self.root.after(0, self.backtest_finished)
    
    def start_batch_backtest(self):
        """开始批量回测"""
        if not self.validate_config():
            return
        
        if self.is_running:
            messagebox.showwarning("警告", "回测正在进行中")
            return
        
        # 确认批量回测
        if not messagebox.askyesno("确认", "批量回测将测试多种参数组合，可能需要较长时间。\n是否继续？"):
            return
        
        # 更新界面状态
        self.is_running = True
        self.run_button.config(state=tk.DISABLED)
        self.batch_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress.start(10)
        self.status_var.set("正在执行批量回测...")
        
        # 清空结果显示
        self.result_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, f"\n{'='*50}\n开始批量回测任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}\n")
        
        # 在新线程中运行批量回测
        thread = threading.Thread(target=self.run_batch_backtest_thread)
        thread.daemon = True
        thread.start()
    
    def run_batch_backtest_thread(self):
        """批量回测线程"""
        try:
            # 获取配置
            config = self.get_current_config()
            
            # 创建流水线
            self.pipeline = FactorBacktestPipeline(config)
            
            # 运行批量回测
            results = self.pipeline.batch_backtest(
                return_file_path=self.return_file_var.get(),
                save_results=True
            )
            
            # 显示结果
            self.root.after(0, self.show_batch_results, results)
            
        except Exception as e:
            self.root.after(0, self.show_error, str(e))
        finally:
            self.root.after(0, self.batch_backtest_finished)
    
    def show_batch_results(self, results: Dict[str, Any]):
        """显示批量回测结果"""
        try:
            result_text = "批量回测完成！结果对比:\n"
            result_text += "="*60 + "\n"
            
            # 显示对比表格
            comparison_table = results['comparison_table']
            for _, row in comparison_table.iterrows():
                result_text += f"[{row['组合名称']}]\n"
                result_text += f"  ICIR: {row['ICIR']} | RankIC: {row['平均RankIC']}\n"
                result_text += f"  多空收益: {row['多空年化收益']} | 超额收益: {row['超额年化收益']}\n\n"
            
            # 显示最佳组合
            valid_results = [r for r in results['results'] if 'error' not in r]
            if valid_results:
                best_icir = max(valid_results, key=lambda x: x['metrics']['ICIR'])
                best_excess = max(valid_results, key=lambda x: x['metrics']['excess_return'])
                
                result_text += f"🏆 最佳ICIR组合: {best_icir['combination_name']} (ICIR: {best_icir['metrics']['ICIR']:.4f})\n"
                result_text += f"🎯 最佳超额收益组合: {best_excess['combination_name']} (超额收益: {best_excess['metrics']['excess_return']:.4f})\n\n"
            
            if 'saved_files' in results:
                result_text += f"保存的文件:\n"
                for file_type, file_path in results['saved_files'].items():
                    result_text += f"  {file_type}: {file_path}\n"
            
            self.result_text.insert(tk.END, result_text)
            
            messagebox.showinfo("成功", "批量回测完成！请查看结果对比。")
            
        except Exception as e:
            self.show_error(f"显示批量结果时出错: {str(e)}")
    
    def batch_backtest_finished(self):
        """批量回测完成后的清理"""
        self.is_running = False
        self.run_button.config(state=tk.NORMAL)
        self.batch_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress.stop()
        self.status_var.set("批量回测完成")
    
    def show_results(self, results: Dict[str, Any]):
        """显示回测结果"""
        try:
            eval_results = results['evaluation_results']
            
            result_text = f"""回测完成！主要结果:
{'='*40}
ICIR: {eval_results['ICIR']:.4f}
平均Rank IC: {eval_results['average_rank_IC']:.4f}
多空年化收益: {eval_results['long_short_return']:.4f}
超额年化收益: {eval_results['excess_return']:.4f}
多空换手率: {eval_results['long_short_turnover']:.4f}
多头换手率: {eval_results['long_turnover']:.4f}

分组年化收益率:
"""
            
            for i, ret in enumerate(eval_results['group_returns'], 1):
                result_text += f"组 {i}: {ret:.4f}\n"
            
            if 'saved_files' in eval_results:
                result_text += f"\n保存的文件:\n"
                for file_type, file_path in eval_results['saved_files'].items():
                    result_text += f"  {file_type}: {file_path}\n"
            
            self.result_text.insert(tk.END, result_text)
            
            messagebox.showinfo("成功", "回测完成！请查看结果。")
            
        except Exception as e:
            self.show_error(f"显示结果时出错: {str(e)}")
    
    def show_error(self, error_msg: str):
        """显示错误"""
        self.log_text.insert(tk.END, f"\n[错误] {error_msg}\n")
        self.log_text.see(tk.END)
        messagebox.showerror("错误", f"回测失败:\n{error_msg}")
    
    def backtest_finished(self):
        """回测完成后的清理"""
        self.is_running = False
        self.run_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress.stop()
        self.status_var.set("就绪")
    
    def stop_backtest(self):
        """停止回测"""
        if messagebox.askyesno("确认", "确定要停止当前回测吗？"):
            self.is_running = False
            self.status_var.set("正在停止...")
            # 注意：实际停止需要更复杂的逻辑
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def save_config(self):
        """保存配置"""
        try:
            config = self.get_current_config()
            filename = filedialog.asksaveasfilename(
                title="保存配置文件",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            if filename:
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
                messagebox.showinfo("成功", f"配置已保存到: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def run(self):
        """运行GUI"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()

def main():
    """启动GUI"""
    app = FactorBacktestGUI()
    app.run()

if __name__ == "__main__":
    main()
