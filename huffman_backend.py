import heapq
import os
import pickle
from collections import Counter, defaultdict
from PIL import Image
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

    if len(priority_queue) == 1:
        node = heapq.heappop(priority_queue)
        merged = HuffmanNode(None, node.freq)
        merged.left = node
        return merged

    while len(priority_queue) > 1:
        left = heapq.heappop(priority_queue)
        right = heapq.heappop(priority_queue)

        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left = left
        merged.right = right

        heapq.heappush(priority_queue, merged)

    return priority_queue[0]


def generate_huffman_codes(node, prefix="", codebook=None):
    if codebook is None:
        codebook = {}

    if node is None:
        return codebook

    if node.symbol is not None: 
        if not prefix and node.left is None and node.right is None:
             codebook[node.symbol] = "0"
        elif prefix:
             codebook[node.symbol] = prefix
        elif len(codebook) == 0: 
             codebook[node.symbol] = "0"

    else:
        if node.left:
            generate_huffman_codes(node.left, prefix + "0", codebook)
        if node.right:
            generate_huffman_codes(node.right, prefix + "1", codebook)
    return codebook


def encode_data(data, codebook):

    if not codebook or len(data) == 0:
        return ""

    encoded_bits = "".join(codebook.get(symbol, "") for symbol in data)
    return encoded_bits

def decode_data(encoded_bits, huffman_tree):
    if not encoded_bits or huffman_tree is None:
        return []

    decoded_symbols = []
    current_node = huffman_tree

    if current_node.left is None and current_node.right is None:
         pass

    if current_node.symbol is None and current_node.left and current_node.left.symbol is not None and current_node.right is None:
        symbol = current_node.left.symbol
        num_symbols = len(encoded_bits) 
        return [symbol] * num_symbols
    if current_node.symbol is None and current_node.right and current_node.right.symbol is not None and current_node.left is None:
        symbol = current_node.right.symbol
        num_symbols = len(encoded_bits)
        return [symbol] * num_symbols


    for bit in encoded_bits:
        if bit == '0':
            if current_node.left:
                current_node = current_node.left
            else:
                 print("Decode Error: Invalid bit '0' encountered.", file=sys.stderr)
                 return None 
        elif bit == '1':
            if current_node.right:
                current_node = current_node.right
            else:
                 print("Decode Error: Invalid bit '1' encountered.", file=sys.stderr)
                 return None
        else:
             print(f"Decode Error: Invalid character '{bit}' in encoded bits.", file=sys.stderr)
             return None

        if current_node.symbol is not None:
            decoded_symbols.append(current_node.symbol)
            current_node = huffman_tree
        elif current_node.left is None and current_node.right is None:
             print("Decode Error: Reached unexpected leaf node.", file=sys.stderr)
             return None


    if current_node != huffman_tree and not (huffman_tree.left is None and huffman_tree.right is None):
         print("Decode Warning: Encoded bits finished mid-symbol.", file=sys.stderr)

    return decoded_symbols



def flatten_image_data(image):
    img_array = np.array(image)
    if img_array.ndim == 3:
         return img_array.flatten().astype(np.uint16) 
    else:
        return img_array.flatten().astype(np.uint8)

def pad_encoded_text(encoded_text):
    extra_padding = 8 - len(encoded_text) % 8
    if extra_padding == 8:
        extra_padding = 0
    padded_encoded_text = encoded_text + '0' * extra_padding
    padding_info = "{0:08b}".format(extra_padding)
    return padded_encoded_text, padding_info

def remove_padding(padded_encoded_text):
    if len(padded_encoded_text) < 8:
        print("Error removing padding: Data too short.", file=sys.stderr)
        return ""
    padding_info = padded_encoded_text[:8]
    try:
        extra_padding = int(padding_info, 2)
    except ValueError:
        print("Error removing padding: Invalid padding info.", file=sys.stderr)
        return ""

    encoded_text = padded_encoded_text[8:]
    if extra_padding > len(encoded_text) or extra_padding < 0:
         print(f"Error removing padding: Invalid padding amount {extra_padding} for length {len(encoded_text)}.", file=sys.stderr)
         return ""

    if extra_padding > 0:
        encoded_text = encoded_text[:-extra_padding]
    return encoded_text

