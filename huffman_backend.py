import heapq
import os
import pickle
from collections import Counter
from PIL import Image, ImageOps
import numpy as np
import sys


class HuffmanNode:

    def __init__(self, symbol, freq):
        self.symbol = symbol
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

    def __eq__(self, other):
        if other is None or not isinstance(other, HuffmanNode):
            return False
        return self.freq == other.freq

def build_frequency_table(data):
    return Counter(data)

def build_huffman_tree(freq_table):
    priority_queue = [HuffmanNode(symbol, freq) for symbol, freq in freq_table.items()]
    heapq.heapify(priority_queue)

    if not priority_queue:
        return None

    if len(priority_queue) == 1:
        node = heapq.heappop(priority_queue)
        merged = HuffmanNode(None, node.freq)
        merged.left = node
        heapq.heappush(priority_queue, merged)

    while len(priority_queue) > 1:
        left = heapq.heappop(priority_queue)
        right = heapq.heappop(priority_queue)

        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left = left
        merged.right = right

        heapq.heappush(priority_queue, merged)
    
    return priority_queue[0] if priority_queue else None


def generate_huffman_codes(node, prefix="", codebook=None):
    if codebook is None:
        codebook = {}

    if node is None:
        return codebook

    if node.symbol is not None: # Nút lá
        codebook[node.symbol] = prefix if prefix else "0"
    else: # Nút nội bộ
        if node.left:
            generate_huffman_codes(node.left, prefix + "0", codebook)
        if node.right:
            generate_huffman_codes(node.right, prefix + "1", codebook)
    return codebook


def encode_data(data, codebook):
    if not codebook:
        if not data:
             return ""
        print("Lỗi mã hóa: Codebook trống nhưng có dữ liệu.", file=sys.stderr)
        return None
    
    encoded_bits = "".join(codebook.get(str(symbol) if not isinstance(symbol, str) else symbol, "") for symbol in data)
    encoded_bits = "".join(codebook.get(symbol, "") for symbol in data)
    return encoded_bits

def decode_data(encoded_bits, huffman_tree):
    if huffman_tree is None:
        if not encoded_bits:
            return []
        print("Lỗi giải mã: Cây Huffman là None.", file=sys.stderr)
        return None

    decoded_symbols = []
    current_node = huffman_tree


    if current_node.symbol is not None:
        if encoded_bits and all(bit == encoded_bits[0] for bit in encoded_bits):
            pass

    for bit in encoded_bits:
        if current_node is None :
            print("Lỗi giải mã: Đạt đến nút None khi đang duyệt cây.", file=sys.stderr)
            return None

        if bit == '0':
            current_node = current_node.left
        elif bit == '1':
            current_node = current_node.right
        else:
            print(f"Lỗi giải mã: Ký tự không hợp lệ '{bit}' trong chuỗi bit.", file=sys.stderr)
            return None

        if current_node is None:
             print(f"Lỗi giải mã: Chuỗi bit dẫn đến đường không tồn tại trong cây (bit='{bit}').", file=sys.stderr)
             return None

        if current_node.symbol is not None:
            decoded_symbols.append(current_node.symbol)
            current_node = huffman_tree
    
    is_single_symbol_tree = (huffman_tree.left is not None and huffman_tree.left.symbol is not None and huffman_tree.right is None) or \
                            (huffman_tree.right is not None and huffman_tree.right.symbol is not None and huffman_tree.left is None)

    if current_node != huffman_tree and not (current_node.symbol is not None and is_single_symbol_tree):
        if current_node.symbol is None:
            print("Cảnh báo giải mã: Chuỗi bit kết thúc giữa chừng của một ký tự.", file=sys.stderr)

    return decoded_symbols


def flatten_image_data(image):
    img_array = np.array(image)
    if img_array.dtype == bool:
        img_array = img_array.astype(np.uint8)
    return img_array.flatten(), img_array.dtype.str

