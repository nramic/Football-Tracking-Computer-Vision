#!/usr/local/bin/python


''' squawkFly.py

The all-encompassing GUI and controller for user operation.

Requires no command line arguments, just boots the graphical interface and
proceeds to call the requisite scripts based on the file paths supplied through
that, and manage the underlying filesystem.

Built with Python's Tkinter and ttk framework.

'''

from Tkinter import *
import ttk
from tkFileDialog import askopenfilename
from tkFileDialog import askdirectory
import os
import shutil
import subprocess


# Set the status message
def setStatus(string):
    status.set(string)
    status_label.update()


# escape any spaces that might appear in the input paths
def handleSpaces(string):

    print string

    i = string.find(' ')
    if i != -1:
        new = string[:i] + '\\' + string[i:]

        i = new.find(' ')
        if new.find('\ ') != i - 1:
            new = handleSpaces(new)

        return new

    return string


'''
    All of the choose methods assign a path to a text variable to later
    be passed as command line arguments to the system scripts.
'''


def d_choose1():
    filename = askdirectory()
    calib1.set(filename)


def d_choose2():
    filename = askdirectory()
    clip1.set(filename)


def d_choose3():
    filename = askdirectory()
    calib2.set(filename)


def d_choose4():
    filename = askdirectory()
    clip2.set(filename)


def f_choose1():
    filename = askopenfilename()
    calib1.set(filename)


def f_choose2():
    filename = askopenfilename()
    clip1.set(filename)


def f_choose3():
    filename = askopenfilename()
    calib2.set(filename)


def f_choose4():
    filename = askopenfilename()
    clip2.set(filename)


# Update the list of existing clips when a session is selected
def changeClipOptions(event):
    session_value = session_name.get()
    lst = get_subdirectories('sessions\\' + session_value)
    clip_entry['values'] = lst


# return the list of subdirectories within a folder
def get_subdirectories(folder):
    return [sub for sub in os.listdir(folder)
            if os.path.isdir(os.path.join(folder, sub))]


# Delete the current clip folder and all of it's contents
def delete():
    clip = clip_name.get()
    session = session_name.get()
    if session is not None and session != '':
        p_session = "sessions\\" + session
        p_clip = p_session + '\\' + clip

        if os.path.exists(p_clip):
            print "Delete:", p_clip
            shutil.rmtree(p_clip)
        else:
            print "Session does not exist:", p_clip