def get_byte_array(padded_encoded_text):
    if len(padded_encoded_text) % 8 != 0:
        print("Error in get_byte_array: Input is not padded correctly.", file=sys.stderr)
        raise ValueError("Chuỗi bit cần được padding để chia hết cho 8.")
    b = bytearray()
    for i in range(0, len(padded_encoded_text), 8):
        byte = padded_encoded_text[i:i+8]
        try:
            b.append(int(byte, 2))
        except ValueError:
            print(f"Error in get_byte_array: Invalid byte sequence '{byte}'.", file=sys.stderr)
            raise
    return bytes(b)

def bits_to_string(byte_data):
    bit_string = "".join(f"{byte:08b}" for byte in byte_data)
    return bit_string


def encode_image(image_path, output_path):
    """Mã hóa ảnh và lưu vào file. Trả về True nếu thành công, False nếu thất bại."""
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

    try:
        original_size_bytes = os.path.getsize(image_path)
        print(f"Kích thước gốc: {original_size_bytes} bytes")
    except OSError as e:
        print(f"Lỗi khi lấy kích thước file gốc: {e}", file=sys.stderr)
        return False

    # 1. Lấy dữ liệu ảnh và làm phẳng
    try:
        img_data = flatten_image_data(image)
        original_shape = np.array(image).shape 
        image_mode = image.mode
        if len(img_data) == 0 and original_size_bytes > 0:
             print("Cảnh báo: Dữ liệu ảnh trống sau khi làm phẳng.", file=sys.stderr)

    except Exception as e:
        print(f"Lỗi khi xử lý dữ liệu ảnh: {e}", file=sys.stderr)
        return False

    if len(img_data) == 0:
        print("Ảnh không chứa dữ liệu pixel để mã hóa.")

        freq_table = {}
        huffman_tree = None
        encoded_bits = ""
    else:
        # 2. Xây dựng bảng tần suất
        freq_table = build_frequency_table(img_data)
        if not freq_table:
            print("Lỗi: Không thể tạo bảng tần suất.", file=sys.stderr)
            return False

        # 3. Xây dựng cây Huffman
        huffman_tree = build_huffman_tree(freq_table)
        if huffman_tree is None:
             print("Lỗi: Không thể xây dựng cây Huffman.", file=sys.stderr)
             return False


        # 4. Tạo bảng mã Huffman
        codebook = generate_huffman_codes(huffman_tree)
        if not codebook and len(freq_table) > 0 : 
            print("Lỗi: Không thể tạo bảng mã Huffman.", file=sys.stderr)
            return False


        # 5. Mã hóa dữ liệu
        encoded_bits = encode_data(img_data, codebook)


    # 6. Thêm padding
    padded_encoded_bits, padding_info = pad_encoded_text(encoded_bits)

    # 7. Chuyển thành byte array
    try:
        full_bit_string = padding_info + padded_encoded_bits
        output_byte_array = get_byte_array(full_bit_string)
    except ValueError as e:
        print(f"Lỗi khi chuyển đổi sang byte array: {e}", file=sys.stderr)
        return False


    # 8. Chuẩn bị dữ liệu metadata để lưu
    metadata = {
        'tree': huffman_tree,
        'shape': original_shape,
        'mode': image_mode
    }

    # 9. Lưu file mã hóa
    try:
        with open(output_path, 'wb') as f_out:
            pickle.dump(metadata, f_out, protocol=pickle.HIGHEST_PROTOCOL)
            f_out.write(output_byte_array)
        print(f"Đã lưu file mã hóa: {output_path}")
    except Exception as e:
        print(f"Lỗi khi lưu file mã hóa: {e}", file=sys.stderr)
        try:
            os.remove(output_path)
        except OSError:
            pass
        return False

    # 10. Tính toán tỉ suất nén
    try:
        compressed_size_bytes = os.path.getsize(output_path)
        if original_size_bytes > 0:
             compression_ratio = compressed_size_bytes / original_size_bytes
             print(f"Kích thước sau khi nén: {compressed_size_bytes} bytes")
             print(f"Tỉ suất nén (compressed/original): {compression_ratio:.4f}")
             print(f"Tỉ lệ tiết kiệm: {(1 - compression_ratio) * 100:.2f}%")
        else:
             print(f"Kích thước sau khi nén: {compressed_size_bytes} bytes")
             print("Không thể tính tỉ suất nén (kích thước gốc là 0).")

    except OSError as e:
        print(f"Lỗi khi lấy kích thước file nén: {e}", file=sys.stderr)

    print(f"--- Mã hóa hoàn tất ---")
    return True