def pad_encoded_text(encoded_text):
    extra_padding = 8 - len(encoded_text) % 8
    if extra_padding == 8:
        extra_padding = 0
    padded_encoded_text = encoded_text + '0' * extra_padding
    padding_info = "{0:08b}".format(extra_padding)
    return padded_encoded_text, padding_info

def remove_padding(padded_encoded_text_with_info):
    if len(padded_encoded_text_with_info) < 8:
        print("Lỗi khi loại bỏ padding: Dữ liệu quá ngắn để chứa thông tin padding.", file=sys.stderr)
        return ""
    
    padding_info_bits = padded_encoded_text_with_info[:8]
    try:
        extra_padding = int(padding_info_bits, 2)
    except ValueError:
        print("Lỗi khi loại bỏ padding: Thông tin padding không hợp lệ.", file=sys.stderr)
        return "" 

    padded_encoded_text = padded_encoded_text_with_info[8:]
    
    if extra_padding > len(padded_encoded_text) or extra_padding < 0: 
         print(f"Lỗi khi loại bỏ padding: Số lượng padding không hợp lệ ({extra_padding}) cho độ dài {len(padded_encoded_text)}.", file=sys.stderr)
         return ""

    if extra_padding == 0:
        return padded_encoded_text
    else:
        return padded_encoded_text[:-extra_padding]

def get_byte_array(padded_encoded_text):
    if len(padded_encoded_text) % 8 != 0:
        print("Lỗi trong get_byte_array: Input không được padding đúng (chiều dài không chia hết cho 8).", file=sys.stderr)
        raise ValueError("Chuỗi bit cần được padding để chia hết cho 8.")
    
    b = bytearray()
    for i in range(0, len(padded_encoded_text), 8):
        byte = padded_encoded_text[i:i+8]
        try:
            b.append(int(byte, 2))
        except ValueError:
            print(f"Lỗi trong get_byte_array: Chuỗi byte không hợp lệ '{byte}'.", file=sys.stderr)
            raise
    return bytes(b)

def bits_to_string(byte_data):
    return "".join(f"{byte:08b}" for byte in byte_data)


