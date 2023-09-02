import streamlit as st
import os
import heapq
import base64
from bitstring import BitArray

class BinaryTree:
    def __init__(self, value, frequ):
        self.value = value
        self.frequ = frequ
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.frequ < other.frequ

    def __eq__(self, other):
        return self.frequ == other.frequ

class Huffmancode:
    def __init__(self, path):
        self.path = path
        self.__heap = []
        self.__code = {}
        self.__reversecode = {}

    def __frequency_from_text(self, text):
        frequ_dict = {}
        for char in text:
            if char not in frequ_dict:
                frequ_dict[char] = 0
            frequ_dict[char] += 1
        return frequ_dict

    def __Build_heap(self, frequency_dict):
        for key in frequency_dict:
            frequency = frequency_dict[key]
            binary_tree_node = BinaryTree(key, frequency)
            heapq.heappush(self.__heap, binary_tree_node)

    def __Build_Binary_Tree(self):
        while len(self.__heap) > 1:
            binary_tree_node_1 = heapq.heappop(self.__heap)
            binary_tree_node_2 = heapq.heappop(self.__heap)
            sum_of_freq = binary_tree_node_1.frequ + binary_tree_node_2.frequ
            newnode = BinaryTree(None, sum_of_freq)
            newnode.left = binary_tree_node_1
            newnode.right = binary_tree_node_2
            heapq.heappush(self.__heap, newnode)

    def __Build_Tree_Code_Helper(self, root, curr_bits):
        if root is None:
            return
        if root.value is not None:
            self.__code[root.value] = curr_bits
            self.__reversecode[curr_bits] = root.value
            return
        self.__Build_Tree_Code_Helper(root.left, curr_bits + '0')
        self.__Build_Tree_Code_Helper(root.right, curr_bits + '1')

    def __Build_Tree_Code(self):
        root = heapq.heappop(self.__heap)
        self.__Build_Tree_Code_Helper(root, '')

    def __Build_Encoded_Text(self, text):
        encoded_text = ''
        for char in text:
            encoded_text += self.__code[char]
        return encoded_text

    def __Build_Padded_Text(self, encoded_text):
        padding_value = 8 - (len(encoded_text) % 8)
        if padding_value == 0:
            padding_value = 8  # Add a full byte of padding if no padding is needed
        for i in range(padding_value):
            encoded_text += '0'

        padded_info = "{0:08b}".format(padding_value)
        padded_encoded_text = padded_info + encoded_text
        return padded_encoded_text

    def __Remove_Padding(self, text):
        padding_info = text[:8]
        extra_padding = int(padding_info, 2)
        text = text[8:]
        padding_removed_text = text[:-extra_padding]
        return padding_removed_text


    def __Build_Byte_Array(self, padded_text):
        array = []
        for i in range(0, len(padded_text), 8):
            byte = padded_text[i:i + 8]
            array.append(int(byte, 2))
        return array

    def encode_text(self, text):
        frequency_dict = self.__frequency_from_text(text)
        self.__Build_heap(frequency_dict)
        self.__Build_Binary_Tree()
        self.__Build_Tree_Code()
        encoded_text = self.__Build_Encoded_Text(text)
        padded_text = self.__Build_Padded_Text(encoded_text)
        return padded_text

    def compression(self):
        # To access the file and extract text from that file.
        filename, file_extension = os.path.splitext(self.path)
        output_path = filename + '.bin'
        with open(self.path, 'r') as file, open(output_path, 'wb') as output:
            text = file.read()
            text = text.rstrip()

            # Encode the text using your new encode_text method
            encoded_text = self.encode_text(text)

            # We have to return that binary file as an output.
            bytes_array = self.__Build_Byte_Array(encoded_text)

            final_bytes = bytes(bytes_array)
            output.write(final_bytes)
        st.success("Compression Complete.")
        return output_path


    def __Decompress_Text(self, text):
        decoded_text = ''
        current_bits = ''
        for bit in text:
            current_bits += bit
            if current_bits in self.__reversecode:
                character = self.__reversecode[current_bits]
                decoded_text += character
                current_bits = ""
        return decoded_text

    def decode_text(self, encoded_text):
        actual_text = self.__Remove_Padding(encoded_text)
        decompressed_text = self.__Decompress_Text(actual_text)
        return decompressed_text

    def decompress(self, input_path):
        filename, _ = os.path.splitext(input_path)
        output_path = filename + '_decompressed' + '.txt'

        with open(input_path, 'rb') as file, open(output_path, 'w', encoding='utf-8') as output:
            compressed_data = file.read()

            # Decode the compressed data using base64
            compressed_bitstring = BitArray(bytes=compressed_data).bin

            actual_text = self.__Remove_Padding(compressed_bitstring)
            decompressed_text = self.__Decompress_Text(actual_text)
            output.write(decompressed_text)
            return output_path

st.title("Huffman Coding Compression and Decompression")

# Initial operation selection
operation = st.radio("Select Operation:", ("Compress", "Decompress"))

if operation == "Compress":
    # File Upload for Text Files
    uploaded_text_file = st.file_uploader("Choose a text file...", type=["txt"])

    if uploaded_text_file:
        # Specify the output path for the compressed binary file
        compressed_file_path = "compressed.bin"

        # Check if the compression was successful before offering the download button
        compression_successful = False

        # Compression for Text Files
        if st.button("Compress Text"):
            h = Huffmancode(uploaded_text_file.name)
            compressed_file_path = h.compression()
            compression_successful = True

        # Display a status message
        if compression_successful:
            st.success("Compression Complete.")
            # Open the compressed file in binary mode for download
            with open(compressed_file_path, "rb") as file:
                bin_data = file.read()
                # Create a download button to automatically download the compressed binary file
                st.download_button(
                    label="Download Compressed File (.bin)",
                    data=bin_data,  # Use binary data directly
                    key="compressed",
                    file_name="compressed.bin",
                    mime="application/octet-stream",
                )
        else:
            st.warning("Compression failed. Please try again.")
elif operation == "Decompress":
    # File Upload for Binary Files (Change type to ["bin"])
    uploaded_binary_file = st.file_uploader(
        "Choose a binary file...", type=["bin"]
    )

    if uploaded_binary_file:
        # Specify the output path for the decompressed text file
        decompressed_file_path = "decompressed.txt"

        # Decompression for Binary Files
        if st.button("Decompress Binary"):
            filename, file_extension = os.path.splitext(uploaded_binary_file.name)
            if file_extension != ".bin":
                pass  # Do nothing if the selected file is not a binary file (.bin)
            else:
                h = Huffmancode(uploaded_binary_file.name)
                output_path = h.decompress(uploaded_binary_file.name)
                with open(output_path, "rb") as file:
                    bin_data = file.read()
                    if bin_data:
                        # Create a download button to automatically download the decompressed binary file
                        st.download_button(
                            label="Download Decompressed File (.bin)",
                            data=bin_data,  # Use binary data directly
                            key="decompressed",
                            file_name="decompressed.bin",
                            mime="application/octet-stream",
                        )

# Display instructions
st.markdown("Instructions:")
st.markdown(
    "- Select an operation: 'Compress' or 'Decompress'."
)
st.markdown(
    "- Upload a text file for compression or a binary file for decompression."
)
st.markdown(
    "- Click the respective button to perform the selected operation."
)
