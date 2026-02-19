import torch
print(f"Versi PyTorch: {torch.__version__}")
print(f"Apakah GPU Terdeteksi? {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Nama GPU: {torch.cuda.get_device_name(0)}")
    print(f"Total VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
else:
    print("GPU TIDAK TERDETEKSI! Cek instalasi CUDA.")