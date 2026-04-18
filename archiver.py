import os
import tarfile
import lzma
import sys
import shutil
import threading
import time

EXT = ".pyarc"
CLR_P = "\033[95m"  # Purple
CLR_R = "\033[0m"  # Default color
CLR_R_RED = "\033[91m"  # Light Red

if sys.platform == "win32":
    os.system("")


def spinner_task(stop_event):
    spinners = ["|", "/", "-", "\\"]
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{CLR_P}{spinners[idx % 4]} Scanning target...{CLR_R}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 30 + "\r")


def get_size(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            total += os.path.getsize(os.path.join(dirpath, f))
    return total


def show_progress(current, total):
    if total <= 0:
        return
    percent = (current / total) * 100
    bar = f"{CLR_P}█{CLR_R}" * int(percent // 2) + "=" * (50 - int(percent // 2))
    sys.stdout.write(f"\r|{bar}| {percent:.1f}%")
    sys.stdout.flush()


def compress(source, output, remove_origin=False):
    if not os.path.exists(source):
        print(f"{CLR_R_RED}Error: File or folder '{source}' not found.{CLR_R}")
        return

    if not output.endswith(EXT):
        output += EXT

    print("\n" + "=" * 50)
    print("Compression Level: 0 (Fast/Low) to 9 (Slow/High)")
    print(f"{CLR_R_RED}WARNING:{CLR_R} Levels 7-9 require significant memory.")
    print("Low-spec devices may crash due to high RAM usage.")
    print("=" * 50)

    try:
        level_input = input("Select level (0-9, default 6): ").strip()
        level = int(float(level_input)) if level_input else 6
        if not (0 <= level <= 9):
            level = 6
    except ValueError:
        print(f"{CLR_R_RED}Invalid input. Using default level 6.{CLR_R}")
        level = 6  # Default to level 6 if input is invalid

    print(
        f"{CLR_R_RED}\nWARNING: Do not close this window until the process is complete.{CLR_R}"
    )
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner_task, args=(stop_event,))
    spinner_thread.start()
    try:
        f_count = (
            sum([len(files) for r, d, files in os.walk(source)])
            if os.path.isdir(source)
            else 1
        )
        d_count = (
            sum([len(d) for r, d, files in os.walk(source)])
            if os.path.isdir(source)
            else 0
        )
        total_size = get_size(source)

    finally:
        stop_event.set()
        spinner_thread.join()

    print(f"\nTarget: {f_count} files, {d_count} folders")
    current_read = 0

    print(f"Compressing: {source}")
    try:
        with lzma.open(output, "wb", preset=level | lzma.PRESET_EXTREME) as f_out:
            with tarfile.open(fileobj=f_out, mode="w") as tar:

                def progress_filter(tarinfo):
                    nonlocal current_read
                    if tarinfo.isfile():
                        current_read += tarinfo.size
                        show_progress(min(current_read, total_size), total_size)
                    return tarinfo

                tar.add(
                    source, arcname=os.path.basename(source), filter=progress_filter
                )

        comp_size = os.path.getsize(output)
        ratio = (1 - (comp_size / total_size)) * 100 if total_size > 0 else 0
        print(f"\n\nDone: {output} ({CLR_P}Compressed: {ratio:.1f}%{CLR_R})")
        print(f"Archive Path: {os.path.abspath(output)}")

        if remove_origin:
            if os.path.isdir(source):
                shutil.rmtree(source)
            else:
                os.remove(source)
            print(f"Original removed: {source}\n")

        print()

    except Exception as e:
        print(f"\nError: {e}")
        if os.path.exists(output):
            os.remove(output)


def decompress(archive, remove_origin=False):
    if not os.path.exists(archive):
        print(f"{CLR_R_RED}Error: File or folder '{archive}' not found.{CLR_R}")
        return

    print(
        f"{CLR_R_RED}\nWARNING: Do not close this window until the process is complete.{CLR_R}"
    )
    print(f"\nExtracting: {archive}")
    try:
        with lzma.open(archive, "rb") as f_in:
            with tarfile.open(fileobj=f_in, mode="r") as tar:
                members = tar.getmembers()

                for i, member in enumerate(members):
                    tar.extract(member, path=".", filter="data")
                    show_progress(i + 1, len(members))

        print(f"\n\nExtraction Finished.")
        print(f"Archive Path: {os.path.abspath(archive)}")
        print(f"Extracted to: {os.path.abspath(os.getcwd())}")

        if remove_origin:
            os.remove(archive)
            print(f"Archive removed: {archive}\n")

        print()

    except PermissionError:
        print(
            f"\n{CLR_R_RED}Error: Permission denied. If '{archive}' is a folder, you cannot decompress it.{CLR_R}"
        )

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        if os.path.exists(output):
            os.remove(output) # Delete incomplete file

    except (lzma.LZMAError, tarfile.ReadError):
        print(
            f"\n{CLR_R_RED}Error: '{archive}' is not a valid {EXT} format or is corrupted.{CLR_R}"
        )

    except Exception as e:
        print(f"\n{CLR_R_RED}Error: {e}{CLR_R}")


if __name__ == "__main__":
    args = sys.argv[1:]
    opts = [a.lower() for a in args if a.startswith("-")]
    paths = [a for a in args if not a.startswith("-")]

    if len(paths) < 1:
        print("Usage: python archiver.py [-c/-d] [-r] [source] [output_name]")
        sys.exit()

    src = paths[0]
    if len(paths) > 1:
        out = paths[1]

    else:
        out = os.path.basename(os.path.normpath(src))


    if "-c" in opts:
        compress(src, out, "-r" in opts)

    elif "-d" in opts:
        decompress(src, "-r" in opts)

    else:
        print("Invalid option. Use -c to compress or -d to decompress.")