# Submit the four file paths for analysis
def submit(*args):
    print "--Submit--"

    new_session = False
    new_clip = False
    videos = False
    session = session_name.get()
    clip = clip_name.get()
    cal1 = calib1.get()
    cal2 = calib2.get()
    vid1 = clip1.get()
    vid2 = clip2.get()
    view = viewer.get()

    # paths
    p_session = "sessions\\" + session
    p_clip = p_session + '\\' + clip

    if vid1 and vid2:
        videos = True

    # unless the session already exists, all four input fields necessary
    if not os.path.exists(p_session):
        new_session = True
        if not cal1 or not cal2 or not vid1 or not vid2:
            print "WARN: Invalid input. To create a session you must" + \
                "submit all four files with a valid clip name."
            return

    if not os.path.exists(p_clip):
        new_clip = True
        if not vid1 or not vid2:
            print "WARN: Invalid input. To create a new clip in an" + \
                "existing session you must submit both free kick videos."
            return

    if new_session:
        cal1 = handleSpaces(calib1.get())
        cal2 = handleSpaces(calib2.get())

    # technically, user could supply these for the visualisation of an old clip
    if videos:
        vid1 = handleSpaces(clip1.get())
        vid2 = handleSpaces(clip2.get())

    # paths
    p_session = "sessions\\" + session
    p_clip = p_session + '\\' + clip

    print "Session:", p_session
    print "Clip:", p_clip

    session = ' ' + p_session + '\\'
    clip = ' ' + p_clip + '\\'

    # Setup all of the various arguments to be passed to each step
    # of the processing pipeline
    args_cal1 = cal1 + session + 'camera1.txt ' + view
    args_cal2 = cal2 + session + 'camera2.txt ' + view

    args_posts1 = vid1 + session + 'postPts1.txt' + session + 'image1.png'
    args_posts2 = vid2 + session + 'postPts2.txt' + session + 'image2.png'

    args_match = vid1 + ' ' + vid2 + session + \
        'statics1.txt' + session + 'statics2.txt'

    args_detect1 = vid1 + clip + 'detections1.txt ' + view
    args_detect2 = vid2 + clip + 'detections2.txt ' + view

    args_kalman1 = clip + "detections1.txt" + clip + "trajectories1.txt"
    args_kalman2 = clip + "detections2.txt" + clip + "trajectories2.txt"

    args_traj1 = clip + "detections1.txt" + clip + \
        "trajectories1.txt" + clip + "trajectory1.txt " + view
    args_traj2 = clip + "detections2.txt" + clip + \
        "trajectories2.txt" + clip + "trajectory2.txt " + view

    args_interp1 = clip + 'trajectory1.txt 30' + \
        clip + 'trajectory1.txt ' + view
    args_interp2 = clip + 'trajectory2.txt 30' + \
        clip + 'trajectory2.txt ' + view

    args_reconstruct = session_name.get() + ' ' + clip_name.get() + ' ' + view

    args_topdown = clip + '3d_out.txt ' + clip + 'graphs\\top_down.pdf'
    args_sideon = clip + '3d_out.txt ' + clip + 'graphs\\side_on.pdf'

    args_trace1 = vid1 + ' ' + clip + \
        'trajectory1.txt ' + clip + 'graphs\\trace1.mov'
    args_trace2 = vid2 + ' ' + clip + \
        'trajectory2.txt ' + clip + 'graphs\\trace2.mov'

    args_beehive = p_session + ' ' + os.path.join(p_session, 'beehive.png')

    # New session: create the scene data
    if not os.path.exists(p_session):
        os.makedirs(p_session)

        setStatus('Calibrating...')
        os.system("python calibrate.py " + args_cal1)
        os.system("python calibrate.py " + args_cal2)

        setStatus('Matching goalposts...')
        os.system("python postPoints.py " + args_posts1)
        os.system("python postPoints.py " + args_posts2)

        setStatus('Matching scene points...')
        os.system("python manualMatch.py " + args_match)

    # New clip: create the clip and reconstruction data
    if not os.path.exists(p_clip):
        os.makedirs(p_clip)
        setStatus('Detecting...')
        os.system("python detect.py " + args_detect1)
        os.system("python detect.py " + args_detect2)

        setStatus('Generating trajectories...')
        os.system("python kalman.py" + args_kalman1)
        os.system("python kalman.py" + args_kalman2)

        setStatus('Selecting the best trajectory...')
        os.system("python trajectories.py -1" + args_traj1)
        os.system("python trajectories.py -1" + args_traj2)

        setStatus('Interpolating...')
        os.system("python interpolate.py" + args_interp1)
        os.system("python interpolate.py" + args_interp2)

        setStatus('Reconstructing...')
        os.system("python reconstruct.py " + args_reconstruct)

    # Clip never analysed before: Create the graphs directory
    if not os.path.isdir(p_clip + '\\graphs'):
        os.makedirs(p_clip + '\\graphs')

    # Everything's there: Visualise it
    if videos:
        setStatus('Generating and saving tracer videos...')
        os.system("python trace.py " + args_trace1)
        os.system("python trace.py " + args_trace2)
    setStatus('Generating and saving views...')
    os.system("python top_down.py " + args_topdown)
    os.system("python side_on.py " + args_sideon)
    os.system("python beehive.py " + args_beehive)
    os.system("python generate_x3d.py " + p_clip)
    setStatus("Done!")

    # finish by revealing the results in finder
    subprocess.call(["open", "-R", p_clip + '\\graphs'])

'''
----------------------------------------------------------
----------------Program begins to run HERE----------------
----------------------------------------------------------
'''

# create graphical components
root = Tk()
root.title("squawkFly")

# Get the session names
lst = os.listdir('sessions')

frame = ttk.Frame(root, padding="3 3 12 12")
frame.grid(column=0, row=0, sticky=(N, W, E, S))

calib1 = StringVar()
calib2 = StringVar()
clip1 = StringVar()
clip2 = StringVar()
session_name = StringVar()
clip_name = StringVar()

