import os
import tarfile
import lzma
import sys
import shutil

EXT = ".pyarc"


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
    bar = "█" * int(percent // 2) + "=" * (50 - int(percent // 2))
    sys.stdout.write(f"\r|{bar}| {percent:.1f}%")
    sys.stdout.flush()


def compress(source, output, remove_origin=False):
    if not output.endswith(EXT):
        output += EXT

    print("\n" + "=" * 50)
    print("Compression Level: 0 (Fast/Low) to 9 (Slow/High)")
    print("WARNING: Levels 7-9 require significant memory.")
    print("Low-spec devices may crash due to high RAM usage.")
    print("=" * 50)

    try:
        level_input = input("Select level (0-9, default 6): ").strip()
        level = int(float(level_input)) if level_input else 6
        if not (0 <= level <= 9):
            level = 6
    except ValueError:
        level = 6  # Default to level 6 if input is invalid

    f_count = (
        sum([len(files) for r, d, files in os.walk(source)])
        if os.path.isdir(source)
        else 1
    )
    d_count = (
        sum([len(d) for r, d, files in os.walk(source)]) if os.path.isdir(source) else 0
    )
    print(f"Target: {f_count} files, {d_count} folders")

    total_size = get_size(source)
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
        print(f"\nDone: {output} (Compressed: {ratio:.1f}%)")

        if remove_origin:
            if os.path.isdir(source):
                shutil.rmtree(source)
            else:
                os.remove(source)
            print(f"Original removed: {source}")

    except Exception as e:
        print(f"\nError: {e}")
        if os.path.exists(output):
            os.remove(output)


def decompress(archive, remove_origin=False):
    if not os.path.exists(archive):
        return
    print(f"Extracting: {archive}")
    try:
        with lzma.open(archive, "rb") as f_in:
            with tarfile.open(fileobj=f_in, mode="r") as tar:
                members = tar.getmembers()
                for i, member in enumerate(members):
                    tar.extract(member, filter="data")
                    show_progress(i + 1, len(members))
        print(f"\nExtraction Finished.")

        if remove_origin:
            os.remove(archive)
            print(f"Archive removed: {archive}")

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    args = sys.argv[1:]
    opts = [a.lower() for a in args if a.startswith("-")]
    paths = [a for a in args if not a.startswith("-")]

    if len(paths) < 1:
        print("Usage: python archiver.py [-c/-d] [-r] [source] [output_name]")
        sys.exit()

    src = paths[0]
    out = paths[1] if len(paths) > 1 else "archive"

    if "-c" in opts:
        compress(src, out, "-r" in opts)
    elif "-d" in opts:
        decompress(src, "-r" in opts)
    else:
        print("Invalid option. Use -c to compress or -d to decompress.")
