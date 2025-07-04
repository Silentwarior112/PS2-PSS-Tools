import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import threading
import time

def show_progress():
    progress_win = tk.Toplevel()
    progress_win.title("Working...")
    progress_win.geometry("300x100")
    progress_win.resizable(False, False)
    tk.Label(progress_win, text="Unweaving and encoding...").pack(pady=10)
    bar = ttk.Progressbar(progress_win, mode="indeterminate")
    bar.pack(fill="x", padx=20, pady=10)
    bar.start(10)
    progress_win.grab_set()
    progress_win.update()
    progress_win.mainloop()

def unweave_fields(input_path, temp_path, fps_in, target_fps):
    cap = cv2.VideoCapture(input_path)
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    if f"{actual_fps:.6f}" != f"{fps_in:.6f}":
        messagebox.showwarning("FPS Mismatch", f"Input reports {actual_fps:.6f} fps, but expected {fps_in:.6f}")

    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    # Get original dimensions
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    field_height = height // 2  # Half the height for each field

    # Output dimensions (we want full frame size)
    output_width = 640
    output_height = 448
    out = cv2.VideoWriter(temp_path, fourcc, target_fps, (output_width, output_height))
    frame_count = 0

    while True:
        ret1, frame1 = cap.read()
        ret2, frame2 = cap.read()
        if not ret1 or not ret2:
            break

        # Extract fields (no resizing yet!)
        top_field = frame1[0::2, :, :]   # Even lines from Frame N
        bot_field = frame2[1::2, :, :]   # Odd lines from Frame N+1

        # Stack them vertically
        stacked = np.vstack((top_field, bot_field))

        # Resize stacked frame to 640x448
        resized = cv2.resize(stacked, (output_width, output_height), interpolation=cv2.INTER_LINEAR)

        out.write(resized)
        frame_count += 1

    cap.release()
    out.release()
    return frame_count
    
def update_target_fps(*args):
    try:
        fps = float(fps_in_var.get())
        target_fps_var.set(f"{fps / 2:.6f}")
    except ValueError:
        target_fps_var.set("Invalid")

def encode_with_ffmpeg(temp_path, output_path, target_fps):
    bitrate = "9000k"
    bufsize = "1835k"
    gop = "12"
    bf = "2"
    pix_fmt = "yuv420p"

    cmd = [
        "ffmpeg", "-y", "-i", temp_path,
        "-c:v", "mpeg2video",
        "-b:v", bitrate,
        "-minrate", bitrate,
        "-maxrate", bitrate,
        "-bufsize", bufsize,
        "-r", f"{target_fps:.6f}",
        "-g", gop,
        "-bf", bf,
        "-pix_fmt", pix_fmt,
        "-s", "640x448",
        "-f", "mpeg2video",
        output_path
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        messagebox.showerror("FFmpeg Error", "Failed to encode with FFmpeg.")

def browse_input():
    path = filedialog.askopenfilename(
    title="Select interlaced Video",
    filetypes=[("Video files", "*.mpg;*.m2v;*.mp4;*.avi")])
    if path:
        input_var.set(path)

def browse_output():
    path = filedialog.asksaveasfilename(
        defaultextension=".m2v",
        title="Save field-stacked progressive Video",
        filetypes=[
        ("MPEG-2 Video", "*.m2v"),
        ("MP4 Video", "*.mp4"),
        ("AVI Video", "*.avi")
    ])
    if path:
        output_var.set(path)

def start_unweaving():
    def task():
        try:
            input_path = input_var.get()
            output_path = output_var.get()
            fps_in = float(fps_in_var.get())
            target_fps = float(target_fps_var.get())
            print(f"[Unweaving Started] Input: {input_path} | Output: {output_path} | Input FPS: {fps_in:.6f} → Target FPS: {target_fps:.6f}")
            print(f"Unweaving fields...")
            if not input_path or not output_path:
                messagebox.showerror("Missing Files", "Please select both input and output files.")
                return

            output_dir = os.path.dirname(output_path)
            temp_path = os.path.join(output_dir, "temp_output.avi")

            frame_count = unweave_fields(input_path, temp_path, fps_in, target_fps)
            print(f"Fields unweaved successfully. Re-rendering...")

            if frame_count == 0:
                return  # Already showed error message

            encode_with_ffmpeg(temp_path, output_path, target_fps)

            try:
                os.remove(temp_path)
            except FileNotFoundError:
                pass

            messagebox.showinfo("Done", f"✅ {frame_count} frames written to {output_path} at {target_fps:.6f} fps.")
        finally:
            # Close the progress bar window from main thread
            root.after(0, lambda: progress_window.destroy())

    # Create and start the progress window thread
    
    progress_window = tk.Toplevel()
    progress_window.title("Working...")
    progress_window.geometry("300x100")
    progress_window.resizable(False, False)
    tk.Label(progress_window, text="Unweaving and encoding...").pack(pady=10)
    bar = ttk.Progressbar(progress_window, mode="indeterminate")
    bar.pack(fill="x", padx=20, pady=10)
    bar.start(10)
    progress_window.grab_set()

    # Run the processing in a separate thread
    threading.Thread(target=task, daemon=True).start()

# GUI Setup
root = tk.Tk()
root.title("MPEG-2 Field Unweaver")

input_var = tk.StringVar()
output_var = tk.StringVar()
fps_in_var = tk.StringVar(value="59.940060")
target_fps_var = tk.StringVar(value="29.970030")

tk.Label(root, text="Input Video:").grid(row=0, column=0, sticky="e")
tk.Entry(root, textvariable=input_var, width=50).grid(row=0, column=1)
tk.Button(root, text="Browse", command=browse_input).grid(row=0, column=2)

tk.Label(root, text="Output Video:").grid(row=1, column=0, sticky="e")
tk.Entry(root, textvariable=output_var, width=50).grid(row=1, column=1)
tk.Button(root, text="Browse", command=browse_output).grid(row=1, column=2)

tk.Label(root, text="Input FPS:").grid(row=2, column=0, sticky="e")

fps_input_frame = tk.Frame(root)
fps_input_frame.grid(row=2, column=1, sticky="w")

tk.Entry(fps_input_frame, textvariable=fps_in_var, width=12).pack(side="left")

tk.Button(fps_input_frame, text="NTSC", command=lambda: fps_in_var.set("59.940060")).pack(side="left", padx=(5, 0))
tk.Button(fps_input_frame, text="PAL", command=lambda: fps_in_var.set("50.000000")).pack(side="left", padx=(5, 0))

# Target FPS (read-only, auto-calculated)
tk.Label(root, text="Target FPS:").grid(row=3, column=0, sticky="e")
target_fps_entry = tk.Entry(root, textvariable=target_fps_var, width=20, state="readonly")
target_fps_entry.grid(row=3, column=1, sticky="w")

# Link input box to target_fps calculation
fps_in_var.trace_add("write", update_target_fps)
update_target_fps()

tk.Button(root, text="Start", command=start_unweaving, bg="lightgreen").grid(row=4, column=1, pady=10)

root.mainloop()