def encode_image(image_path, output_path):
    print(f"--- Bắt đầu mã hóa ---")
    try:
        image = Image.open(image_path)
        print(f"Đang mã hóa ảnh: {image_path} ({image.mode}, {image.size})")
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file ảnh '{image_path}'", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Lỗi khi mở ảnh: {e}", file=sys.stderr)
        return False
    
    original_size_bytes = 0
    try:
        original_size_bytes = os.path.getsize(image_path)
        print(f"Kích thước gốc: {original_size_bytes} bytes")
    except OSError as e:
        print(f"Lỗi khi lấy kích thước file gốc: {e}", file=sys.stderr)

    try:
        img_data_flat, img_dtype_str = flatten_image_data(image)
        original_shape = np.array(image).shape 
        image_mode = image.mode
    
        palette_data = None
        if image_mode == 'P':
            palette_data = image.getpalette()

    except Exception as e:
        print(f"Lỗi khi xử lý dữ liệu ảnh: {e}", file=sys.stderr)
        return False

    if len(img_data_flat) == 0 and original_size_bytes > 0 :
         print("Cảnh báo: Dữ liệu ảnh trống sau khi làm phẳng, dù file có kích thước.", file=sys.stderr)
    if len(img_data_flat) == 0:
        print("Ảnh không chứa dữ liệu pixel để mã hóa (có thể là ảnh 0 pixel).")
        freq_table = {}
        huffman_tree = None
        encoded_bits = ""
    else:
        freq_table = build_frequency_table(img_data_flat)
        if not freq_table:
            print("Lỗi: Không thể tạo bảng tần suất (dữ liệu có thể trống hoặc lỗi).", file=sys.stderr)
            return False

        huffman_tree = build_huffman_tree(freq_table)
        if huffman_tree is None:
             print("Lỗi: Không thể xây dựng cây Huffman (bảng tần suất trống).", file=sys.stderr)
             return False

        codebook = generate_huffman_codes(huffman_tree)
        if not codebook and len(freq_table) > 0: 
            print("Lỗi: Không thể tạo bảng mã Huffman.", file=sys.stderr)
            return False
        
        encoded_bits = encode_data(img_data_flat, codebook)
        if encoded_bits is None:
            print("Lỗi trong quá trình mã hóa dữ liệu.", file=sys.stderr)
            return False

    padded_encoded_bits, padding_info = pad_encoded_text(encoded_bits)
    full_bit_string = padding_info + padded_encoded_bits

    try:
        output_byte_array = get_byte_array(full_bit_string)
    except ValueError as e:
        print(f"Lỗi khi chuyển đổi sang byte array: {e}", file=sys.stderr)
        return False

    metadata = {
        'tree': huffman_tree,
        'shape': original_shape,
        'mode': image_mode,
        'dtype_str': img_dtype_str,
        'palette': palette_data
    }

    try:
        with open(output_path, 'wb') as f_out:
            pickle.dump(metadata, f_out, protocol=pickle.HIGHEST_PROTOCOL)
            f_out.write(output_byte_array)
        print(f"Đã lưu file mã hóa: {output_path}")
    except Exception as e:
        print(f"Lỗi khi lưu file mã hóa: {e}", file=sys.stderr)
        if os.path.exists(output_path):
            try: os.remove(output_path)
            except OSError: pass
        return False

    try:
        compressed_size_bytes = os.path.getsize(output_path)
        if original_size_bytes > 0:
             compression_ratio = compressed_size_bytes / original_size_bytes
             print(f"Kích thước sau khi nén: {compressed_size_bytes} bytes")
             print(f"Tỉ suất nén (compressed/original): {compression_ratio:.4f}")
             print(f"Tỉ lệ tiết kiệm: {(1 - compression_ratio) * 100:.2f}%")
        else: # Ảnh gốc 0 byte
             print(f"Kích thước sau khi nén: {compressed_size_bytes} bytes")
             if compressed_size_bytes > 0:
                 print("Ảnh gốc 0 byte, ảnh nén có kích thước (do metadata).")
             else:
                 print("Ảnh gốc và ảnh nén đều 0 byte (hoặc lỗi lấy kích thước).")

    except OSError as e:
        print(f"Lỗi khi lấy kích thước file nén: {e}", file=sys.stderr)

    print(f"--- Mã hóa hoàn tất ---")
    return True


