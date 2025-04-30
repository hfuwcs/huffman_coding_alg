import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import sys
import io

try:
    import huffman_backend as hf
except ImportError:
    messagebox.showerror("Lỗi", "Không tìm thấy file 'huffman_backend.py'. Hãy đảm bảo nó nằm cùng thư mục.")
    sys.exit(1)

class TextRedirector(io.StringIO):
    """Chuyển hướng print output vào Text widget."""
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def write(self, msg):
        # Đảm bảo cập nhật widget trong luồng chính của Tkinter
        self.widget.after(0, self._write_to_widget, msg)

    def _write_to_widget(self, msg):
        self.widget.configure(state='normal')
        self.widget.insert(tk.END, msg)
        self.widget.see(tk.END) # Cuộn xuống cuối
        self.widget.configure(state='disabled')

    def flush(self):
        pass

class HuffmanApp:
    def __init__(self, master):
        self.master = master
        master.title("Ứng dụng Mã hóa/Giải mã Ảnh Huffman")
        master.geometry("800x700")

        self.original_image_path = tk.StringVar()
        self.encoded_file_path = tk.StringVar()
        self.decoded_image_path = tk.StringVar()

        # --- Khung Input ---
        input_frame = tk.LabelFrame(master, text="1. Chọn ảnh gốc", padx=10, pady=10)
        input_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(input_frame, text="Đường dẫn ảnh:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.input_entry = tk.Entry(input_frame, textvariable=self.original_image_path, width=60, state='readonly')
        self.input_entry.grid(row=0, column=1, padx=5, pady=2)
        self.browse_input_btn = tk.Button(input_frame, text="Chọn file...", command=self.browse_input_image)
        self.browse_input_btn.grid(row=0, column=2, padx=5, pady=2)

        # --- Khung Mã hóa ---
        encode_frame = tk.LabelFrame(master, text="2. Mã hóa (Encode)", padx=10, pady=10)
        encode_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(encode_frame, text="Lưu file mã hóa (.huff):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.encode_output_entry = tk.Entry(encode_frame, textvariable=self.encoded_file_path, width=60, state='readonly')
        self.encode_output_entry.grid(row=0, column=1, padx=5, pady=2)
        self.browse_encode_output_btn = tk.Button(encode_frame, text="Chọn nơi lưu...", command=self.browse_encoded_output)
        self.browse_encode_output_btn.grid(row=0, column=2, padx=5, pady=2)

        self.encode_btn = tk.Button(encode_frame, text="Mã hóa ảnh", command=self.encode_action, state='disabled')
        self.encode_btn.grid(row=1, column=1, pady=10)

        # --- Khung Giải mã ---
        decode_frame = tk.LabelFrame(master, text="3. Giải mã (Decode)", padx=10, pady=10)
        decode_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(decode_frame, text="Chọn file mã hóa (.huff):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        # Entry riêng cho việc chọn file .huff để giải mã
        self.decode_input_entry = tk.Entry(decode_frame, width=60, state='readonly')
        self.decode_input_entry.grid(row=0, column=1, padx=5, pady=2)
        self.browse_decode_input_btn = tk.Button(decode_frame, text="Chọn file...", command=self.browse_decode_input)
        self.browse_decode_input_btn.grid(row=0, column=2, padx=5, pady=2)

        tk.Label(decode_frame, text="Lưu ảnh giải mã:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.decode_output_entry = tk.Entry(decode_frame, textvariable=self.decoded_image_path, width=60, state='readonly')
        self.decode_output_entry.grid(row=1, column=1, padx=5, pady=2)
        self.browse_decode_output_btn = tk.Button(decode_frame, text="Chọn nơi lưu...", command=self.browse_decoded_output)
        self.browse_decode_output_btn.grid(row=1, column=2, padx=5, pady=2)

        self.decode_btn = tk.Button(decode_frame, text="Giải mã ảnh", command=self.decode_action, state='disabled')
        self.decode_btn.grid(row=2, column=1, pady=10)


        # --- Khung So sánh ---
        compare_frame = tk.LabelFrame(master, text="4. So sánh", padx=10, pady=10)
        compare_frame.pack(padx=10, pady=5, fill="x")

        self.compare_btn = tk.Button(compare_frame, text="So sánh ảnh gốc và ảnh giải mã", command=self.compare_action, state='disabled')
        self.compare_btn.pack(pady=5) # Pack đơn giản hơn grid ở đây

        # --- Khung Output/Log ---
        log_frame = tk.LabelFrame(master, text="Thông tin xử lý", padx=10, pady=10)
        log_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10, state='disabled')
        self.log_text.pack(fill="both", expand=True)

        # --- Chuyển hướng stdout ---
        self.stdout_redirector = TextRedirector(self.log_text)
        self.original_stdout = sys.stdout
        sys.stdout = self.stdout_redirector

        # Thiết lập trạng thái ban đầu của các nút
        self.update_button_states()

        # Khôi phục stdout khi đóng cửa sổ
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def log(self, message):
        """Ghi thông điệp vào Text widget (thay thế print trực tiếp nếu cần)."""
        print(message) # Vẫn dùng print vì nó đã được chuyển hướng

    def clear_log(self):
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')

    def browse_input_image(self):
        # Nên ưu tiên các định dạng không nén hoặc lossless
        filetypes = [
            ("Ảnh không nén", "*.bmp *.tiff"),
            ("Ảnh Lossless", "*.png"),
            ("Tất cả ảnh", "*.bmp *.png *.tiff *.jpg *.jpeg *.gif"),
            ("Tất cả file", "*.*")
        ]
        filepath = filedialog.askopenfilename(title="Chọn ảnh gốc", filetypes=filetypes)
        if filepath:
            self.original_image_path.set(filepath)
            # Tự động đề xuất tên file output
            base, _ = os.path.splitext(filepath)
            self.encoded_file_path.set(base + ".huff")
            self.decoded_image_path.set(base + "_decoded.png") # Mặc định PNG lossless
            self.log(f"Đã chọn ảnh gốc: {filepath}")
            self.update_button_states() # Cập nhật trạng thái nút Encode

    def browse_encoded_output(self):
        # Lấy đường dẫn đề xuất làm mặc định
        initial_dir = os.path.dirname(self.encoded_file_path.get())
        initial_file = os.path.basename(self.encoded_file_path.get())
        filepath = filedialog.asksaveasfilename(
            title="Lưu file đã mã hóa",
            initialdir=initial_dir or os.getcwd(),
            initialfile=initial_file or "encoded_image.huff",
            defaultextension=".huff",
            filetypes=[("Huffman Encoded File", "*.huff"), ("Tất cả file", "*.*")]
        )
        if filepath:
            self.encoded_file_path.set(filepath)
            self.log(f"Sẽ lưu file mã hóa tại: {filepath}")
            self.update_button_states()

    def browse_decode_input(self):
        filepath = filedialog.askopenfilename(
            title="Chọn file mã hóa (.huff) để giải mã",
            filetypes=[("Huffman Encoded File", "*.huff"), ("Tất cả file", "*.*")]
        )
        if filepath:
            # Cập nhật Entry của phần Decode
            self.decode_input_entry.configure(state='normal')
            self.decode_input_entry.delete(0, tk.END)
            self.decode_input_entry.insert(0, filepath)
            self.decode_input_entry.configure(state='readonly')

            # Đề xuất tên file giải mã dựa trên file .huff
            base, _ = os.path.splitext(filepath)
            self.decoded_image_path.set(base + "_decoded.png") # Mặc định PNG

            self.log(f"Đã chọn file mã hóa để giải mã: {filepath}")
            self.update_button_states()

    def browse_decoded_output(self):
        initial_dir = os.path.dirname(self.decoded_image_path.get())
        initial_file = os.path.basename(self.decoded_image_path.get())
        filepath = filedialog.asksaveasfilename(
            title="Lưu ảnh đã giải mã",
            initialdir=initial_dir or os.getcwd(),
            initialfile=initial_file or "decoded_image.png",
            defaultextension=".png", # Ưu tiên PNG
            filetypes=[
                ("PNG Image", "*.png"),
                ("Bitmap Image", "*.bmp"),
                ("JPEG Image", "*.jpg *.jpeg"),
                ("TIFF Image", "*.tiff"),
                ("Tất cả file", "*.*")]
        )
        if filepath:
            self.decoded_image_path.set(filepath)
            self.log(f"Sẽ lưu ảnh giải mã tại: {filepath}")
            self.update_button_states()

    def update_button_states(self):
        """Cập nhật trạng thái enable/disable của các nút."""
        can_encode = bool(self.original_image_path.get() and self.encoded_file_path.get())
        self.encode_btn.config(state=tk.NORMAL if can_encode else tk.DISABLED)

        can_decode = bool(self.decode_input_entry.get() and self.decoded_image_path.get())
        self.decode_btn.config(state=tk.NORMAL if can_decode else tk.DISABLED)

        # Chỉ cho phép so sánh nếu có ảnh gốc VÀ ảnh đã giải mã (đường dẫn tồn tại)
        # Giả sử self.last_decoded_path lưu đường dẫn thực tế sau khi giải mã thành công
        original_exists = bool(self.original_image_path.get())
        try:
             decoded_exists = hasattr(self, 'last_decoded_path') and bool(self.last_decoded_path) and os.path.exists(self.last_decoded_path)
        except: # Bắt lỗi nếu self.last_decoded_path chưa được tạo
             decoded_exists = False

        # Hoặc cách đơn giản hơn: chỉ cần đường dẫn được đặt, hàm compare sẽ kiểm tra file tồn tại
        # decoded_path_set = bool(self.decoded_image_path.get())
        # can_compare = original_exists and decoded_path_set

        # Cách chặt chẽ hơn: kiểm tra cả file tồn tại
        try:
             original_file_exists = os.path.exists(self.original_image_path.get())
        except: original_file_exists = False
        try:
             # Dùng đường dẫn thực tế sau khi decode thành công
             decoded_file_path_to_check = getattr(self, 'last_decoded_path', self.decoded_image_path.get())
             decoded_file_exists = os.path.exists(decoded_file_path_to_check) and decoded_file_path_to_check
        except: decoded_file_exists = False


        can_compare = original_file_exists and decoded_file_exists
        self.compare_btn.config(state=tk.NORMAL if can_compare else tk.DISABLED)


    def encode_action(self):
        self.clear_log()
        in_path = self.original_image_path.get()
        out_path = self.encoded_file_path.get()

        if not in_path or not out_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn ảnh gốc và nơi lưu file mã hóa.")
            return

        try:
            # Vô hiệu hóa các nút trong khi xử lý
            self.disable_buttons()
            self.master.update_idletasks() # Cập nhật giao diện

            # Gọi hàm backend
            success = hf.encode_image(in_path, out_path)

            if success:
                self.log("\nMã hóa thành công!")
                # Tự động điền file vừa mã hóa vào ô input của giải mã
                self.decode_input_entry.configure(state='normal')
                self.decode_input_entry.delete(0, tk.END)
                self.decode_input_entry.insert(0, out_path)
                self.decode_input_entry.configure(state='readonly')
            else:
                 self.log("\nMã hóa thất bại. Xem chi tiết lỗi ở trên.")
                 messagebox.showerror("Mã hóa thất bại", "Quá trình mã hóa gặp lỗi. Vui lòng xem log.")

        except Exception as e:
            self.log(f"\nLỗi không mong muốn trong quá trình mã hóa: {e}")
            messagebox.showerror("Lỗi nghiêm trọng", f"Đã xảy ra lỗi không xác định: {e}")
        finally:
            # Kích hoạt lại các nút
            self.enable_buttons()
            self.update_button_states() # Cập nhật lại trạng thái dựa trên kết quả

    def decode_action(self):
        self.clear_log()
        in_path = self.decode_input_entry.get() # Lấy từ entry của phần decode
        out_path = self.decoded_image_path.get()

        if not in_path or not out_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn file mã hóa (.huff) và nơi lưu ảnh giải mã.")
            return

        try:
            self.disable_buttons()
            self.master.update_idletasks()

            # Gọi hàm backend, hàm này trả về đường dẫn thực tế đã lưu hoặc False
            actual_output_path = hf.decode_image(in_path, out_path)

            if actual_output_path: # Nếu trả về đường dẫn (thành công)
                self.log("\nGiải mã thành công!")
                # Cập nhật lại đường dẫn output nếu backend trả về khác (ví dụ, đổi thành .png)
                self.decoded_image_path.set(actual_output_path)
                # Lưu đường dẫn thực tế để so sánh
                self.last_decoded_path = actual_output_path
            else:
                self.log("\nGiải mã thất bại. Xem chi tiết lỗi ở trên.")
                messagebox.showerror("Giải mã thất bại", "Quá trình giải mã gặp lỗi. Vui lòng xem log.")
                self.last_decoded_path = None # Xóa đường dẫn nếu thất bại

        except Exception as e:
            self.log(f"\nLỗi không mong muốn trong quá trình giải mã: {e}")
            messagebox.showerror("Lỗi nghiêm trọng", f"Đã xảy ra lỗi không xác định: {e}")
            self.last_decoded_path = None
        finally:
            self.enable_buttons()
            self.update_button_states()

    def compare_action(self):
        self.clear_log()
        original_path = self.original_image_path.get()
        # Lấy đường dẫn ảnh đã giải mã thực tế (nếu có)
        decoded_path = getattr(self, 'last_decoded_path', self.decoded_image_path.get())


        if not original_path or not decoded_path:
             messagebox.showerror("Lỗi", "Thiếu đường dẫn ảnh gốc hoặc ảnh giải mã để so sánh.")
             return
        if not os.path.exists(original_path):
             messagebox.showerror("Lỗi", f"Không tìm thấy ảnh gốc: {original_path}")
             return
        if not os.path.exists(decoded_path):
             messagebox.showerror("Lỗi", f"Không tìm thấy ảnh đã giải mã: {decoded_path}. Hãy giải mã trước.")
             return


        try:
            self.disable_buttons()
            self.master.update_idletasks()

            # Gọi hàm backend
            result = hf.compare_images(original_path, decoded_path)

            # Hàm compare_images đã print kết quả, có thể thêm thông báo tóm tắt
            if result is True:
                 self.log("\nKết luận: Ảnh gốc và ảnh giải mã GIỐNG HỆT NHAU.")
                 messagebox.showinfo("Kết quả so sánh", "Ảnh gốc và ảnh giải mã giống hệt nhau.")
            elif result is False:
                 self.log("\nKết luận: Ảnh gốc và ảnh giải mã CÓ KHÁC BIỆT.")
                 messagebox.showwarning("Kết quả so sánh", "Ảnh gốc và ảnh giải mã có khác biệt. Xem log để biết chi tiết.")
            else: # result is None (lỗi)
                 self.log("\nSo sánh gặp lỗi.")
                 messagebox.showerror("Lỗi so sánh", "Quá trình so sánh gặp lỗi. Vui lòng xem log.")

        except Exception as e:
            self.log(f"\nLỗi không mong muốn trong quá trình so sánh: {e}")
            messagebox.showerror("Lỗi nghiêm trọng", f"Đã xảy ra lỗi không xác định: {e}")
        finally:
            self.enable_buttons()
            self.update_button_states()

    def disable_buttons(self):
        """Vô hiệu hóa các nút hành động chính."""
        self.browse_input_btn.config(state=tk.DISABLED)
        self.browse_encode_output_btn.config(state=tk.DISABLED)
        self.encode_btn.config(state=tk.DISABLED)
        self.browse_decode_input_btn.config(state=tk.DISABLED)
        self.browse_decode_output_btn.config(state=tk.DISABLED)
        self.decode_btn.config(state=tk.DISABLED)
        self.compare_btn.config(state=tk.DISABLED)

    def enable_buttons(self):
        """Kích hoạt lại các nút duyệt file (các nút hành động sẽ được cập nhật bởi update_button_states)."""
        self.browse_input_btn.config(state=tk.NORMAL)
        self.browse_encode_output_btn.config(state=tk.NORMAL)
        self.browse_decode_input_btn.config(state=tk.NORMAL)
        self.browse_decode_output_btn.config(state=tk.NORMAL)
        # Không kích hoạt encode/decode/compare ở đây, để update_button_states quyết định


    def on_closing(self):
        """Khôi phục stdout và đóng ứng dụng."""
        sys.stdout = self.original_stdout # Quan trọng: Khôi phục stdout
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = HuffmanApp(root)
    root.mainloop()