session_name.set('demo')
clip_name.set('demo_clip')
calib1.set('..\\res\\camera1_calibration.mkv')
clip1.set('..\\res\\camera1_freekick.mkv')
calib2.set('..\\res\\camera2_calibration\\')
clip2.set('..\\res\\camera2_freekick.mp4')

# SESSION NAME
session_entry = ttk.Combobox(frame, textvariable=session_name)
session_entry.grid(column=2, row=1, sticky=(W, E))
session_entry['values'] = lst
session_entry.bind('<<ComboboxSelected>>', changeClipOptions)

# CLIP NAME
clip_entry = ttk.Combobox(frame, textvariable=clip_name)
clip_entry.grid(column=2, row=2, sticky=(W, E))

# PATH ENRTRY BOXES
calib1_entry = ttk.Entry(frame, width=60, textvariable=calib1)
clip1_entry = ttk.Entry(frame, width=60, textvariable=clip1)

calib2_entry = ttk.Entry(frame, width=60, textvariable=calib2)
clip2_entry = ttk.Entry(frame, width=60, textvariable=clip2)

calib1_entry.grid(column=2, row=3, sticky=(W, E))
clip1_entry.grid(column=2, row=4, sticky=(W, E))

calib2_entry.grid(column=2, row=5, sticky=(W, E))
clip2_entry.grid(column=2, row=6, sticky=(W, E))

# FILE SELECTORS
f_choose1 = ttk.Button(frame, text="Video", command=f_choose1)
f_choose1.grid(column=3, row=3, sticky=(W, E))

f_choose2 = ttk.Button(frame, text="Video", command=f_choose2)
f_choose2.grid(column=3, row=4, sticky=(W, E))

f_choose3 = ttk.Button(frame, text="Video", command=f_choose3)
f_choose3.grid(column=3, row=5, sticky=(W, E))

f_choose4 = ttk.Button(frame, text="Video", command=f_choose4)
f_choose4.grid(column=3, row=6, sticky=(W, E))

# DIRECTORY SELECTORS
d_choose1 = ttk.Button(frame, text="Image sequence", command=d_choose1)
d_choose1.grid(column=4, row=3, sticky=(W, E))

d_choose2 = ttk.Button(frame, text="Image sequence", command=d_choose2)
d_choose2.grid(column=4, row=4, sticky=(W, E))

d_choose3 = ttk.Button(frame, text="Image sequence", command=d_choose3)
d_choose3.grid(column=4, row=5, sticky=(W, E))

d_choose4 = ttk.Button(frame, text="Image sequence", command=d_choose4)
d_choose4.grid(column=4, row=6, sticky=(W, E))

# ANALYSE BUTTON
button_sub = ttk.Button(frame, text="Analyse", command=submit)
button_sub.grid(column=2, row=7, sticky=(W, E))

# TOGGLE PROCESS VIEWING
viewer = StringVar()
button_view = ttk.Checkbutton(frame,
                              text="View process?",
                              variable=viewer,
                              onvalue='view',
                              offvalue='suppress')
button_view.grid(column=3, row=7, sticky=(W, E))
button_view.instate(['disabled'])
viewer.set('suppress')

# DELETE BUTTON
button_del = ttk.Button(frame, text="Delete current analysis", command=delete)
button_del.grid(column=3, row=8, sticky=(W, E))

# STATIC LABELS
ttk.Label(frame, text="Session Name").grid(column=1, row=1, sticky=E)
ttk.Label(frame, text="Clip Name").grid(column=1, row=2, sticky=E)
ttk.Label(frame, text="Calibration Video 1").grid(column=1, row=3, sticky=E)
ttk.Label(frame, text="FK Video 1").grid(column=1, row=4, sticky=E)
ttk.Label(frame, text="Calibration Video 2").grid(column=1, row=5, sticky=E)
ttk.Label(frame, text="FK Video 2").grid(column=1, row=6, sticky=E)

# STATUS LABEL
status = StringVar()
status_label = ttk.Label(frame, textvariable=status)
status_label.grid(column=2, row=8)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
frame.columnconfigure(2, weight=1)

for child in frame.winfo_children():
    child.grid_configure(padx=5, pady=5)

root.update()
root.resizable(0, 0)
root.minsize(root.winfo_width(), root.winfo_height())

calib1_entry.focus()
root.bind('<Return>', submit)
root.mainloop()