def decode_image(encoded_path, output_path):
    print(f"--- Bắt đầu giải mã ---")
    try:
        with open(encoded_path, 'rb') as f_in:
            metadata = pickle.load(f_in)
            encoded_byte_data = f_in.read()
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file mã hóa '{encoded_path}'", file=sys.stderr)
        return False
    except (pickle.UnpicklingError, EOFError, ImportError, IndexError) as e: 
        print(f"Lỗi: File mã hóa '{encoded_path}' bị hỏng hoặc không đúng định dạng. ({e})", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Lỗi khi đọc file mã hóa: {e}", file=sys.stderr)
        return False

    try:
        huffman_tree = metadata['tree']
        original_shape = metadata['shape']
        image_mode = metadata['mode']
        img_dtype_str = metadata.get('dtype_str', np.dtype(np.uint8).str)
        palette_data = metadata.get('palette', None)

        if not isinstance(original_shape, tuple) or not all(isinstance(dim, int) for dim in original_shape):
             print("Lỗi: Metadata chứa shape không hợp lệ.", file=sys.stderr)
             return False
        if not isinstance(image_mode, str):
             print("Lỗi: Metadata chứa image mode không hợp lệ.", file=sys.stderr)
             return False
    except KeyError as e:
        print(f"Lỗi: Metadata thiếu key bắt buộc: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Lỗi khi truy cập metadata: {e}", file=sys.stderr)
        return False

    padded_encoded_bits_from_file = bits_to_string(encoded_byte_data)
    encoded_bits = remove_padding(padded_encoded_bits_from_file)

    if encoded_bits == "" and len(padded_encoded_bits_from_file) >= 8 and np.prod(original_shape) > 0 :
         print("Lỗi khi loại bỏ padding từ dữ liệu file.", file=sys.stderr)
         return False


    expected_elements = np.prod(original_shape) if original_shape else 0
    decoded_data_list = []

    if expected_elements == 0:
        print("Ảnh giải mã không có pixel (dựa trên shape).")
    elif huffman_tree is None:
        print("Lỗi: Cây Huffman là None nhưng kích thước ảnh mong đợi khác 0.", file=sys.stderr)
        return False
    elif not encoded_bits and expected_elements > 0:

        print(f"Lỗi: Dữ liệu bit mã hóa trống nhưng ảnh gốc có {expected_elements} pixel.", file=sys.stderr)
        return False
    else:
        decoded_data_list = decode_data(encoded_bits, huffman_tree)
        if decoded_data_list is None:
            print("Lỗi trong quá trình giải mã dữ liệu bit.", file=sys.stderr)
            return False

    try:
        target_dtype = np.dtype(img_dtype_str)
    except TypeError:
        print(f"Cảnh báo: Không thể nhận dạng dtype '{img_dtype_str}' từ metadata, dùng np.uint8.", file=sys.stderr)
        target_dtype = np.uint8
    
    if len(decoded_data_list) != expected_elements:
         print(f"Lỗi: Số lượng pixel giải mã ({len(decoded_data_list)}) không khớp kích thước ảnh gốc ({expected_elements}). File có thể bị lỗi hoặc metadata sai.", file=sys.stderr)
         return False

    try:
        if expected_elements == 0:
            reconstructed_array = np.array([], dtype=target_dtype).reshape(original_shape)
        else:

            try:
                processed_data = [target_dtype.type(s) for s in decoded_data_list]
            except (ValueError, TypeError) as e:
                 print(f"Lỗi: Không thể chuyển đổi ký hiệu giải mã sang kiểu dữ liệu {target_dtype}. Ký hiệu ví dụ: {decoded_data_list[0] if decoded_data_list else 'N/A'}. Lỗi: {e}", file=sys.stderr)
                 return False
            
            decoded_array = np.array(processed_data, dtype=target_dtype)
            reconstructed_array = decoded_array.reshape(original_shape)

    except ValueError as e:
        print(f"Lỗi khi tái tạo ảnh từ dữ liệu giải mã (reshape): {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Lỗi không xác định khi tái tạo mảng ảnh: {e}", file=sys.stderr)
        return False
        
    try:
        decoded_image = None
        if image_mode == '1':
            unique_values = np.unique(reconstructed_array)
            if not (len(unique_values) <= 2 and np.all(np.isin(unique_values, [0, 1]))):
                print(f"Cảnh báo: Ảnh mode '1' chứa giá trị không phải 0/1: {unique_values}. Chuyển sang 'L' rồi '1'.", file=sys.stderr)
                temp_img = Image.fromarray(reconstructed_array.astype(np.uint8), mode='L')
                decoded_image = temp_img.convert('1', dither=Image.NONE)
            else:
                array_for_pil_1bit = (1 - reconstructed_array).astype(np.uint8)
                decoded_image = Image.fromarray(array_for_pil_1bit, mode='1')

        elif image_mode == 'P':
            decoded_image = Image.fromarray(reconstructed_array, mode='P')
            if palette_data:
                decoded_image.putpalette(palette_data)
            else:
                print("Cảnh báo: Ảnh mode 'P' được giải mã mà không có palette. Màu sắc có thể không đúng.", file=sys.stderr)
        else:
             decoded_image = Image.fromarray(reconstructed_array, mode=image_mode)

        output_ext = os.path.splitext(output_path)[1].lower()
        output_format_pil = Image.registered_extensions().get(output_ext)

        if output_format_pil:
             if output_ext in ['.jpg', '.jpeg'] and image_mode != 'RGB':
                 if decoded_image.mode not in ['RGB', 'L', 'CMYK']:
                     print(f"Cảnh báo: Ảnh mode {decoded_image.mode} không thể lưu trực tiếp sang JPG. Thử convert sang RGB.", file=sys.stderr)
                     decoded_image = decoded_image.convert('RGB')
                 elif decoded_image.mode == 'L' or decoded_image.mode == '1':
                     pass
                 
             if output_ext in ['.jpg', '.jpeg']:
                 print(f"Cảnh báo: Lưu ảnh giải mã dưới dạng {output_ext} (lossy). Để so sánh chính xác, hãy lưu dưới dạng PNG hoặc BMP.", file=sys.stderr)
                 decoded_image.save(output_path, format=output_format_pil, quality=95)
             else:
                 decoded_image.save(output_path, format=output_format_pil)
        else:
             # Mặc định PNG nếu không nhận diện được
             print(f"Không nhận dạng được định dạng từ '{output_ext}', mặc định lưu thành PNG.")
             default_output_path = os.path.splitext(output_path)[0] + ".png"
             decoded_image.save(default_output_path, format='PNG')
             output_path = default_output_path

        print(f"Đã lưu ảnh giải mã: {output_path}")
        print(f"--- Giải mã hoàn tất ---")
        return output_path

    except ValueError as e:
         print(f"Lỗi khi tạo/lưu đối tượng Image: {e}. Mode: {image_mode}, Shape: {reconstructed_array.shape if 'reconstructed_array' in locals() else 'N/A'}", file=sys.stderr)
         return False
    except Exception as e:
        print(f"Lỗi khi lưu ảnh giải mã: {e}", file=sys.stderr)
        if os.path.exists(output_path):
            try: os.remove(output_path)
            except OSError: pass
        return False


def compare_images(image1_path, image2_path):
    print(f"--- Bắt đầu so sánh ---")
    print(f"Ảnh 1: {image1_path}")
    print(f"Ảnh 2: {image2_path}")
    try:
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)

        if img1.mode != img2.mode:
            print(f"KHÁC BIỆT: Chế độ màu (mode) khác nhau: {img1.mode} vs {img2.mode}")
            print(f"--- So sánh thất bại (khác mode) ---")
            return False


        arr1 = np.array(img1)
        arr2 = np.array(img2)

        if arr1.shape != arr2.shape:
            print(f"KHÁC BIỆT: Kích thước ảnh khác nhau:")
            print(f" - {os.path.basename(image1_path)}: {arr1.shape}")
            print(f" - {os.path.basename(image2_path)}: {arr2.shape}")
            print(f"--- So sánh thất bại (khác shape) ---")
            return False

        if np.array_equal(arr1, arr2):
            print(f"GIỐNG HỆT NHAU: Ảnh gốc và ảnh giải mã khớp hoàn toàn.")
            print(f"--- So sánh thành công ---")
            return True
        else:
            diff = np.abs(arr1.astype(np.int64) - arr2.astype(np.int64)) 
            
            if diff.ndim == 3: # Ảnh màu
                num_diff_pixels = np.count_nonzero(np.sum(diff, axis=2) > 0)
            else: # Ảnh grayscale hoặc 1-bit
                num_diff_pixels = np.count_nonzero(diff > 0)
            
            total_pixels = np.prod(arr1.shape[:2])
            max_diff_val = np.max(diff)
            avg_diff_val = np.mean(diff) if total_pixels > 0 else 0

            print(f"KHÁC BIỆT: Ảnh gốc và ảnh giải mã CÓ sự khác biệt.")
            print(f" - Số pixel khác nhau: {num_diff_pixels} / {total_pixels}")
            print(f" - Mức khác biệt tối đa trên một kênh màu/giá trị: {max_diff_val}")
            print(f" - Mức khác biệt trung bình (trên tất cả các giá trị): {avg_diff_val:.4f}")

            print(f"--- So sánh hoàn tất (có khác biệt) ---")
            return False

    except FileNotFoundError as e:
        print(f"Lỗi: Không tìm thấy file ảnh để so sánh: {e.filename}", file=sys.stderr)
        print(f"--- So sánh thất bại ---")
        return None 
    except Exception as e:
        print(f"Lỗi khi so sánh ảnh: {e}", file=sys.stderr)
        print(f"--- So sánh thất bại ---")
        return None