def decode_image(encoded_path, output_path):
    """Giải mã file và lưu lại ảnh. Trả về True nếu thành công, False nếu thất bại."""
    print(f"--- Bắt đầu giải mã ---")
    try:
        with open(encoded_path, 'rb') as f_in:
            # 1. Đọc metadata
            metadata = pickle.load(f_in)
            # 2. Đọc dữ liệu mã hóa (phần còn lại của file)
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


    # 3. Chuyển byte data thành chuỗi bit (bao gồm padding info)
    padded_encoded_bits = bits_to_string(encoded_byte_data)

    # 4. Loại bỏ padding
    encoded_bits = remove_padding(padded_encoded_bits)
    if not encoded_bits and len(padded_encoded_bits) >= 8: 
         return False


    expected_elements = np.prod(original_shape) if original_shape else 0
    if not encoded_bits and expected_elements == 0:
        print("Dữ liệu mã hóa trống, tương ứng với ảnh gốc trống.")
        decoded_data_list = []
    elif huffman_tree is None and expected_elements > 0 :
         print("Lỗi: Cây Huffman là None nhưng dữ liệu gốc không trống.", file=sys.stderr)
         return False
    elif not encoded_bits and expected_elements > 0:
         print("Lỗi: Dữ liệu mã hóa trống nhưng ảnh gốc không trống.", file=sys.stderr)
         return False
    else:
        # 5. Giải mã dữ liệu
        decoded_data_list = decode_data(encoded_bits, huffman_tree)
        if decoded_data_list is None:
            print("Lỗi trong quá trình giải mã.", file=sys.stderr)
            return False

    # 6. Tái tạo lại mảng numpy với shape gốc
    try:
        dtype = np.uint8

        if len(decoded_data_list) != expected_elements:
             print(f"Lỗi: Số lượng pixel giải mã ({len(decoded_data_list)}) không khớp kích thước ảnh gốc ({expected_elements}). File có thể bị lỗi hoặc metadata sai.", file=sys.stderr)
             return False

        if expected_elements == 0:
            reconstructed_array = np.array([], dtype=dtype).reshape(original_shape)
        else:
            try:
                processed_data = [dtype(symbol) for symbol in decoded_data_list]
            except (ValueError, TypeError) as e:
                 print(f"Lỗi: Không thể chuyển đổi ký hiệu giải mã sang kiểu dữ liệu {dtype}. Ký hiệu ví dụ: {decoded_data_list[0] if decoded_data_list else 'N/A'}. Lỗi: {e}", file=sys.stderr)
                 return False

            decoded_array = np.array(processed_data, dtype=dtype)
            reconstructed_array = decoded_array.reshape(original_shape)

    except ValueError as e:
        print(f"Lỗi khi tái tạo ảnh từ dữ liệu giải mã: {e}", file=sys.stderr)
        print(f"Shape mong đợi: {original_shape}, Số phần tử giải mã: {len(decoded_data_list)}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Lỗi không xác định khi tái tạo ảnh: {e}", file=sys.stderr)
        return False

    # 7. Tạo và lưu ảnh
    try:

        if image_mode == 'P' and 'palette' in metadata:
             print("Cảnh báo: Chế độ Palette ('P') chưa được hỗ trợ đầy đủ, ảnh có thể hiển thị sai màu.", file=sys.stderr)
             decoded_image = Image.fromarray(reconstructed_array, mode='L') 
        elif image_mode == '1': 
              reconstructed_array_bw = (reconstructed_array > 0) * 255
              decoded_image = Image.fromarray(reconstructed_array_bw.astype(np.uint8), mode='L').convert('1')
        else:
             decoded_image = Image.fromarray(reconstructed_array, mode=image_mode)

        # Xác định định dạng file output dựa trên phần mở rộng
        output_ext = os.path.splitext(output_path)[1].lower()
        output_format = Image.registered_extensions().get(output_ext)

        if output_format:
             if output_ext in ['.jpg', '.jpeg']:
                 print(f"Cảnh báo: Lưu ảnh giải mã dưới dạng {output_ext} (lossy). Để so sánh chính xác, hãy lưu dưới dạng PNG hoặc BMP.", file=sys.stderr)
                 decoded_image.save(output_path, format=output_format, quality=95) # Example quality
             else:
                 decoded_image.save(output_path, format=output_format)
        else:
             print(f"Không nhận dạng được định dạng từ '{output_ext}', mặc định lưu thành PNG.")
             if output_ext != ".png":
                 output_path = os.path.splitext(output_path)[0] + ".png"
             decoded_image.save(output_path, format='PNG')

        print(f"Đã lưu ảnh giải mã: {output_path}")

        print(f"--- Giải mã hoàn tất ---")
        return output_path

    except ValueError as e:
         print(f"Lỗi khi tạo đối tượng Image từ array: {e}. Mode: {image_mode}, Shape: {reconstructed_array.shape}", file=sys.stderr)
         return False
    except Exception as e:
        print(f"Lỗi khi lưu ảnh giải mã: {e}", file=sys.stderr)
        try:
             if os.path.exists(output_path): os.remove(output_path)
        except OSError:
             pass
        return False


