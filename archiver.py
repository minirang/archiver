import os
import tarfile
import lzma
import sys

EXT = ".pyarc"

def get_size(path):
    if os.path.isfile(path): return os.path.getsize(path)
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            total += os.path.getsize(os.path.join(dirpath, f))
    return total

def show_progress(current, total):
    if total <= 0: return
    percent = (current / total) * 100
    bar = "█" * int(percent // 2) + "-" * (50 - int(percent // 2))
    sys.stdout.write(f"\r|{bar}| {percent:.1f}%")
    sys.stdout.flush()

def compress(source, output):
    if not output.endswith(EXT): output += EXT
    
    # Pre-scan info
    f_count = sum([len(files) for r, d, files in os.walk(source)]) if os.path.isdir(source) else 1
    d_count = sum([len(d) for r, d, files in os.walk(source)]) if os.path.isdir(source) else 0
    print(f"Target: {f_count} files, {d_count} folders")
    
    total_size = get_size(source)
    current_read = 0
    
    print(f"Compressing: {source}")
    
    try:
        # preset 9 + EXTREME for max compression
        with lzma.open(output, "wb", preset=8 | lzma.PRESET_EXTREME) as f_out:
            with tarfile.open(fileobj=f_out, mode="w") as tar:
                def progress_filter(tarinfo):
                    nonlocal current_read
                    if tarinfo.isfile():
                        current_read += tarinfo.size
                        show_progress(min(current_read, total_size), total_size)
                    return tarinfo
                tar.add(source, arcname=os.path.basename(source), filter=progress_filter)
        print(f"\nDone: {output}")
        
    except PermissionError:
        print("\nError: Permission denied. Please run as administrator.")
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        if os.path.exists(output): os.remove(output) # Delete incomplete file
    except Exception as e:
        print(f"\nError: {e}")

def decompress(archive):
    if not os.path.exists(archive):
        print(f"Error: {archive} not found."); return
        
    print(f"Extracting: {archive}")
    try:
        with lzma.open(archive, "rb") as f_in:
            with tarfile.open(fileobj=f_in, mode="r") as tar:
                members = tar.getmembers()
                for i, member in enumerate(members):
                    tar.extract(member, filter='data')
                    show_progress(i + 1, len(members))
        print(f"\nExtraction Finished.")
    except KeyboardInterrupt:
        print("\nExtraction interrupted.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py [c/d] [source] [output_name(optional)]")
    else:
        cmd = sys.argv[1].lower()
        if cmd == 'c':
            compress(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "archive")
        elif cmd == 'd':
            decompress(sys.argv[2])
