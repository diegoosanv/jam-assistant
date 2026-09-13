import platform
import psutil
import subprocess
import shutil

class HardwareDetector:
    def __init__(self):
        self.os_name = platform.system()
        self.arch = platform.machine()
    
    def get_ram_info(self):
        ram = psutil.virtual_memory()
        total_ram_gb = ram.total / (1024 ** 3)
        available_ram_gb = ram.available / (1024 ** 3)
        return {"total_gb": round(total_ram_gb, 2), "available_gb": round(available_ram_gb, 2)}
    
    def get_cpu_info(self):
        return {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "architecture": self.arch
        }
    
    def detect_gpu(self):
        gpu_info = {"type": "CPU Only", "vram_gb": 0, "details": "Sin GPU detectada o faltan drivers"}
        
        # Check Apple Silicon (Metal)
        if self.os_name == "Darwin" and self.arch == "arm64":
            gpu_info = {"type": "Apple Silicon (Metal)", "vram_gb": "Compartida con RAM", "details": "Memoria Unificada"}
            return gpu_info
            
        # Check NVIDIA (CUDA)
        if shutil.which("nvidia-smi"):
            try:
                # Obtener VRAM total en MB
                result = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=memory.total,gpu_name", "--format=csv,noheader,nounits"], 
                    text=True
                )
                if result:
                    lines = result.strip().split('\n')
                    total_vram_mb = 0
                    names = []
                    for line in lines:
                        parts = line.split(',')
                        total_vram_mb += int(parts[0].strip())
                        names.append(parts[1].strip())
                    
                    gpu_info = {
                        "type": "NVIDIA (CUDA)",
                        "vram_gb": round(total_vram_mb / 1024, 2),
                        "details": " | ".join(names)
                    }
                    return gpu_info
            except Exception:
                pass
                
        # Check AMD (ROCm)
        if shutil.which("rocm-smi"):
            try:
                gpu_info = {"type": "AMD (ROCm)", "vram_gb": "Desconocida", "details": "GPU AMD detectada"}
                return gpu_info
            except Exception:
                pass
                
        return gpu_info

    def get_full_report(self):
        return {
            "os": self.os_name,
            "cpu": self.get_cpu_info(),
            "ram": self.get_ram_info(),
            "gpu": self.detect_gpu()
        }