def compare_images(image1_path, image2_path):
    """So sánh hai ảnh xem có giống hệt nhau không. Trả về True nếu giống, False nếu khác hoặc lỗi."""
    print(f"--- Bắt đầu so sánh ---")
    print(f"Ảnh 1: {image1_path}")
    print(f"Ảnh 2: {image2_path}")
    try:
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)

        arr1 = np.array(img1)
        arr2 = np.array(img2)

        if arr1.shape != arr2.shape:
            print(f"KHÁC BIỆT: Kích thước ảnh khác nhau:")
            print(f" - {os.path.basename(image1_path)}: {arr1.shape}, Mode: {img1.mode}")
            print(f" - {os.path.basename(image2_path)}: {arr2.shape}, Mode: {img2.mode}")
            print(f"--- So sánh thất bại ---")
            return False

        if np.array_equal(arr1, arr2):
            print(f"GIỐNG HỆT NHAU: Ảnh gốc và ảnh giải mã khớp hoàn toàn.")
            print(f"--- So sánh thành công ---")
            return True
        else:
            diff = np.abs(arr1.astype(np.float64) - arr2.astype(np.float64)) 
            num_diff_pixels = np.count_nonzero(np.sum(diff, axis=2) > 0) if diff.ndim == 3 else np.count_nonzero(diff > 0)
            max_diff = np.max(diff)
            avg_diff = np.mean(diff)

            print(f"KHÁC BIỆT: Ảnh gốc và ảnh giải mã CÓ sự khác biệt.")
            print(f" - Số pixel khác nhau: {num_diff_pixels} / {np.prod(arr1.shape[:2])}")
            print(f" - Mức khác biệt tối đa trên một kênh màu/giá trị: {max_diff:.2f}")
            print(f" - Mức khác biệt trung bình: {avg_diff:.4f}")

            print(f"--- So sánh hoàn tất (có khác biệt) ---")
            return False

    except FileNotFoundError as e:
        print(f"Lỗi: Không tìm thấy file ảnh để so sánh: {e}", file=sys.stderr)
        print(f"--- So sánh thất bại ---")
        return None 
    except Exception as e:
        print(f"Lỗi khi so sánh ảnh: {e}", file=sys.stderr)
        print(f"--- So sánh thất bại ---")
        return None